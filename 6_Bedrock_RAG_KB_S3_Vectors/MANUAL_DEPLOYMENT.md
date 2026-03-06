# Manual Deployment (AWS Console)

Step-by-step instructions for deploying the AWS infrastructure through the console. If you prefer automated deployment, see the **CDK** option in the [README](./README.md).

Do these steps **in this order**:

---

## Step 1 — Create the Lambda execution role

1. IAM → **Roles** → **Create role**
2. **Trusted entity type:** AWS service → **Service or use case:** Lambda → **Next**
3. **Add permissions:** attach no policies → **Next**
4. **Role name:** `rag-kb-s3-vectors-lambda-role` → **Create role**
5. On the role → **Permissions** tab → **Add permissions** → **Create inline policy** → **JSON** tab
6. Delete the placeholder, paste the full contents of **`iam/lambda-inline-policy.json`** → **Next** → **Policy name:** `rag-kb-s3-vectors-lambda-bedrock` → **Create policy**

---

## Step 2 — S3 docs bucket

7. S3 → **Create bucket** (name it and note the name)
8. Upload the 11 documents from **`4_Bedrock_RAG_KB/assets/`** into that bucket

---

## Step 3 — Create the Knowledge Base role

9. IAM → **Roles** → **Create role**
10. **Trusted entity type:** Custom trust policy → delete placeholder, paste full contents of **`iam/kb-trust-policy.json`** → **Next**
11. **Add permissions:** attach no policies → **Next**
12. **Role name:** `rag-kb-s3-vectors-kb-role` → **Create role**
13. On the role → **Permissions** tab → **Add permissions** → **Create inline policy** → **JSON** tab
14. Delete the placeholder, paste the full contents of **`iam/kb-inline-policy.json`**, then **replace every `YOUR-DOCS-BUCKET-NAME`** with the bucket name from step 7 → **Next** → **Policy name:** `rag-kb-s3-vectors-kb-s3-bedrock` → **Create policy**

---

## Step 4 — Bedrock Knowledge Base

15. Bedrock → **Knowledge bases** → **Create knowledge base**
16. Choose **S3 Vectors** as storage (console will create the vector bucket/index); use **Titan Text Embeddings V2** for embeddings; attach the S3 docs bucket and the role **`rag-kb-s3-vectors-kb-role`**; sync the data source. Note the **Knowledge base ID**.

---

## Step 5 — Lambda function

17. Lambda → **Create function** (author from scratch). **Name** it (e.g. `rag-kb-chat`).
18. **Execution role:** choose **Use an existing role** → select **`rag-kb-s3-vectors-lambda-role`**. (If you don't see it, you did not complete step 1.)
19. **Configuration** → **Environment variables** → **Edit** → **Add**:
    - **Key:** `KNOWLEDGE_BASE_ID` → **Value:** the Knowledge base ID from step 16
    - **Key:** `FOUNDATION_MODEL_ARN` → **Value:** `arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-haiku-20240307-v1:0` (change `us-east-1` only if your Lambda is in another region)
20. **Code** → replace the default handler with the contents of **`lambda/lambda.py`** → **Deploy**

---

## Step 6 — Set the Knowledge Base generation model

21. Bedrock → **Knowledge bases** → open your KB → **Edit** → set **Generative AI model** to **Claude 3 Haiku** → **Save**

---

## Step 7 — API Gateway

22. API Gateway → **Create API** → **HTTP API** → add a route **POST /chat** integrated with your Lambda.
23. Enable CORS:
    - In the HTTP API console → **CORS** tab → **Configure CORS**
    - **Access-Control-Allow-Origin:** `*` (or your S3 bucket's static website URL if known)
    - **Access-Control-Allow-Methods:** check `POST` (and `OPTIONS` if not already selected)
    - **Access-Control-Allow-Headers:** check `Content-Type`
    - Click **Save**
    - Note the **Invoke URL** (you'll need it for the frontend `.env` file)

---

## Step 8 — Test the Lambda

24. In the Lambda console → **Test** tab → **Create new event** → paste this **exact** JSON → **Save** → **Test**:
    ```json
    {"body": "{\"query\": \"What is AI Agent Insure?\"}"}
    ```
25. You should get status 200 and a JSON body with `generated_response` and `s3_locations`. If you get 502, the Lambda is not using **`rag-kb-s3-vectors-lambda-role`** — go to Lambda → **Configuration** → **Permissions** → **Edit** → **Use an existing role** → **`rag-kb-s3-vectors-lambda-role`**.

---

## Step 9 — S3 static website (optional, for frontend)

26. S3 → create a bucket for the frontend; enable **Static website hosting**; upload the built frontend (see Part 2 and Part 3 in the [README](./README.md)).

---

## Manual Tear Down

In the AWS Console, delete in this order:

1. Bedrock Knowledge Base (and data source)
2. S3 vector index → S3 vector bucket
3. S3 docs bucket (empty first, then delete)
4. Lambda function
5. API Gateway HTTP API
6. S3 frontend bucket (empty first, then delete)
7. IAM roles
