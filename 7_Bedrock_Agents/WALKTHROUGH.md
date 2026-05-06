# Bedrock Agents Walkthrough

This walkthrough covers the three core layers of the demo: how the agent is defined, how the action group contract works, and how the frontend invokes the agent.

The demo is "Aria" — an AI claims and policy assistant for a fictional AI-native insurer called **AI Agent Insure**.

---

## 1. How the Agent Is Defined

The repo ships two deployment options — **CDK** (`cdk/lib/bedrock-agents-stack.ts`) and **Terraform** (`terraform/agent.tf`) — that produce identical infrastructure. Both read the same shared source files: `assets/agent_instruction.md` for the system prompt and `action_groups/openapi_schema.json` for the action group contract.

### System Instruction (`assets/agent_instruction.md`)

Both deployments load this file at deploy time and pass its content as the agent's `instruction` property. It establishes the agent's identity and behaviour:

- **Identity:** "Aria", AI claims and policy assistant for AI Agent Insure
- **Capabilities:** submit claims, check claim status, look up policies, answer product questions via the knowledge base
- **Rules:** collect all required fields before calling a tool; never fabricate policy or claim data; use the KB for general product questions; use action group tools for live data operations

Keeping the instruction in a standalone file means you can iterate on the prompt without touching any infrastructure code.

### CDK (`cdk/lib/bedrock-agents-stack.ts`)

```typescript
const agentInstruction = fs.readFileSync(
  path.join(__dirname, '../../assets/agent_instruction.md'), 'utf-8'
);
const openapiSchema = fs.readFileSync(
  path.join(__dirname, '../../action_groups/openapi_schema.json'), 'utf-8'
);

const agent = new bedrock.CfnAgent(this, 'Agent', {
  agentName:              `${PREFIX}-assistant`,
  foundationModel:        FOUNDATION_MODEL,
  instruction:            agentInstruction,
  agentResourceRoleArn:   agentRole.roleArn,
  idleSessionTtlInSeconds: IDLE_SESSION_TTL,
  autoPrepare:            true,
  skipResourceInUseCheckOnDelete: true,
  knowledgeBases: [{
    knowledgeBaseId:    kb.ref,
    description:        'AI Agent Insure product and coverage knowledge base',
    knowledgeBaseState: 'ENABLED',
  }],
  actionGroups: [{
    actionGroupName:    'ClaimsPolicyActions',
    actionGroupState:   'ENABLED',
    actionGroupExecutor: { lambda: claimsLambda.functionArn },
    apiSchema:          { payload: openapiSchema },
  }],
});

const agentAlias = new bedrock.CfnAgentAlias(this, 'AgentAlias', {
  agentId:        agent.ref,
  agentAliasName: 'live',
});
```

### Terraform (`terraform/agent.tf`)

```hcl
resource "awscc_bedrock_agent" "main" {
  agent_name              = "${var.prefix}-assistant"
  foundation_model        = var.foundation_model
  instruction             = local.agent_instruction     # from assets/agent_instruction.md
  agent_resource_role_arn = aws_iam_role.agent.arn
  idle_session_ttl_in_seconds      = 1800
  auto_prepare                     = true
  skip_resource_in_use_check_on_delete = true

  knowledge_bases = [{
    knowledge_base_id    = awscc_bedrock_knowledge_base.main.knowledge_base_id
    description          = "AI Agent Insure product documents..."
    knowledge_base_state = "ENABLED"
  }]

  action_groups = [{
    action_group_name     = "ClaimsPolicyActions"
    action_group_state    = "ENABLED"
    action_group_executor = { lambda = aws_lambda_function.claims.arn }
    api_schema            = { payload = local.openapi_schema }
  }]
}

resource "awscc_bedrock_agent_alias" "live" {
  agent_id         = awscc_bedrock_agent.main.agent_id
  agent_alias_name = "live"
}
```

`local.agent_instruction` and `local.openapi_schema` are populated in `main.tf` using Terraform's `file()` function, pointing at the shared source files.

Both tools read the instruction and schema from the same files using `fs.readFileSync()` / `file()` — the agent definition stays in sync regardless of which IaC tool you use.

### Key Properties (Common to Both)

| Property | Value | Purpose |
|---|---|---|
| `foundationModel` | `claude-3-haiku-20240307-v1:0` | Backing LLM |
| `instruction` | `assets/agent_instruction.md` | System prompt (Aria persona + rules) |
| `idleSessionTtlInSeconds` | `1800` | 30-minute conversation memory window |
| `autoPrepare` | `true` | Agent rebuilds itself after every deploy |
| `knowledgeBases` | S3 Vectors KB | Static product docs for general questions |
| `actionGroups` | `ClaimsPolicyActions` → Lambda | Live data operations (claims, policies) |

### Alias

The Bedrock `invoke_agent` API requires both an agent ID and an alias ID. The agent ID is stable and never changes, but the alias ID controls which version of the agent runs. By targeting the `live` alias rather than a specific version number, you can promote a new agent version by updating the alias pointer — without changing any client configuration.

---

## 2. How the Action Group Contract Works

The action group has two halves: the **OpenAPI schema** that Bedrock reads to understand what operations exist, and the **Lambda handler** that executes them.

### The OpenAPI Schema (`action_groups/openapi_schema.json`)

Bedrock reads this schema to determine which function to call and what parameters to extract from the conversation. It defines five operations:

| Operation | Method | Purpose |
|---|---|---|
| `POST /submitClaim` | POST | File a new claim under an active policy |
| `GET /getClaimStatus` | GET | Look up a claim by ID |
| `GET /lookupPolicy` | GET | Get full policy details |
| `GET /listPolicies` | GET | List all policies, optionally filter by holder |
| `GET /getCoverageSummary` | GET | Get a human-readable coverage summary |

Each operation has a natural-language `description` that the agent uses to decide which operation matches the user's intent. Bedrock does not pattern-match on keywords — the model reads the description and reasons about which operation to call, then extracts the required parameters from the conversation context before invoking the Lambda.

### The Lambda Handler (`action_groups/claims_lambda.py`)

The Lambda receives a structured event from Bedrock and must return a structured response envelope.

**Incoming event shape:**
```python
event['actionGroup']   # "ClaimsPolicyActions"
event['apiPath']       # e.g. "/submitClaim"
event['httpMethod']    # "POST" or "GET"
event['parameters']    # list of {name, type, value} — for GET-style params
event['requestBody']   # nested dict — for POST body params
```

**Parameter extraction** handles both formats, since GET and POST operations deliver parameters differently:
```python
def _parse_parameters(event: dict) -> dict:
    # GET-style: flat list of {name, value} dicts
    params = {p['name']: p['value'] for p in event.get('parameters') or []}
    # POST-style: nested under requestBody
    try:
        props = event["requestBody"]["content"]["application/json"]["properties"]
        params.update({p['name']: p['value'] for p in props})
    except (KeyError, TypeError):
        pass
    return params
```

**Dispatch** uses a simple action map keyed by function name (not path). Bedrock sends either `event['function']` directly, or `event['apiPath']` (e.g. `/listPolicies`) which the handler strips to get the bare name:
```python
_ACTION_MAP = {
    "submitClaim":       submit_claim,
    "getClaimStatus":    get_claim_status,
    "lookupPolicy":      lookup_policy,
    "listPolicies":      list_policies,
    "getCoverageSummary": get_coverage_summary,
}
```

**Required response envelope** — Bedrock is strict about this shape:
```python
{
  "messageVersion": "1.0",
  "response": {
    "actionGroup": action_group,
    "apiPath": event.get("apiPath", f"/{function_name}"),
    "httpMethod": event.get("httpMethod", "GET"),
    "httpStatusCode": 200,
    "responseBody": {
      "application/json": {
        "body": json.dumps(result)   # must be a JSON string, not an object
      }
    }
  },
  "sessionAttributes": event.get("sessionAttributes", {}),
  "promptSessionAttributes": event.get("promptSessionAttributes", {}),
}
```

**Backend data** lives in two DynamoDB tables (table names injected via environment variables):
- `CLAIMS_TABLE` — keyed on `claim_id` (generated as `CLM-{uuid_hex[:6].upper()}`)
- `POLICIES_TABLE` — keyed on `policy_id`, seeded with three demo policies (POL-001, POL-002, POL-003)

The `submit_claim` handler validates that the policy exists and is active before writing the claim item, returning an error response otherwise.

### Data Flow: Agent → Lambda → DynamoDB

```
User message
  → Bedrock Agent (reasons about intent)
    → Selects operation from OpenAPI schema
      → Extracts parameters from conversation
        → Invokes Lambda with structured event
          → Lambda reads/writes DynamoDB
            → Returns JSON result in response envelope
              → Agent incorporates result into its reply
```

---

## 3. How the Frontend Invokes the Agent

The frontend is a Streamlit app in **`frontend/app.py`**. It calls the Bedrock Agent Runtime API directly via `boto3` — there is no intermediate REST server.

### Client Setup

```python
AWS_REGION    = os.environ.get("AWS_REGION", "us-east-1")
AGENT_ID      = os.environ["AGENT_ID"]
AGENT_ALIAS_ID = os.environ["AGENT_ALIAS_ID"]

bedrock_agent_runtime = boto3.client("bedrock-agent-runtime", region_name=AWS_REGION)
```

`AGENT_ID` and `AGENT_ALIAS_ID` come from Terraform outputs (or CDK outputs). The app user must have `bedrock:InvokeAgent` IAM permission on the agent ARN.

### Session Management

Session state is initialized to `None` on page load. A UUID is generated lazily the first time a message is sent:
```python
# On page load
if "session_id" not in st.session_state:
    st.session_state.session_id = None

# On first message send
if not st.session_state.session_id:
    st.session_state.session_id = str(uuid.uuid4())
```

Bedrock uses this ID to maintain conversation memory across turns (up to the 30-minute idle TTL configured on the agent). The sidebar shows a "New conversation" button that resets it to `None`, starting a fresh session.

### Invoking the Agent

```python
response = bedrock_agent_runtime.invoke_agent(
    agentId=AGENT_ID,
    agentAliasId=AGENT_ALIAS_ID,
    sessionId=session_id,
    inputText=message,
    enableTrace=True,    # streams reasoning steps alongside the reply
)
```

The response is not a single JSON object — it is a streaming event sequence.

### Consuming the Event Stream

```python
for event in response["completion"]:
    if "trace" in event:
        # agent reasoning step — rationale, tool call, tool result, KB lookup
        yield ("trace", parse_trace(event))
    elif "chunk" in event:
        # incremental text of the final reply
        yield ("chunk", event["chunk"]["bytes"].decode("utf-8"))
```

**Trace events** are emitted as the agent reasons. The app parses four trace components from `event['trace']['trace']['orchestrationTrace']`:

| Trace component | What it shows |
|---|---|
| `rationale.text` | The model's reasoning before acting |
| `invocationInput.actionGroupInvocationInput` | Which function was called and with what parameters |
| `invocationInput.knowledgeBaseLookupInput` | The query sent to the KB |
| `observation.actionGroupInvocationOutput.text` | The raw JSON result returned from Lambda |

**Chunk events** carry the streamed text of the final answer, assembled incrementally as the model generates it.

### UI Layout

The app splits into two columns:
- **Left** — chat history with styled user/assistant bubbles
- **Right** — live agent trace panel (toggleable), updated in real time as events arrive

A sidebar provides example prompts to seed common demo flows:
- "What policies does AI Agent Insure offer?" — routes to KB
- "Look up policy POL-001" — calls `lookupPolicy` via action group
- "List all policies" — calls `listPolicies`
- "What's the coverage limit on POL-003?" — calls `getCoverageSummary` or `lookupPolicy`
- "I need to file a claim under POL-002 — our AI model crashed and caused $80,000 in losses" — calls `submitClaim`
- "Check the status of claim CLM-ABC123" — calls `getClaimStatus`
- "What does Agentic AI Liability Insurance cover?" — routes to KB

The trace panel makes the agent's decision-making visible: you can watch it retrieve from the KB, decide to call a tool, pass parameters to Lambda, and incorporate the result — all before composing the final reply.
