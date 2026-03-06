# Module 4, 5 vs Module 6 — Differences

Comparison between **4_Bedrock_RAG_KB** (OpenSearch-based RAG backend), **5_Bedrock_RAG_KB_App_Integration** (app that uses 4), and **6_Bedrock_RAG_KB_S3_Vectors** (S3 Vectors–based RAG with app included).

---

## At a Glance

| Aspect | Module 4 | Module 5 | Module 6 |
|--------|----------|----------|----------|
| **Vector store** | OpenSearch Serverless | (uses 4) | S3 Vectors |
| **Scope** | AWS backend only (no UI in repo) | App only (Streamlit + FastAPI, local) | Backend + React app (local or S3) |
| **Lambda** | In 4_* (`lambda.py`) | Uses 4’s Lambda via API Gateway | In 6_* (`lambda/lambda.py`) |
| **API Gateway** | REST API | Calls 4’s REST API | HTTP API |
| **Cost (demo scale)** | ~$700/mo minimum (OpenSearch) | (same as 4) | ~$0.11 for ~48 hours |

---

## AWS Services

| Service | Module 4 | Module 5 | Module 6 |
|---------|----------|----------|----------|
| S3 (docs) | ✅ `assets/` → bucket | (uses 4’s bucket) | ✅ Same corpus (e.g. from 4_* assets) |
| S3 (frontend) | ❌ | ❌ | ✅ Optional (React static site) |
| OpenSearch Serverless | ✅ | (uses 4) | ❌ |
| S3 Vectors | ❌ | ❌ | ✅ (vector bucket + index) |
| Bedrock Knowledge Base | ✅ (OpenSearch backend) | (uses 4) | ✅ (S3 Vectors backend) |
| Lambda | ✅ (in 4_*) | ❌ (calls 4’s API) | ✅ (in 6_*) |
| API Gateway | REST API | Client of 4’s API | HTTP API |
| IAM (in repo) | ❌ | ❌ | ✅ `iam/` (Lambda + KB roles) |

---

## App / UI

| Module | App |
|--------|-----|
| **4** | No app in the repo. You call the deployed API (e.g. from 5_* or your own client). |
| **5** | Streamlit frontend + FastAPI backend, both run locally. FastAPI proxies to 4’s API Gateway. |
| **6** | React (Vite + TypeScript) app included; run locally or deploy to S3 static website. Frontend calls 6’s API Gateway directly (no local backend). |

---

## When to Use Which

- **Module 4:** You want the OpenSearch Serverless RAG backend and will use it from another app (e.g. 5_* or custom).
- **Module 5:** You want a local UI for the 4_* stack (Streamlit + FastAPI) and are fine depending on 4_* and its cost.
- **Module 6:** You want a single, low-cost stack (S3 Vectors) with an app included and no dependency on 4_*.
