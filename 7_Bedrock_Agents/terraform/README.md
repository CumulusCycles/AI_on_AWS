# Terraform — Reading Order

This folder deploys the Bedrock Agents infrastructure with **Terraform**. The same stack can alternatively be deployed with **TypeScript CDK** — see [../cdk/README.md](../cdk/README.md). Use one or the other per account/region, not both.

If you're new to this stack, read the `.tf` files in this order so dependencies and flow make sense.

---

### 1. **main.tf**

**What it does:** Terraform and provider configuration, data sources, and `locals`.

- Declares required Terraform version and providers (`aws`, `awscc`, `archive`, `null`).
- Configures the `aws` and `awscc` providers with the selected region.
- Uses `data` sources to get the current account ID and region.
- Defines **locals** used everywhere else:
  - `kb_doc_files` — map of KB document paths (from `4_Bedrock_RAG_KB/assets/*.md`).
  - `agent_instruction` — contents of `../assets/agent_instruction.md`.
  - `openapi_schema` — contents of `../action_groups/openapi_schema.json`.
  - Expiry dates for demo policies (optional context).

Start here so you know what inputs and shared values the rest of the config relies on.

---

### 2. **variables.tf**

**What it does:** Declares input variables and their defaults.

- `aws_region`, `prefix`, `foundation_model`, `embedding_model`, `embedding_dimensions`.

You don't need to read the whole file in depth; just know that `var.prefix`, `var.foundation_model`, etc. are defined here. Use **terraform.tfvars** (or **terraform.tfvars.example** as a template) to override them when needed.

---

### 3. **iam.tf**

**What it does:** IAM roles and policies for Lambda and the Bedrock Agent.

- **Lambda role** — assume policy, `AWSLambdaBasicExecutionRole`, and inline policies for DynamoDB (claims + policies tables) and for Bedrock to invoke the Lambda.
- **Agent role** — assume policy for `bedrock.amazonaws.com` and inline policy for S3 docs, S3 Vectors, and Bedrock model access.

Everything that runs under AWS (Lambda, Agent) gets its permissions from here.

---

### 4. **dynamodb.tf**

**What it does:** Two DynamoDB tables used by the claims action group.

- **Claims table** — stores submitted claims (`claim_id` as hash key).
- **Policies table** — stores policy records (`policy_id` as hash key).

Both use pay-per-request billing. The Lambda’s environment variables reference these table names.

---

### 5. **lambda.tf**

**What it does:** Packages and deploys the claims action group Lambda.

- Uses `archive_file` to zip `../action_groups/claims_lambda.py`.
- Creates the Lambda with the IAM role from `iam.tf` and env vars pointing at the DynamoDB tables from `dynamodb.tf`.
- Adds a resource-based policy so the Bedrock Agent can invoke this Lambda.

This is the code the agent calls when it runs “Submit claim” or “Look up policy” actions.

---

### 6. **knowledge_base.tf**

**What it does:** S3 docs bucket, S3 Vectors bucket and index, and Bedrock Knowledge Base.

- **S3 docs bucket** — holds the KB markdown files; uploads them from `local.kb_doc_files` (from `main.tf`).
- **S3 Vectors** — vector bucket and index (embedding dimensions and model come from variables).
- **Bedrock Knowledge Base** — uses the S3 Vectors index and the docs bucket as the data source; includes an IAM role for Bedrock to read S3 and call the embedding model.

The agent’s “knowledge” (RAG) comes from this KB.

---

### 7. **agent.tf**

**What it does:** Defines the Bedrock Agent and its live alias.

- Creates the agent with instruction (`local.agent_instruction`), foundation model, and idle session TTL.
- Attaches the Knowledge Base from `knowledge_base.tf`.
- Attaches the action group that calls the Lambda from `lambda.tf` and uses `local.openapi_schema`.
- Creates a “live” alias so the Streamlit app can call `invoke_agent` with a stable alias ID.

This file ties together the KB and the Lambda into a single agent.

---

### 8. **outputs.tf**

**What it does:** Values printed after `terraform apply`.

- Agent ID, agent alias ID, knowledge base ID, Lambda ARN, bucket names, DynamoDB table names.

Use these (especially `agent_id` and `agent_alias_id`) in the frontend `.env` when running the Streamlit app.

---

## Summary

| Order | File            | Purpose                                      |
|-------|-----------------|----------------------------------------------|
| 1     | main.tf         | Providers, data, locals                      |
| 2     | variables.tf    | Input variables                             |
| 3     | iam.tf          | Roles and policies for Lambda and Agent     |
| 4     | dynamodb.tf     | Claims and policies tables                  |
| 5     | lambda.tf       | Claims action group Lambda                  |
| 6     | knowledge_base.tf | S3 docs, S3 Vectors, Bedrock KB           |
| 7     | agent.tf        | Bedrock Agent + alias                       |
| 8     | outputs.tf      | Values to use in the app                    |

**Optional:** **terraform.tfvars.example** shows example variable values; copy to `terraform.tfvars` and adjust before running `terraform plan` / `apply`.
