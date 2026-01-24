# Bedrock App Integration

Full-stack automobile damage assessment: a FastAPI backend and two React frontends (Damage Assessment UI and Admin Dashboard). Users submit an accident description and exactly 3 photos (wide-angle, straight-on, closeup) for an AI assessment, then use chat for follow-up questions.

## Prerequisites

- **Python 3.12+**, **Node.js 18+**, **uv** (`curl -LsSf https://astral.sh/uv/install.sh | sh` or `pip install uv`)
- **AWS account** with Bedrock access; model `us.anthropic.claude-sonnet-4-20250514-v1:0` enabled in the Bedrock console
- **AWS CLI** configured (`aws configure`) or credentials in `.env`

## Quick Start

### Setup

1. **Backend**
   ```bash
   cd backend
   uv sync && source .venv/bin/activate   # Windows: .venv\Scripts\activate
   cp .env.example .env
   ```
   Edit `.env`: `AWS_REGION`, and `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` if not using `aws configure`. `BEDROCK_MODEL_ID` defaults to the Claude model above.

2. **Damage Assessment Frontend**
   ```bash
   cd ../chat-frontend
   npm install && cp .env.example .env
   ```

3. **Admin Frontend**
   ```bash
   cd ../admin-frontend
   npm install && cp .env.example .env
   ```

### Running

Start the backend first, then the frontends.

| Component   | Command                                      | URL                         |
|------------|-----------------------------------------------|-----------------------------|
| Backend    | `cd backend && source .venv/bin/activate && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000` | http://localhost:8000       |
| Chat UI    | `cd chat-frontend && npm run dev`             | http://localhost:3000       |
| Admin      | `cd admin-frontend && npm run dev`            | http://localhost:3001       |

- Health: http://localhost:8000/health  
- API docs: http://localhost:8000/docs  

## Verification

1. `curl http://localhost:8000/health` → `{"status":"healthy"}`
2. Open http://localhost:3000 and http://localhost:3001 (no console errors).
3. In the chat UI: submit a description and 3 damage photos; confirm you receive an assessment.

## Architecture

```
3_Bedrock_App_Integration/
├── backend/                 # FastAPI, port 8000
│   ├── routers/             # chat, conversations, admin, config
│   ├── models.py, storage.py, utils.py, config.py
│   ├── model_limits.json
│   └── Postman/
├── chat-frontend/           # Damage Assessment UI, port 3000
│   └── src/components/, services/, types.ts
├── admin-frontend/          # Admin Dashboard, port 3001
│   └── src/components/, services/, types.ts, config.ts
└── assets/                  # Sample images and accident_description.txt
```

- **Backend**: Damage assessment (`POST /chat`), conversations CRUD, admin analytics. [backend/README.md](backend/README.md)
- **Chat frontend**: Initial form (description + 3 images) then follow-up chat; conversation list. [chat-frontend/README.md](chat-frontend/README.md)
- **Admin frontend**: Analytics, conversations, model usage, system info; auto-refresh. [admin-frontend/README.md](admin-frontend/README.md)

## Configuration

- **Backend**: `.env` — `AWS_REGION`, `BEDROCK_MODEL_ID`, `CORS_ORIGINS`, etc. See [backend/README.md](backend/README.md).
- **Frontends**: `VITE_API_URL` (default `http://localhost:8000`); admin also `VITE_POLLING_INTERVAL` (default 15000).

## Testing

- **Postman**: Import `backend/Postman/Bedrock_Chat_API.postman_collection.json` and the environment. See [backend/Postman/README.md](backend/Postman/README.md).
- **Manual – Chat UI**: Description + 3 photos (wide-angle, straight-on, closeup) via **Select 3 images**, then **Submit Assessment**; follow-ups via **Send**. Use the conversations control in the header to switch or start a new conversation.
- **Manual – Admin**: Tabs for Analytics, Conversations, Models, System Info; data refreshes every 15s.

## Troubleshooting

| Issue | What to check |
|-------|----------------|
| `ModuleNotFoundError` | Activate venv: `source .venv/bin/activate`; or run `.venv/bin/python -m uvicorn main:app --reload` |
| Connection refused | Backend on 8000; frontends on 3000/3001. `lsof -i :8000` etc. |
| CORS | Backend allows 3000/3001; change `CORS_ORIGINS` in `backend/config.py` if needed |
| Bedrock `AccessDeniedException` | Enable `us.anthropic.claude-sonnet-4-20250514-v1:0` in Bedrock console |
| Upload / 400 | Initial submission: exactly 3 images; ≤ 3.75 MB each; JPEG, PNG, GIF, WebP |

More: [backend/README.md](backend/README.md), [chat-frontend/README.md](chat-frontend/README.md), [admin-frontend/README.md](admin-frontend/README.md).

## License

Part of the AI on AWS project.
