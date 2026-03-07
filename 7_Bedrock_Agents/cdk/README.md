# 7_Bedrock_Agents — TypeScript CDK

This directory contains the **AWS CDK (TypeScript)** version of the Bedrock Agents stack, equivalent to the Terraform in [../terraform](../terraform). You can deploy with either; use one per account/region (see main [../README.md](../README.md)).

## Prerequisites

- **Node.js** 20.x or 22.x (LTS)
- **AWS CLI** configured with credentials and a default region
- **npm** (or yarn)

## One-time setup

1. **Install CDK dependencies**

   ```bash
   npm install
   ```

2. **Install dependencies for custom resource Lambdas** (required for synth/deploy)

   ```bash
   cd lambdas/kb-ingestion && npm install && cd ../..
   cd lambdas/seed-policies && npm install && cd ../..
   ```

3. **Bootstrap CDK in your account/region** (once per account/region)

   ```bash
   npx cdk bootstrap
   ```

## Deploy

```bash
npx cdk deploy
```

Accept the IAM changes when prompted. After deployment, note the stack outputs (Agent ID, Agent Alias ID, etc.) and set them in your frontend/backend `.env` as in `../env.example`.

## Useful commands

- `npm run build` — Compile TypeScript
- `npx cdk synth` — Synthesize CloudFormation template
- `npx cdk deploy` — Deploy the stack
- `npx cdk destroy` — Tear down the stack

## Stack contents

- **S3** — Docs bucket for Knowledge Base source files (from `4_Bedrock_RAG_KB/assets`)
- **S3 Vectors** — Vector bucket and index for KB embeddings
- **Bedrock Knowledge Base** — S3 Vectors–backed KB + S3 data source; a custom resource runs initial ingestion. You may need to **manually sync** the data source if the agent reports no KB results (see below).
- **DynamoDB** — Claims and Policies tables; custom resource seeds three demo policies
- **Lambda** — Python claims action group handler (same as Terraform)
- **IAM** — Roles for Lambda, Bedrock Agent, and Knowledge Base
- **Bedrock Agent** — Agent + “live” alias, with KB and action group (Lambda + OpenAPI schema)

## Manual KB sync

If the agent says it has no information from the knowledge base (e.g. “What is AI Agent Insure?” returns nothing), sync the data source manually. Use the stack outputs `KnowledgeBaseIdOutput` and `DataSourceIdOutput` (after a deploy that includes the data source output):

```bash
# Replace with your stack output values and region
KB_ID=<KnowledgeBaseIdOutput>
DS_ID=<DataSourceIdOutput>
REGION=us-east-1

aws bedrock-agent start-ingestion-job \
  --knowledge-base-id $KB_ID \
  --data-source-id $DS_ID \
  --region $REGION
```

Poll until complete (optional):

```bash
# Use the ingestionJobId from start-ingestion-job output
aws bedrock-agent get-ingestion-job \
  --knowledge-base-id $KB_ID \
  --data-source-id $DS_ID \
  --ingestion-job-id <JOB_ID> \
  --region $REGION \
  --query 'ingestionJob.status' --output text
```

When status is `COMPLETE`, ask the agent again.

## Configuration

Defaults match the Terraform variables (prefix `ai-agent-insure`, Claude 3 Haiku, Titan embeddings, 1024 dimensions). To change them, edit the constants at the top of `lib/bedrock-agents-stack.ts` or introduce CDK context/context file.
