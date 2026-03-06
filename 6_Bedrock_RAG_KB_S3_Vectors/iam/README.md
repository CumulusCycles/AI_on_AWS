# IAM Roles Setup

**Follow the main [README Part 1](../README.md#part-1--deploy-the-aws-infrastructure) in order.** The steps there include these IAM steps in the right sequence (Lambda role first, then S3 bucket, then KB role, then KB, then Lambda, etc.). This file repeats the IAM details for reference.

This folder contains the JSON policy documents needed to create the two IAM roles. Copy and paste them directly into the AWS Console — no editing required except where noted.

---

## Role 1 — Lambda Execution Role

**Role name:** `rag-kb-s3-vectors-lambda-role`

This role is assumed by the Lambda function. It grants permission to write logs to CloudWatch and to call the Bedrock RAG APIs.

You do **not** paste `lambda-trust-policy.json` — the console sets the trust policy automatically when you choose **Lambda** as the service. The file is in the repo for reference (e.g. CLI or Terraform).

### Step 1a — Create the role

1. Open the [IAM Console](https://console.aws.amazon.com/iam/) → **Roles** → **Create role**
2. **Trusted entity type:** AWS service
3. **Service or use case:** Lambda (choose the Lambda use case if the console shows one)
4. Click **Next**
5. On **Add permissions:** do not attach any policies. Click **Next** (you will add an inline policy in Step 1b).
6. **Role name:** `rag-kb-s3-vectors-lambda-role`
7. Click **Create role**

### Step 1b — Add the inline policy

1. On the role's summary page, go to the **Permissions** tab
2. Click **Add permissions** → **Create inline policy**
3. Switch to the **JSON** tab
4. Delete the placeholder text and paste the contents of **`lambda-inline-policy.json`**
5. Click **Next**
6. **Policy name:** `rag-kb-s3-vectors-lambda-bedrock`
7. Click **Create policy**

---

## Role 2 — Knowledge Base Role

**Role name:** `rag-kb-s3-vectors-kb-role`

This role is assumed by the Bedrock Knowledge Base. It grants permission to read your S3 docs bucket and to call the Titan embeddings model when syncing documents.

### Step 2a — Create the role

1. In the IAM Console → **Roles** → **Create role**
2. **Trusted entity type:** Custom trust policy
3. Delete the placeholder and paste the full contents of **`kb-trust-policy.json`**
4. Click **Next**
5. On **Add permissions:** do not attach any policies. Click **Next**
6. **Role name:** `rag-kb-s3-vectors-kb-role`
7. Click **Create role**

### Step 2b — Add the inline policy

1. On the role's summary page, go to the **Permissions** tab
2. Click **Add permissions** → **Create inline policy**
3. Switch to the **JSON** tab
4. Delete the placeholder text and paste the contents of **`kb-inline-policy.json`**
5. **Replace `YOUR-DOCS-BUCKET-NAME`** (appears twice) with the name of the S3 bucket where you uploaded the KB documents
6. Click **Next**
7. **Policy name:** `rag-kb-s3-vectors-kb-s3-bedrock`
8. Click **Create policy**

---

## Summary

| Role name | Trust policy | Inline policy | Used by |
|---|---|---|---|
| `rag-kb-s3-vectors-lambda-role` | (set automatically — Lambda use case) | `lambda-inline-policy.json` | Lambda function |
| `rag-kb-s3-vectors-kb-role` | `kb-trust-policy.json` | `kb-inline-policy.json` | Bedrock Knowledge Base |

Once both roles are created, continue with the rest of the setup in the [module README](../README.md) Part 1 (steps 5 onward).
