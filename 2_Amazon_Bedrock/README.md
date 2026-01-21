# AWS Bedrock Chat Application

A full-stack chat application built with Streamlit (frontend) and FastAPI (backend) that uses AWS Bedrock for AI-powered conversations.

## Architecture

```
┌─────────────────┐         HTTP/REST         ┌──────────────────┐
│                 │ ────────────────────────► │                  │
│  Streamlit UI   │                           │   FastAPI Server │
│   (Frontend)    │ ◄──────────────────────── │    (Backend)     │
│                 │                           │                  │
└─────────────────┘                           └────────┬─────────┘
                                                       │
                                                       │ AWS SDK (boto3)
                                                       │
                                                       ▼
                                              ┌──────────────────┐
                                              │   AWS Bedrock    │
                                              │   (Claude API)   │
                                              └──────────────────┘
```

## Features

- 🤖 Chat interface with AWS Bedrock models (Claude 4.5 Haiku)
- ⚙️ Configurable temperature and max tokens with dynamic slider ranges
- 🔢 Optional max tokens limit (1000) for cost control
- 📊 Model information display (shows current model ID)
- 🌊 Streaming support for real-time response generation
- 💬 Conversation history management
- 🔌 RESTful API backend with FastAPI
- 🎨 Modern Streamlit UI
- 🔒 CORS support for cross-origin requests

## Prerequisites

1. **Python 3.12+** installed
2. **uv** installed ([Installation guide](https://github.com/astral-sh/uv))
3. **AWS Account** with Bedrock access enabled
4. **AWS Credentials** configured (via AWS CLI, environment variables, or IAM role)
5. **Bedrock Model Access** - Ensure you have access to the Claude models in your AWS region

### Setting up AWS Bedrock Access

1. Go to AWS Bedrock console
2. Request access to Claude models (e.g., `us.anthropic.claude-haiku-4-5-20251001-v1:0`)
3. Configure AWS credentials:
   ```bash
   aws configure
   ```

## Installation

**Note:** This project uses separate virtual environments for the frontend and backend. This provides clear separation, allows independent deployment, and follows best practices for full-stack applications.

1. **Clone or navigate to the project directory:**
   ```bash
   cd 2_Amazon_Bedrock
   ```

2. **Set up the backend:**
   ```bash
   cd backend
   uv sync
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
   This will automatically create a virtual environment and install all dependencies from `pyproject.toml`.

3. **Set up the frontend:**
   ```bash
   cd ../frontend
   uv sync
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
   This will automatically create a virtual environment and install all dependencies from `pyproject.toml`.

4. **Configure environment variables:**
   
   **Backend:**
   ```bash
   cd backend
   cp env.example .env
   # Edit .env with your AWS credentials and configuration
   ```
   
   **Frontend:**
   ```bash
   cd ../frontend
   cp env.example .env
   # Edit .env with API URL (optional - defaults to http://localhost:8000)
   ```

## Running the Application

**Start the FastAPI backend:**
   ```bash
   cd backend
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   python main.py
   # Or: uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```
   The API will be available at `http://localhost:8000`

**Start the Streamlit frontend** (in a new terminal):
   ```bash
   cd frontend
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   streamlit run streamlit_app.py
   ```
   The UI will open in your browser at `http://localhost:8501`

**Note:** The frontend requires the backend to be running. If the backend is not available, the frontend will display an error and refuse to start.

## User Interface

The Streamlit frontend provides:

- **Chat Interface**: Main conversation area with message history
- **Model Information**: Displays the current model ID from `backend/.env` in the sidebar
- **Temperature Slider**: Adjustable from 0.0 to 1.0 with 0.01 step increments for fine control
- **Max Tokens Slider**: Adjustable range based on the selected model (e.g., 100-64000 for Claude 4.5 Haiku)
- **Max Tokens Limit Checkbox**: When enabled, caps the max tokens slider at 1000 for cost control. Automatically resets the slider value if it exceeds 1000.
- **Enable Streaming Checkbox**: When checked, uses the streaming endpoint (`/chat/stream`) for real-time response generation from AWS Bedrock
- **Clear Chat Button**: Resets conversation history

## Configuration

### Available Models

The following Claude models are commonly available in Bedrock:
- `us.anthropic.claude-haiku-4-5-20251001-v1:0` (Default)
- `anthropic.claude-3-5-haiku-20241022-v1:0`
- `anthropic.claude-3-haiku-20240307-v1:0`
- `anthropic.claude-3-sonnet-20240229-v1:0`
- `anthropic.claude-3-opus-20240229-v1:0`

Check your AWS Bedrock console for available models in your region.

### Model-Specific Limits and Configuration

The backend uses two files together to configure parameter limits and defaults:

1. **`backend/.env`** - Sets which model to use and default starting values:
   - `BEDROCK_MODEL_ID`: Selects which model (e.g., `us.anthropic.claude-haiku-4-5-20251001-v1:0`)
   - `DEFAULT_TEMPERATURE`: Initial slider value for temperature (e.g., `0.2`)
   - `DEFAULT_MAX_TOKENS`: Initial slider value for max tokens (e.g., `1000`)

2. **`backend/model_limits.json`** - Defines model-specific min/max ranges:
   - Each model entry specifies `temperature_min/max` and `max_tokens_min/max`
   - These limits vary by model (e.g., Claude 4.5 Haiku allows up to 64000 tokens, older Haiku versions only 4096)

**How They Work Together:**
- The `/config` endpoint reads the model ID from `.env`, looks up its limits in `model_limits.json`, and combines them with default values from `.env`
- The frontend receives both the default starting values (from `.env`) and the allowed ranges (from `model_limits.json`) to configure sliders correctly
- **Important:** The frontend has a hard dependency on the backend `/config` endpoint. The frontend will not start if the backend is unavailable, ensuring configuration is always synchronized.

To add support for a new model, add its limits entry to `model_limits.json`.

### Backend Environment Variables (`backend/.env`)

| Variable | Description | Default |
|----------|-------------|---------|
| `AWS_REGION` | AWS region for Bedrock | `us-east-1` |
| `BEDROCK_MODEL_ID` | Model ID to use | `us.anthropic.claude-haiku-4-5-20251001-v1:0` |
| `BEDROCK_ANTHROPIC_VERSION` | Anthropic API version for Bedrock | `bedrock-2023-05-31` |
| `API_HOST` | FastAPI host | `0.0.0.0` |
| `API_PORT` | FastAPI port | `8000` |
| `CORS_ORIGINS` | CORS allowed origins (comma-separated, or `*` for all) | `*` |
| `DEFAULT_TEMPERATURE` | Default temperature | `0.2` |
| `DEFAULT_MAX_TOKENS` | Default max tokens | `1000` |

### Frontend Environment Variables (`frontend/.env`)

| Variable | Description | Default |
|----------|-------------|---------|
| `API_BASE_URL` | Base URL for the FastAPI backend | `http://localhost:8000` |

**Note:** Slider min/max ranges are automatically provided by the backend `/config` endpoint based on the selected model. See `backend/model_limits.json` for model-specific limits.

## API Endpoints

### `GET /health`
Health check endpoint. Returns `{"status": "healthy"}` when the API is running.

### `GET /config`
Get configuration including default values and model-specific parameter limits

**Response:**
```json
{
  "default_temperature": 0.2,
  "default_max_tokens": 1000,
  "temperature_min": 0.0,
  "temperature_max": 1.0,
  "max_tokens_min": 100,
  "max_tokens_max": 64000,
  "model_id": "us.anthropic.claude-haiku-4-5-20251001-v1:0"
}
```

The frontend uses this endpoint on load to configure slider ranges and initial values based on the model specified in `backend/.env`. The frontend displays the `model_id` in the UI and uses the parameter limits to set slider ranges dynamically.

### `POST /chat`
Send a chat message to AWS Bedrock (non-streaming)

**Request Body:**
```json
{
  "messages": [
    {"role": "user", "content": "Hello, how are you?"},
    {"role": "assistant", "content": "I'm doing well, thank you!"},
    {"role": "user", "content": "What can you help me with?"}
  ],
  "model_id": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
  "temperature": 0.2,
  "max_tokens": 1000
}
```

**Response:**
```json
{
  "message": "I can help you with...",
  "model_id": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
  "usage": {
    "input_tokens": 25,
    "output_tokens": 150
  }
}
```

### `POST /chat/stream`
Send a chat message to AWS Bedrock with streaming response (Server-Sent Events)

**Request Body:** (Same as `/chat` endpoint)

**Response:** Server-Sent Events (SSE) stream with the following event types:

- `data: {"type": "start"}` - Content block started
- `data: {"type": "delta", "text": "..."}` - Incremental text chunks
- `data: {"type": "stop"}` - Content block finished
- `data: {"type": "done", "usage": {...}}` - Message complete with usage info
- `data: {"type": "complete", "message": "...", "model_id": "...", "usage": {...}}` - Final complete message
- `data: {"type": "error", "error": "..."}` - Error occurred

The frontend automatically uses this endpoint when the "Enable Streaming" checkbox is checked in the UI.
