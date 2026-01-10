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