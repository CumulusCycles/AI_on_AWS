"""
FastAPI backend server for AWS Bedrock chat application
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
import os
import json
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="AWS Bedrock Chat API")

# CORS configuration from environment
cors_origins_str = os.getenv("CORS_ORIGINS", "*")
cors_origins = ["*"] if cors_origins_str == "*" else [origin.strip() for origin in cors_origins_str.split(",")]

# CORS middleware to allow Streamlit frontend to communicate
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Bedrock client
bedrock_client = boto3.client(
    service_name='bedrock-runtime',
    region_name=os.getenv('AWS_REGION', 'us-east-1')
)

# Default model - can be overridden via environment variable
DEFAULT_MODEL_ID = os.getenv('BEDROCK_MODEL_ID', 'us.anthropic.claude-haiku-4-5-20251001-v1:0')
# Anthropic API version for Bedrock
ANTHROPIC_VERSION = os.getenv('BEDROCK_ANTHROPIC_VERSION', 'bedrock-2023-05-31')


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"] = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model_id: Optional[str] = None
    temperature: Optional[float] = 0.2
    max_tokens: Optional[int] = 1000
    stream: Optional[bool] = False


class ChatResponse(BaseModel):
    message: str
    model_id: str
    usage: Optional[dict] = None


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/config")
async def get_config():
    """
    Configuration endpoint - returns default values and model-specific limits
    Frontend depends on this endpoint for initial slider values and ranges
    """
    # Load model limits from JSON file
    model_limits_path = os.path.join(os.path.dirname(__file__), "model_limits.json")
    try:
        with open(model_limits_path, "r") as f:
            model_limits = json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Model limits configuration file not found")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid model limits configuration file")
    
    # Get current model ID from environment
    current_model_id = os.getenv("BEDROCK_MODEL_ID", DEFAULT_MODEL_ID)
    
    # Get model-specific limits, fallback to default if model not found
    model_config = model_limits.get(current_model_id, model_limits.get("default", {}))
    
    # Get default values from environment
    default_temperature = float(os.getenv("DEFAULT_TEMPERATURE", "0.2"))
    default_max_tokens = int(os.getenv("DEFAULT_MAX_TOKENS", "1000"))
    
    return {
        "default_temperature": default_temperature,
        "default_max_tokens": default_max_tokens,
        "temperature_min": model_config.get("temperature_min", 0.0),
        "temperature_max": model_config.get("temperature_max", 1.0),
        "max_tokens_min": model_config.get("max_tokens_min", 100),
        "max_tokens_max": model_config.get("max_tokens_max", 8192),
        "model_id": current_model_id
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint that sends messages to AWS Bedrock and returns responses
    """
    model_id = request.model_id or DEFAULT_MODEL_ID
    
    try:
        # Format messages for Claude API format
        formatted_messages = []
        for msg in request.messages:
            formatted_messages.append({
                "role": msg.role,
                "content": [{"type": "text", "text": msg.content}]
            })
        
        # Prepare the request body for Bedrock
        body = {
            "anthropic_version": ANTHROPIC_VERSION,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "messages": formatted_messages
        }
        
        # Invoke the model
        response = bedrock_client.invoke_model(
            modelId=model_id,
            body=json.dumps(body)
        )
        
        # Parse the response
        response_body = json.loads(response['body'].read())
        
        # Extract the assistant's message
        assistant_message = ""
        if response_body.get('content'):
            for content_block in response_body['content']:
                if content_block.get('type') == 'text':
                    assistant_message += content_block.get('text', '')
        
        # Extract usage information if available
        usage = None
        if 'usage' in response_body:
            usage = {
                "input_tokens": response_body['usage'].get('input_tokens', 0),
                "output_tokens": response_body['usage'].get('output_tokens', 0)
            }
        
        return ChatResponse(
            message=assistant_message,
            model_id=model_id,
            usage=usage
        )
    
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        raise HTTPException(
            status_code=500,
            detail=f"AWS Bedrock error ({error_code}): {error_message}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Streaming chat endpoint that streams responses from AWS Bedrock in real-time
    Returns Server-Sent Events (SSE) format for streaming
    """
    model_id = request.model_id or DEFAULT_MODEL_ID
    
    async def generate_stream():
        try:
            # Format messages for Claude API format
            formatted_messages = []
            for msg in request.messages:
                formatted_messages.append({
                    "role": msg.role,
                    "content": [{"type": "text", "text": msg.content}]
                })
            
            # Prepare the request body for Bedrock
            body = {
                "anthropic_version": ANTHROPIC_VERSION,
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
                "messages": formatted_messages
            }
            
            # Invoke the model with streaming
            response = bedrock_client.invoke_model_with_response_stream(
                modelId=model_id,
                body=json.dumps(body)
            )
            
            # Process the stream
            full_message = ""
            usage = None
            
            for event in response['body']:
                if 'chunk' in event:
                    chunk = json.loads(event['chunk']['bytes'])
                    
                    # Handle different chunk types
                    if chunk.get('type') == 'content_block_delta':
                        # Text delta (incremental text)
                        if 'delta' in chunk and 'text' in chunk['delta']:
                            text_delta = chunk['delta']['text']
                            full_message += text_delta
                            # Send the delta as SSE
                            yield f"data: {json.dumps({'type': 'delta', 'text': text_delta})}\n\n"
                    
                    elif chunk.get('type') == 'content_block_start':
                        # Content block started
                        yield f"data: {json.dumps({'type': 'start'})}\n\n"
                    
                    elif chunk.get('type') == 'content_block_stop':
                        # Content block finished
                        yield f"data: {json.dumps({'type': 'stop'})}\n\n"
                    
                    elif chunk.get('type') == 'message_delta':
                        # Message delta (usage info)
                        if 'usage' in chunk.get('delta', {}):
                            usage = chunk['delta']['usage']
                    
                    elif chunk.get('type') == 'message_stop':
                        # Message complete
                        yield f"data: {json.dumps({'type': 'done', 'usage': usage})}\n\n"
            
            # Send final complete message
            yield f"data: {json.dumps({'type': 'complete', 'message': full_message, 'model_id': model_id, 'usage': usage})}\n\n"
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            error_data = json.dumps({
                'type': 'error',
                'error': f"AWS Bedrock error ({error_code}): {error_message}"
            })
            yield f"data: {error_data}\n\n"
        except Exception as e:
            error_data = json.dumps({
                'type': 'error',
                'error': f"Internal server error: {str(e)}"
            })
            yield f"data: {error_data}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)