# Backend — AWS Bedrock App Integration

FastAPI server for the automobile damage assessment app: `POST /chat` (initial: text + 3 images; follow-up: text, images optional), conversation CRUD, and admin endpoints.

## Features

- **Damage assessment**: System prompt for expert-style analysis; initial submission requires text + exactly 3 images (wide-angle, straight-on, closeup); follow-ups text-only (images optional).
- **Conversations**: Create, list, get, delete with user isolation.
- **Admin**: Analytics, timeline, conversations, models, system info, bulk delete.
- **Storage**: In-memory, thread-safe. Data lost on restart.

## Tech Stack

Python 3.12+, FastAPI, Pydantic, Boto3 (Bedrock Converse API), python-dotenv, python-multipart.

## Project Structure

```
backend/
├── main.py              # FastAPI app
├── config.py            # Constants, Bedrock client, CORS, system prompt
├── models.py            # Pydantic schemas
├── storage.py           # In-memory store and helpers
├── utils.py             # File handling, message formatting
├── model_limits.json    # Model-specific limits
├── .env.example
├── pyproject.toml, uv.lock
├── Postman/             # Collection and environment
└── routers/
    ├── config.py        # /health, /config
    ├── chat.py          # /chat
    ├── conversations.py # /conversations
    └── admin.py         # /admin/*
```

## Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv): `curl -LsSf https://astral.sh/uv/install.sh | sh` or `pip install uv`
- AWS account with Bedrock access; [AWS CLI](https://aws.amazon.com/cli/) recommended for credentials

## Installation

1. `cd backend && uv sync && source .venv/bin/activate` (Windows: `.venv\Scripts\activate`)
2. `cp .env.example .env` and set at least `AWS_REGION`. If not using `aws configure`, set `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`.

## Configuration

### Environment variables

| Variable | Purpose |
|----------|---------|
| `AWS_REGION` | AWS region (e.g. `us-east-1`) |
| `AWS_ACCESS_KEY_ID` | Optional if using `aws configure` |
| `AWS_SECRET_ACCESS_KEY` | Optional if using `aws configure` |
| `BEDROCK_MODEL_ID` | Default: `us.anthropic.claude-sonnet-4-20250514-v1:0` |
| `CORS_ORIGINS` | Comma-separated origins or `*` |
| `DEFAULT_TEMPERATURE` | Default: `0.2` |
| `DEFAULT_MAX_TOKENS` | Default: `1000` |

Model limits (temperature/max_tokens ranges) live in `model_limits.json`; `/config` exposes them.

## Running

- **Development**: `python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000`
- **Production**: `python -m uvicorn main:app --host 0.0.0.0 --port 8000`

API: http://localhost:8000 — Docs: http://localhost:8000/docs

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/config` | Model limits and defaults |
| POST | `/chat` | Damage assessment or follow-up; multipart (initial + files) or JSON (follow-up) |
| POST | `/conversations` | Create conversation |
| GET | `/conversations?user_id=` | List user's conversations |
| GET | `/conversations/{id}?user_id=` | Get one |
| DELETE | `/conversations/{id}?user_id=` | Delete one |
| GET | `/admin/analytics` | Aggregated stats |
| GET | `/admin/analytics/timeline?days=` | Timeline |
| GET | `/admin/conversations?sort_by=&order=` | List all (admin) |
| GET | `/admin/conversations/{id}` | Get one (admin) |
| GET | `/admin/conversations/{id}/stats` | Stats (admin) |
| DELETE | `/admin/conversations/{id}` | Delete one (admin) |
| POST | `/admin/conversations/bulk-delete` | Body: `["id1","id2"]` |
| GET | `/admin/models` | Model usage |
| GET | `/admin/system` | System info |
| GET | `/admin/activity/recent?limit=` | Recent activity |

## Usage Examples

**Initial assessment** (3 images required):

```bash
curl -X POST "http://localhost:8000/chat" \
  -F "user_id=user123" \
  -F "message=My car was hit in a parking lot. Assess the rear bumper and trunk." \
  -F "files=@wide-angle.jpg" -F "files=@straight-on.jpg" -F "files=@closeup.jpg"
```

**Follow-up** (text-only; optional files):

```bash
curl -X POST "http://localhost:8000/chat" \
  -F "user_id=user123" -F "conversation_id=RETURNED_ID" \
  -F "message=What is the estimated repair cost?"
```

**Create conversation** (optional; `/chat` without `conversation_id` also creates one):

```bash
curl -X POST "http://localhost:8000/conversations" -H "Content-Type: application/json" \
  -d '{"user_id":"user123","model_id":"us.anthropic.claude-sonnet-4-20250514-v1:0","temperature":0.2,"max_tokens":1000}'
```

## Postman

Import `Postman/Bedrock_Chat_API.postman_collection.json` and `Postman/Bedrock_Chat_API.postman_environment.json`; select the environment and run. See [Postman/README.md](Postman/README.md). Postman does not need AWS credentials.

## Constraints and Limits

- **Images**: ≤ 3.75 MB each; JPEG, PNG, GIF, WebP; up to 20 per message (Bedrock). Initial `/chat` without `conversation_id`: exactly 3 required.
- **Status codes**: 200, 400, 403, 404, 500.

## Technical Notes

- **System prompt**: In `config.py`; defines damage-assessment behavior for all `/chat` calls.
- **Storage**: In-memory, thread-safe. For production, replace with a DB or Redis.
- **Adding routes**: Add router in `routers/`, models in `models.py`, register in `main.py`.

## Dependencies (pyproject.toml)

fastapi, uvicorn, pydantic, pydantic-settings, boto3≥1.35.25, python-dotenv, python-multipart.
