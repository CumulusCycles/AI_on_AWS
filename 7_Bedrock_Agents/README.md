# Bedrock Agents

A complete **Amazon Bedrock Agents** project: AWS infrastructure (Terraform or TypeScript CDK) and a Streamlit chat application that calls the Bedrock Agent directly via boto3.

---

## What is a Bedrock Agent?

A **Bedrock Agent** is a managed AI orchestrator that:

1. Receives a natural-language request from a user
2. **Reasons** about what steps are needed (using a foundation model)
3. **Calls action group functions** (Lambda) to take real actions — like submitting a claim or looking up a policy
4. **Queries a knowledge base** to retrieve relevant product documents
5. Synthesizes all results into a coherent final response

Unlike RAG (which only retrieves and generates), an agent can take **multi-step actions** and make **autonomous decisions** about which tools to use and in what order.

---

## Architecture

```
Streamlit UI  ── boto3 ──►  Bedrock Agent  ──►  Foundation Model (Claude 3 Haiku)
                                  │
                                  ├── Action Group (OpenAPI) ──► Lambda ──► DynamoDB
                                  │
                                  └── Knowledge Base ──► S3 Vectors ──► S3 (docs)
```

The action group Lambda implements five operations: submitClaim, getClaimStatus, lookupPolicy, listPolicies, getCoverageSummary (claims and policies tables). The KB uses an S3 Vectors index populated from the S3 docs bucket (11 product markdown files). Streamlit calls `bedrock-agent-runtime` directly — no intermediate server.

---

## Infrastructure: CDK or Terraform

You can deploy the same stack with either:

- **TypeScript CDK** — `cdk/`. See **[cdk/README.md](cdk/README.md)** for setup and deploy (see **Part 1** below).
- **Terraform** — `terraform/`. Outputs (agent ID, alias ID, etc.) are the same; use them in the frontend `.env` as described in Part 2.

---

## Project Structure

```
7_Bedrock_Agents/
├── cdk/                     # TypeScript CDK (alternative to Terraform)
│   ├── bin/                 # CDK app entry
│   ├── lib/                 # BedrockAgentsStack
│   ├── lambdas/             # Custom resource handlers (KB ingestion, DynamoDB seed)
│   └── README.md
├── terraform/
│   ├── main.tf              # Provider config, locals
│   ├── variables.tf         # Input variables
│   ├── iam.tf               # All three IAM roles and policies
│   ├── dynamodb.tf          # Claims + policies tables, demo policy seed items
│   ├── lambda.tf            # Lambda packaging, function, Bedrock invoke permission
│   ├── knowledge_base.tf    # S3 docs bucket, S3 vector bucket/index, Bedrock KB + sync
│   ├── agent.tf             # Bedrock Agent, action group, KB attachment, alias
│   ├── outputs.tf           # Agent ID, alias ID, KB ID, and more
│   ├── terraform.tfvars.example
│   └── .gitignore
├── action_groups/
│   ├── claims_lambda.py     # Lambda handler — reads/writes DynamoDB
│   └── openapi_schema.json  # OpenAPI 3.0 schema defining the action group API
├── assets/
│   └── agent_instruction.md # Agent system prompt (unique to this module)
│                            # KB corpus docs are shared from 4_Bedrock_RAG_KB/assets/
├── frontend/
│   ├── app.py               # Streamlit app — chat + live agent trace, calls Bedrock directly
│   ├── pyproject.toml
│   └── env.example
├── env.example
└── README.md
```

---

## Prerequisites

- **Python 3.12+** and **uv** ([install guide](https://github.com/astral-sh/uv)) — for the Streamlit frontend
- **AWS CLI** configured (`aws configure`)
- **Bedrock model access** enabled for:
  - `anthropic.claude-3-haiku-20240307-v1:0` (agent inference; same pattern as 6_*)
  - `amazon.titan-embed-text-v2:0` (KB embeddings)

For **infrastructure** you need one of:

- **CDK** — Node.js 20+ and npm (see [cdk/README.md](cdk/README.md))
- **Terraform** — Terraform >= 1.6 ([install guide](https://developer.hashicorp.com/terraform/install))

---

## Part 1 — Deploy the Infrastructure

Use **either** CDK **or** Terraform (not both for the same account/region).

### Option A — TypeScript CDK

See **[cdk/README.md](cdk/README.md)** for install, bootstrap, and deploy. After `cdk deploy`, use the stack outputs (AgentId, AgentAliasId, etc.) for the frontend `.env` (Part 2).

### Option B — Terraform

#### 1. Configure variables

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` if you need to change the region or prefix. Defaults work out of the box for `us-east-1`.

#### 2. Deploy

```bash
terraform init
terraform apply
```

Terraform creates all resources in dependency order:

| Step | Resources |
|---|---|
| IAM | 3 roles (Lambda, Agent, KB) with least-privilege policies |
| DynamoDB | Claims table, policies table, 3 seeded demo policies |
| Lambda | `claims_lambda.py` packaged and deployed with env vars |
| S3 | Docs bucket + 11 KB documents uploaded |
| S3 Vectors | Vector bucket + 1024-dim cosine index |
| Bedrock KB | Knowledge base backed by S3 Vectors; sync data source (manual if needed — see “Knowledge Base sync”) |
| Bedrock Agent | Agent + action group + KB attached + prepared + `live` alias |

Total time: ~3–5 minutes (dominated by KB document embedding).

#### 3. Get the outputs

```bash
terraform output
```

You'll need `agent_id` and `agent_alias_id` for the next part.

### Knowledge Base sync (if needed)

Deploy runs an initial KB ingestion job; if it doesn’t complete (e.g. timeout), the agent may say it has no information from the KB. **Manually sync the data source** using the stack’s KB ID and data source ID: see [cdk/README.md](cdk/README.md) for the `bedrock-agent start-ingestion-job` commands (CDK), or run the same after getting IDs from Terraform outputs / Bedrock console.

---

## Part 2 — Run the App

```bash
cd frontend
uv venv --python 3.12
source .venv/bin/activate
uv sync
cp env.example .env
```

Edit `.env` with the values from your infrastructure outputs (CDK stack outputs or Terraform `terraform output`):

```
AWS_REGION=us-east-1
AGENT_ID=<agent_id>
AGENT_ALIAS_ID=<agent_alias_id>
```

**If you get "Access denied when calling Bedrock":** The credentials used by the app (same as `aws` in that shell) must have `bedrock:InvokeAgent`. Check who you are with `aws sts get-caller-identity`. Then attach an IAM policy to that user/role with:

```json
{
  "Version": "2012-10-17",
  "Statement": [{ "Effect": "Allow", "Action": "bedrock:InvokeAgent", "Resource": "arn:aws:bedrock:us-east-1:YOUR_ACCOUNT_ID:agent/*" }]
}
```

Replace `YOUR_ACCOUNT_ID` with the Id from `get-caller-identity`.

Start the app (use the venv’s Python so boto3 is found):

```bash
python -m streamlit run app.py
```

Opens at `http://localhost:8501`.

---

## Using the App

1. Type a message or click an example prompt in the sidebar
2. The agent reasons, calls tools, and streams the response
3. Toggle **Show agent trace** in the sidebar to see the agent's reasoning steps live as they arrive — rationale, tool calls, tool results, and KB lookups

### What the agent can do

| Capability | Example prompt |
|---|---|
| Look up a policy | "What are the details of policy POL-001?" |
| List all policies | "Show me all active policies" |
| Get coverage summary | "What does POL-003 cover?" |
| Submit a claim | "File a claim under POL-002 — our model crashed, $80k loss" |
| Check claim status | "What's the status of claim CLM-ABC123?" |
| Answer product questions | "What is Agentic AI Liability Insurance?" |
| Multi-step reasoning | "Look up POL-001, then file a hallucination claim for $50k" |

### Demo policies

| Policy ID | Holder | Product | Coverage Limit |
|---|---|---|---|
| POL-001 | Acme AI Corp | Agentic AI Liability Insurance | $5,000,000 |
| POL-002 | NeuralOps Ltd | AI Infrastructure & Operations Protection | $2,000,000 |
| POL-003 | RoboFleet Systems | Autonomous Systems & Robotics Coverage | $10,000,000 |

---

## Agent Trace

The **agent trace** panel (right column) shows the agent's internal reasoning as it arrives:

- **Rationale** — the model's reasoning about what to do next
- **Tool calls** — which action group function is being called and with what parameters
- **Tool results** — what the Lambda returned
- **KB lookups** — knowledge base queries and retrieved context

This is the key learning concept of this module: unlike a simple RAG query, the agent actively decides which tools to use, in what order, and synthesizes the results into a coherent response.

---

## Cost (~48 hours)

| Service | Cost |
|---|---|
| S3 Vectors (vector storage + queries) | ~$0.01 |
| Bedrock inference (Claude 3 Haiku) | ~$0.05 |
| Lambda, DynamoDB, S3 | ~$0.00 (free tier) |
| **Total** | **~$0.06** |

---

## Tear Down

- **CDK:** `cd cdk && npx cdk destroy`
- **Terraform:** `cd terraform && terraform destroy`

Either command deletes all AWS resources (S3 buckets, DynamoDB tables, Lambda, KB, vector index, and agent) for that stack.
