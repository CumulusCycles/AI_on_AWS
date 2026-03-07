<table style="border: none; border-collapse: collapse;">
  <tr>
    <td style="border: none; padding: 0;">
      <img src="img/logo.png" alt="Logo" width="200">
    </td>
    <td style="border: none; padding: 0;">
      <h1>AI on AWS</h1>
      Repo for the AI on AWS <a href="https://www.youtube.com/playlist?list=PLRBkbp6t5gM2S0wHeDB8jHiwjYx3DhyYj">Playlist</a>.
    </td>
  </tr>
</table>

A progressive, hands-on guide to building AI applications on AWS — from purpose-built AI services through to fully agentic systems.

- [AI on AWS: Playlist](https://www.youtube.com/playlist?list=PLRBkbp6t5gM2S0wHeDB8jHiwjYx3DhyYj)

---

## Modules

| # | Folder | What it covers |
|---|---|---|
| 0 | [`0_Purpose_Built_AI_Services`](./0_Purpose_Built_AI_Services/) | Reference guides and Jupyter notebook examples for AWS purpose-built AI services: Transcribe, Polly, Translate, Comprehend, Rekognition, Textract, Lex |
| 1 | [`1_Purpose_Built_AI_Services_Demo_Apps`](./1_Purpose_Built_AI_Services_Demo_Apps/) | Full-stack demo apps (FastAPI + React/TypeScript) showcasing the purpose-built services in real-world scenarios |
| 2 | [`2_Amazon_Bedrock`](./2_Amazon_Bedrock/) | Intro to Amazon Bedrock — streaming chat app with FastAPI backend and Streamlit frontend |
| 3 | [`3_Bedrock_App_Integration`](./3_Bedrock_App_Integration/) | Multimodal damage assessment app (FastAPI + React/TypeScript) with an admin dashboard; demonstrates image + text input and follow-up chat |
| 4 | [`4_Bedrock_RAG_KB`](./4_Bedrock_RAG_KB/) | AWS infrastructure for a Bedrock RAG Knowledge Base backed by OpenSearch Serverless — Lambda handler and KB corpus documents |
| 5 | [`5_Bedrock_RAG_KB_App_Integration`](./5_Bedrock_RAG_KB_App_Integration/) | Full-stack RAG chat app (FastAPI + Streamlit) wrapping the module 4 Knowledge Base |
| 6 | [`6_Bedrock_RAG_KB_S3_Vectors`](./6_Bedrock_RAG_KB_S3_Vectors/) | Combined RAG project (modules 4+5) rebuilt with S3 Vectors instead of OpenSearch Serverless — React frontend on S3, API Gateway, Lambda, Bedrock KB. Demonstrates the cost-effective vector store alternative |
| 7 | [`7_Bedrock_Agents`](./7_Bedrock_Agents/) | Bedrock Agents: orchestrated AI (Claude) with action groups (Lambda + DynamoDB) and a Knowledge Base (S3 Vectors). Streamlit chat app; infra via Terraform or TypeScript CDK |
