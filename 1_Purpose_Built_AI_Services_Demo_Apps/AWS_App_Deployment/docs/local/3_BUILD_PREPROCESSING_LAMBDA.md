# Preprocessing Lambda Build Guide

This guide will help you build the Preprocessing/AI Pipeline Lambda function. This Lambda receives claim submissions, orchestrates AI service calls (Comprehend and Rekognition), invokes the Aggregate Lambda, and returns results to the frontend.

## Overview

We'll build a modular Lambda function with the following structure:
- **Main application** (`index.py`): FastAPI app, routes, and Lambda handler
- **Configuration module** (`config.py`): AWS client initialization and environment variables
- **Service modules** (`services/`): Separate modules for each AWS service integration
  - `comprehend.py`: Amazon Comprehend text analysis
  - `rekognition.py`: Amazon Rekognition image analysis
  - `lambda_invoker.py`: Aggregate Lambda invocation
- Local development server for testing

This modular structure provides better separation of concerns, testability, and maintainability while keeping the deployment simple.

## Prerequisites

- Python 3.11 or higher
- AWS CLI configured with credentials
- Access to AWS services: Comprehend, Rekognition, Lambda
- Virtual environment tool (venv or uv)

## Step-by-Step Build

### Step 1: Create Directory Structure

Create the Lambda function directory and services subdirectory:

```bash
cd 1_Purpose_Built_AI_Services_Demo_Apps/AWS_App_Deployment
mkdir -p lambda/preprocessing/services
cd lambda/preprocessing
```

### Step 2: Set Up Python Virtual Environment

Create and activate a virtual environment using `uv`:

```bash
uv venv --python=python3.12
source .venv/bin/activate  # On Mac/Linux
# or
.venv\Scripts\activate  # On Windows
```

**Note:** This creates a virtual environment using Python 3.12. If you don't have `uv` installed, install it with: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### Step 3: Install Dependencies

Create `requirements.txt`:

```txt
fastapi==0.104.1
mangum==0.17.0
python-multipart==0.0.6
boto3==1.29.7
python-dotenv==1.0.0
uvicorn[standard]==0.24.0
httpx==0.25.2
```

Install dependencies:

```bash
uv pip install -r requirements.txt -q
```

**What these do:**
- `fastapi` - Web framework for building the API
- `mangum` - ASGI adapter for running FastAPI on AWS Lambda
- `python-multipart` - Required for handling file uploads in FastAPI
- `boto3` - AWS SDK for Python (Comprehend, Rekognition, Lambda)
- `python-dotenv` - Load environment variables from .env files
- `uvicorn` - ASGI server for local development
- `httpx` - HTTP client for calling local Aggregate Lambda (async requests)

### Step 4: Create Environment Variables File

Create `.env.local.example`:

```bash
# Environment variables for local testing
# Copy this file to .env.local and update with your values
# .env.local takes precedence over .env and is gitignored

# AWS Region (used for Comprehend, Rekognition, and Lambda client)
REGION=us-east-1

# Aggregate Lambda function name (only needed if calling deployed Lambda via AWS API)
# Comment out or remove this line if using AGGREGATE_LAMBDA_LOCAL_URL
# AGGREGATE_LAMBDA_FUNCTION_NAME=demo-claim-app-aggregate

# Local aggregate Lambda URL (if running aggregate Lambda locally)
# Uncomment and set this to call a locally running aggregate Lambda instead of deployed one
# Example: AGGREGATE_LAMBDA_LOCAL_URL=http://localhost:8001
# AGGREGATE_LAMBDA_LOCAL_URL=

# AWS Credentials are loaded from:
# - AWS credentials file (~/.aws/credentials)
# - Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
# - IAM role (when running on EC2/Lambda)
```

Create `.env.local` (this file should be gitignored):

```bash
cp .env.local.example .env.local
# Then edit .env.local with your values
```

### Step 5: Create the FastAPI Application

We'll organize the code into multiple files for better maintainability and testability. Create the following structure:

**Directory structure:**
```
lambda/preprocessing/
├── index.py              # FastAPI app, routes, handler
├── config.py            # Configuration and AWS clients
└── services/
    ├── __init__.py
    ├── comprehend.py   # Amazon Comprehend integration
    ├── rekognition.py   # Amazon Rekognition integration
    └── lambda_invoker.py # Aggregate Lambda invocation
```

#### Step 5a: Create Configuration Module

Create `config.py`:

```python
import os
import logging
import boto3
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')
load_dotenv('.env')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# AWS clients
region = os.getenv('REGION', 'us-east-1')
comprehend_client = boto3.client('comprehend', region_name=region)
rekognition_client = boto3.client('rekognition', region_name=region)
lambda_client = boto3.client('lambda', region_name=region)

# Configuration
AGGREGATE_LAMBDA_FUNCTION_NAME = os.getenv('AGGREGATE_LAMBDA_FUNCTION_NAME')
AGGREGATE_LAMBDA_LOCAL_URL = os.getenv('AGGREGATE_LAMBDA_LOCAL_URL')
```

**What this does:**
- Loads environment variables from `.env.local` and `.env` files
- Initializes AWS clients (Comprehend, Rekognition, Lambda)
- Exports configuration variables for use in other modules

#### Step 5b: Create Services Package

Create the services directory and `__init__.py` file:

```bash
mkdir -p services
touch services/__init__.py
```

The `__init__.py` file can be empty - it just makes `services` a Python package.

#### Step 5c: Create Comprehend Service

Create `services/comprehend.py`:

```python
import logging
from config import comprehend_client, logger

def analyze_text_with_comprehend(text: str) -> dict:
    """
    Analyze text with Amazon Comprehend.
    Returns sentiment, entities, and key phrases.
    """
    try:
        # Detect dominant language
        lang_response = comprehend_client.detect_dominant_language(Text=text)
        detected_language = lang_response['Languages'][0]['LanguageCode']
        language_score = lang_response['Languages'][0]['Score']
        
        # Detect sentiment
        sentiment_response = comprehend_client.detect_sentiment(
            Text=text,
            LanguageCode=detected_language
        )
        
        # Detect entities
        entities_response = comprehend_client.detect_entities(
            Text=text,
            LanguageCode=detected_language
        )
        
        # Extract key phrases
        key_phrases_response = comprehend_client.detect_key_phrases(
            Text=text,
            LanguageCode=detected_language
        )
        
        return {
            "detected_language": detected_language,
            "language_score": language_score,
            "sentiment": {
                "sentiment": sentiment_response['Sentiment'],
                "scores": sentiment_response['SentimentScore']
            },
            "entities": [
                {
                    "text": entity['Text'],
                    "type": entity['Type'],
                    "score": entity['Score']
                }
                for entity in entities_response['Entities']
            ],
            "key_phrases": [
                {
                    "text": phrase['Text'],
                    "score": phrase['Score']
                }
                for phrase in key_phrases_response['KeyPhrases']
            ]
        }
    except Exception as e:
        logger.error(f"Error in Comprehend analysis: {str(e)}", exc_info=True)
        raise
```

**What this does:**
- Encapsulates all Amazon Comprehend API calls
- Detects language, sentiment, entities, and key phrases
- Returns structured results for use by the main application

#### Step 5d: Create Rekognition Service

Create `services/rekognition.py`:

```python
import logging
from config import rekognition_client, logger

def analyze_image_with_rekognition(image_bytes: bytes) -> dict:
    """
    Analyze image with Amazon Rekognition.
    Returns labels and text detections.
    """
    try:
        # Detect labels
        labels_response = rekognition_client.detect_labels(
            Image={'Bytes': image_bytes},
            MaxLabels=10,
            MinConfidence=70
        )
        
        # Detect text
        text_response = rekognition_client.detect_text(
            Image={'Bytes': image_bytes}
        )
        
        return {
            "labels": [
                {
                    "name": label['Name'],
                    "confidence": label['Confidence'],
                    "categories": [cat['Name'] for cat in label.get('Categories', [])]
                }
                for label in labels_response['Labels']
            ],
            "text_detections": [
                {
                    "text": detection['DetectedText'],
                    "confidence": detection['Confidence'],
                    "type": detection['Type']
                }
                for detection in text_response['TextDetections']
            ]
        }
    except Exception as e:
        logger.error(f"Error in Rekognition analysis: {str(e)}", exc_info=True)
        raise
```

**What this does:**
- Encapsulates all Amazon Rekognition API calls
- Detects labels and text in images
- Returns structured results for use by the main application

#### Step 5e: Create Lambda Invoker Service

Create `services/lambda_invoker.py`:

```python
import json
import logging
import httpx
from config import lambda_client, AGGREGATE_LAMBDA_FUNCTION_NAME, AGGREGATE_LAMBDA_LOCAL_URL, logger

async def invoke_aggregate_lambda(
    claim_description: str,
    image_bytes: bytes,
    image_filename: str,
    comprehend_result: dict,
    rekognition_result: dict
) -> dict:
    """
    Invoke the Aggregate Lambda function.
    Can call either a locally running Lambda or a deployed Lambda.
    """
    payload = {
        "claim_description": claim_description,
        "image_bytes": image_bytes.hex(),  # Convert bytes to hex string for JSON
        "image_filename": image_filename,
        "comprehend_result": comprehend_result,
        "rekognition_result": rekognition_result
    }
    
    # If local URL is configured, call local Lambda
    if AGGREGATE_LAMBDA_LOCAL_URL:
        logger.info(f"[STEP] Calling local Aggregate Lambda at {AGGREGATE_LAMBDA_LOCAL_URL}")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{AGGREGATE_LAMBDA_LOCAL_URL}/aggregate",
                json=payload,
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            claim_id = result.get('claimId', 'unknown')
            logger.info(f"[STEP] Aggregate Lambda response received - claimId: {claim_id}, status: {response.status_code}")
            return result
    
    # Otherwise, call deployed Lambda via AWS API
    if not AGGREGATE_LAMBDA_FUNCTION_NAME:
        raise ValueError("Either AGGREGATE_LAMBDA_LOCAL_URL or AGGREGATE_LAMBDA_FUNCTION_NAME must be set")
    
    logger.info(f"[STEP] Invoking deployed Lambda: {AGGREGATE_LAMBDA_FUNCTION_NAME}")
    response = lambda_client.invoke(
        FunctionName=AGGREGATE_LAMBDA_FUNCTION_NAME,
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )
    
    # Parse response
    response_payload = json.loads(response['Payload'].read())
    
    if response.get('FunctionError'):
        error_message = response_payload.get('errorMessage', 'Unknown error')
        logger.error(f"[ERROR] Aggregate Lambda invocation failed: {error_message}")
        raise Exception(f"Lambda invocation error: {error_message}")
    
    claim_id = response_payload.get('claimId', 'unknown')
    logger.info(f"[STEP] Aggregate Lambda response received - claimId: {claim_id}, status: success")
    return response_payload
```

**What this does:**
- Encapsulates Aggregate Lambda invocation logic
- Supports both local (HTTP) and deployed (AWS API) Lambda calls
- Handles error responses and logging

#### Step 5f: Create Main Application File

Create `index.py`:

```python
import os
import json
import logging
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from dotenv import load_dotenv

# Import services
from services.comprehend import analyze_text_with_comprehend
from services.rekognition import analyze_image_with_rekognition
from services.lambda_invoker import invoke_aggregate_lambda
from config import logger

# Load environment variables
load_dotenv('.env.local')
load_dotenv('.env')

# Initialize FastAPI app
app = FastAPI(title="Claim Preprocessing API", version="1.0.0")

# Add middleware to log all requests (must be added before other middleware)
@app.middleware("http")
async def log_requests(request, call_next):
    logger.info(f"[MIDDLEWARE] Request received - method: {request.method}, path: {request.url.path}, headers: {dict(request.headers)}")
    try:
        response = await call_next(request)
        logger.info(f"[MIDDLEWARE] Response sent - status: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"[MIDDLEWARE] Error in request processing: {str(e)}", exc_info=True)
        raise

# CORS configuration for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Frontend dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "preprocessing"}


# FastAPI automatically provides interactive API documentation at /docs
# Visit http://localhost:8000/docs when the server is running


@app.post("/process-claim")
async def process_claim(
    claim_description: str = Form(...),
    accident_photo: UploadFile = File(...)
):
    """
    Process a claim submission:
    1. Analyze text with Amazon Comprehend
    2. Analyze image with Amazon Rekognition
    3. Invoke Aggregate Lambda to store data and aggregate results
    4. Return aggregated JSON response
    """
    logger.info(f"[ENDPOINT] /process-claim endpoint called - THIS LOG CONFIRMS ENDPOINT WAS HIT")
    logger.info(f"[REQUEST] Processing claim - description length: {len(claim_description)} chars, filename: {accident_photo.filename}")
    try:
        
        # Read image file
        image_bytes = await accident_photo.read()
        logger.info(f"[STEP] Image read - size: {len(image_bytes)} bytes")
        
        # Step 1: Analyze text with Comprehend
        logger.info("[STEP] Calling Amazon Comprehend for text analysis...")
        comprehend_result = analyze_text_with_comprehend(claim_description)
        logger.info(f"[STEP] Comprehend analysis complete - language: {comprehend_result.get('detected_language', 'unknown')}, sentiment: {comprehend_result.get('sentiment', {}).get('sentiment', 'unknown')}")
        
        # Step 2: Analyze image with Rekognition
        logger.info("[STEP] Calling Amazon Rekognition for image analysis...")
        rekognition_result = analyze_image_with_rekognition(image_bytes)
        labels_count = len(rekognition_result.get('labels', []))
        text_count = len(rekognition_result.get('text_detections', []))
        logger.info(f"[STEP] Rekognition analysis complete - labels: {labels_count}, text detections: {text_count}")
        
        # Step 3: Invoke Aggregate Lambda
        logger.info("[STEP] Invoking Aggregate Lambda for storage and aggregation...")
        aggregate_result = await invoke_aggregate_lambda(
            claim_description=claim_description,
            image_bytes=image_bytes,
            image_filename=accident_photo.filename,
            comprehend_result=comprehend_result,
            rekognition_result=rekognition_result
        )
        
        claim_id = aggregate_result.get('claimId', 'unknown')
        s3_url = aggregate_result.get('storage', {}).get('s3_url', 'N/A')
        logger.info(f"[RESPONSE] Claim processing completed successfully - claimId: {claim_id}, s3_url: {s3_url}")
        logger.info(f"[ENDPOINT] Returning response from /process-claim endpoint")
        return aggregate_result
        
    except Exception as e:
        logger.error(f"[ERROR] Error processing claim: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing claim: {str(e)}")


# Lambda handler for AWS deployment with logging wrapper
_mangum_handler = Mangum(app, lifespan="off")

def handler(event, context):
    """Lambda handler wrapper to ensure logging works"""
    logger.info(f"[LAMBDA_HANDLER_START] Preprocessing Lambda handler invoked")
    if isinstance(event, dict):
        logger.info(f"[LAMBDA_HANDLER_START] Event keys: {list(event.keys())}")
        # Log path information from API Gateway HTTP API event
        if 'requestContext' in event:
            request_context = event.get('requestContext', {})
            http_info = request_context.get('http', {})
            path = http_info.get('path', 'N/A')
            method = http_info.get('method', 'N/A')
            logger.info(f"[LAMBDA_HANDLER_START] API Gateway path: {path}, method: {method}")
        elif 'path' in event:
            logger.info(f"[LAMBDA_HANDLER_START] Event path: {event.get('path')}, method: {event.get('httpMethod')}")
        logger.info(f"[LAMBDA_HANDLER_START] Full event (first 500 chars): {json.dumps(event, default=str)[:500]}")
        # Log request body info if available
        if 'requestContext' in event and 'body' in event:
            body_preview = str(event.get('body', ''))[:200]
            logger.info(f"[LAMBDA_HANDLER_START] Request body preview: {body_preview}")
    try:
        # Mangum handles async automatically, just call it
        logger.info(f"[LAMBDA_HANDLER] Calling Mangum handler...")
        result = _mangum_handler(event, context)
        
        # Mangum may return a coroutine, handle it
        import asyncio
        if asyncio.iscoroutine(result):
            logger.info(f"[LAMBDA_HANDLER] Mangum returned coroutine, awaiting...")
            result = asyncio.run(result)
        
        if isinstance(result, dict):
            status_code = result.get('statusCode', 'N/A')
            body = result.get('body', '')
            body_preview = str(body)[:200] if body else ''
            logger.info(f"[LAMBDA_HANDLER_END] Preprocessing Lambda completed - statusCode: {status_code}, body length: {len(str(body)) if body else 0}")
            logger.info(f"[RESPONSE] Returning response to API Gateway - statusCode: {status_code}, body preview: {body_preview}")
        else:
            logger.info(f"[LAMBDA_HANDLER_END] Preprocessing Lambda completed - result type: {type(result)}")
        return result
    except Exception as e:
        logger.error(f"[LAMBDA_HANDLER_ERROR] Preprocessing Lambda error: {str(e)}", exc_info=True)
        raise
```

**What this does:**
- Sets up FastAPI with CORS for local development
- Handles multipart/form-data file uploads
- Orchestrates the claim processing workflow
- Imports and uses service modules for AWS integrations
- Provides Lambda handler wrapper using Mangum

**Benefits of this structure:**
- **Separation of concerns**: Each service has its own module
- **Testability**: Services can be tested independently
- **Maintainability**: Changes to one service don't affect others
- **Reusability**: Service modules can be reused in other projects
- **Clarity**: Main application file focuses on orchestration, not implementation details

### Step 6: Create Local Development Server

Create `run_local.py`:

```python
import uvicorn
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv('.env.local')
load_dotenv('.env')

if __name__ == "__main__":
    port = int(os.getenv('PORT', 8000))
    uvicorn.run(
        "index:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
```

**What this does:**
- Runs FastAPI as a local development server
- Enables auto-reload on code changes
- Loads environment variables from .env files

### Step 7: Create .gitignore

Create `.gitignore`:

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
.venv/
env/
ENV/

# Environment variables
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
```

### Step 8: Configure AWS Credentials

Before testing the Lambda function, you need to configure AWS credentials so the code can call Amazon Comprehend and Rekognition services.

**Configure AWS credentials:**

```bash
aws configure
```

This will prompt you for:
- **AWS Access Key ID**: Your AWS access key
- **AWS Secret Access Key**: Your AWS secret key
- **Default region name**: The AWS region (e.g., `us-east-1`)
- **Default output format**: Can be `json` (press Enter for default)

This creates/updates `~/.aws/credentials` and `~/.aws/config` files.

**Verify your credentials:**

```bash
aws sts get-caller-identity
```

This should return your AWS account ID and user ARN. If it fails, your credentials are invalid.

**Required AWS Permissions:**

Your AWS credentials need permissions for:
- `comprehend:DetectDominantLanguage`
- `comprehend:DetectSentiment`
- `comprehend:DetectEntities`
- `comprehend:DetectKeyPhrases`
- `rekognition:DetectLabels`
- `rekognition:DetectText`
- `lambda:InvokeFunction` (for Aggregate Lambda, when it's built)

**Note:** If you don't have AWS credentials yet, you'll need to:
1. Create an IAM user in AWS Console
2. Attach policies with the permissions above (or use `AmazonComprehendFullAccess` and `AmazonRekognitionFullAccess`)
3. Create access keys for that user
4. Use those keys with `aws configure`

### Step 9: Configure Aggregate Lambda URL

Before testing, you need to set the Aggregate Lambda configuration in your `.env.local` file. Even though the Aggregate Lambda hasn't been built yet, you need to set this to avoid validation errors.

**Edit `.env.local` and set:**

```bash
AGGREGATE_LAMBDA_LOCAL_URL=http://localhost:8001
```

**What this does:**
- Tells the Preprocessing Lambda where to call the Aggregate Lambda
- Even if the Aggregate Lambda doesn't exist yet, this allows the code to proceed past validation
- When you test `/process-claim`, it will:
  - ✅ Successfully call Comprehend and Rekognition
  - ❌ Fail when trying to call the Aggregate Lambda (expected - it doesn't exist yet)
  - This allows you to test the AI service integrations

**Note:** Once you build the Aggregate Lambda (in a future guide), you can either:
- Keep using `AGGREGATE_LAMBDA_LOCAL_URL` if running it locally
- Or switch to `AGGREGATE_LAMBDA_FUNCTION_NAME` if deploying to AWS

### Step 10: Test Locally

Start the local development server:

```bash
python run_local.py
```

The server will start on `http://localhost:8000`.

**Test the health endpoint:**
```bash
curl http://localhost:8000/health
```

**Expected response:**
```json
{"status": "healthy", "service": "preprocessing"}
```

**View API documentation:**
FastAPI automatically generates interactive API documentation. Open your browser and visit:
```
http://localhost:8000/docs
```

This provides a Swagger UI where you can:
- View all available endpoints
- See request/response schemas
- Test endpoints directly from the browser

**Important:** When testing the `/process-claim` endpoint:
- Make sure you've completed Step 8 (Configure AWS Credentials) before testing
- Make sure you've completed Step 9 (Configure Aggregate Lambda URL) before testing
- The endpoint will call Amazon Comprehend and Rekognition (requires valid AWS credentials)
- The endpoint will try to invoke the Aggregate Lambda (this will fail with a connection error until the Aggregate Lambda is built - that's expected and allows you to test the AI services)
