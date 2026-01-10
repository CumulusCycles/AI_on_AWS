"""
Service module for invoking the Aggregate Lambda function.
"""
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
    
    # If local URL is configured, call local Lambda via HTTP
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
    
    # Otherwise, call deployed Lambda via AWS Lambda service API
    if not AGGREGATE_LAMBDA_FUNCTION_NAME:
        raise ValueError("Either AGGREGATE_LAMBDA_LOCAL_URL or AGGREGATE_LAMBDA_FUNCTION_NAME must be set")
    
    # Invoke AWS Lambda function using boto3 client
    logger.info(f"[STEP] Invoking deployed Lambda: {AGGREGATE_LAMBDA_FUNCTION_NAME}")
    response = lambda_client.invoke(
        FunctionName=AGGREGATE_LAMBDA_FUNCTION_NAME,
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )
    
    # Parse and validate AWS Lambda response
    response_payload = json.loads(response['Payload'].read())
    
    # Check for Lambda function errors
    if response.get('FunctionError'):
        error_message = response_payload.get('errorMessage', 'Unknown error')
        logger.error(f"[ERROR] Aggregate Lambda invocation failed: {error_message}")
        raise Exception(f"Lambda invocation error: {error_message}")
    
    claim_id = response_payload.get('claimId', 'unknown')
    logger.info(f"[STEP] Aggregate Lambda response received - claimId: {claim_id}, status: success")
    return response_payload