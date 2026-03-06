"""
Lambda handler for the AI Agent Insure RAG Knowledge Base.

How it fits into the architecture:
  React frontend (S3)
      → POST /chat  (API Gateway HTTP API)
          → this Lambda
              → Bedrock retrieve_and_generate
                  → S3 Vectors knowledge base
                      → Claude generates an answer
  ← answer + cited source documents returned to the browser

The request body must be JSON: {"query": "your question here"}
The response body is JSON:    {"query": "...", "generated_response": "...", "s3_locations": [...]}

Environment variables (set in the Lambda configuration panel):
  KNOWLEDGE_BASE_ID    — the ID of your Bedrock Knowledge Base (e.g. "ABC123XYZ")
  FOUNDATION_MODEL_ARN — foundation model ARN for generation (Claude 3 Haiku, on-demand).
                         e.g. arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-haiku-20240307-v1:0
"""
import json
import os
import boto3
from botocore.exceptions import ClientError

# Read required config from environment variables.
# Lambda will fail at cold start if these are missing — that's intentional,
# so you catch misconfiguration immediately rather than at request time.
KNOWLEDGE_BASE_ID = os.environ["KNOWLEDGE_BASE_ID"]
FOUNDATION_MODEL_ARN = os.environ["FOUNDATION_MODEL_ARN"]

# boto3 client for the Bedrock Agent Runtime — this is the service that
# exposes retrieve_and_generate (RAG) and invoke_agent (Agents).
# Creating it outside the handler means it's reused across warm invocations.
client = boto3.client("bedrock-agent-runtime")

# These headers are returned with every response.
#
# Content-Type tells the browser the response body is JSON.
#
# The Access-Control-Allow-* headers are CORS headers. Browsers enforce a
# "same-origin policy" — by default a web page can only call APIs on the
# exact same domain it was served from. Since our React app is on S3 and the
# API is on a different domain (execute-api.amazonaws.com), the browser would
# block the request without these headers.
#
# The HTTP API Gateway handles the OPTIONS "preflight" request automatically
# via its own CORS config, so this Lambda never sees OPTIONS calls. However,
# returning these headers on the actual POST response as well is good practice
# — it acts as a fallback if the API Gateway CORS config is ever misconfigured.
CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "POST,OPTIONS",
}


def _get_query(event: dict) -> str:
    """
    Pull the 'query' string out of the API Gateway event.

    API Gateway passes the HTTP request body as a string (even if the
    original request was JSON), so we need to parse it ourselves.

    Args:
        event (dict): The raw API Gateway proxy event passed to the Lambda handler.
                      Expected to contain a 'body' key with a JSON string like
                      '{"query": "What does my policy cover?"}'.

    Returns:
        str: The value of the 'query' key from the request body,
             or an empty string if the body is missing, not valid JSON,
             or does not contain a 'query' key.
    """
    body = event.get("body", "")
    if isinstance(body, str):
        try:
            body = json.loads(body)  # parse the JSON string into a dict
        except (json.JSONDecodeError, TypeError):
            return ""
    if isinstance(body, dict):
        return body.get("query", "")
    return ""


def lambda_handler(event, _context):
    """
    Main entry point — Lambda calls this function for every request.

    Args:
        event (dict): The API Gateway proxy event. Contains the HTTP method,
                      headers, and request body. Expected body shape:
                      {"query": "your question here"}
        _context:     Lambda runtime context object (time remaining, request ID,
                      etc.). Not used here — the underscore prefix is a Python
                      convention for intentionally unused parameters.

    Returns:
        dict: API Gateway-compatible response with the following keys:
              - statusCode (int): 200 on success, 400 for bad input, 502 for
                                  Bedrock errors.
              - headers (dict):   CORS and Content-Type headers.
              - body (str):       JSON-encoded response string. On success:
                                  {"query": "...", "generated_response": "...",
                                   "s3_locations": ["s3://...", ...]}
                                  On error: {"error": "message"}
    """

    # --- Step 1: Extract and validate the query ---
    query = _get_query(event)
    if not query.strip():
        # Return a 400 Bad Request if the query is missing or blank.
        # The frontend will display this error message to the user.
        return {
            "statusCode": 400,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": "Missing or empty 'query' in request body."}),
        }

    # --- Step 2: Call Bedrock retrieve_and_generate ---
    # This single API call does two things in one shot:
    #   1. RETRIEVE — searches the S3 Vectors knowledge base for the most
    #                 relevant document chunks using semantic (vector) search
    #   2. GENERATE — sends those chunks + the user's question to Claude,
    #                 which synthesises a grounded answer from the source material
    try:
        rag_response = client.retrieve_and_generate(
            input={"text": query},
            retrieveAndGenerateConfiguration={
                "type": "KNOWLEDGE_BASE",
                "knowledgeBaseConfiguration": {
                    "knowledgeBaseId": KNOWLEDGE_BASE_ID,
                    "modelArn": FOUNDATION_MODEL_ARN,
                },
            },
        )
    except ClientError as e:
        # ClientError is raised when AWS rejects the API call (e.g. the Lambda
        # role is missing Bedrock permissions, or the KB ID is wrong).
        code = e.response["Error"]["Code"]
        msg = e.response["Error"]["Message"]
        print(f"Bedrock error [{code}]: {msg}")  # visible in CloudWatch Logs
        return {
            "statusCode": 502,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": f"Bedrock error ({code}): {msg}"}),
        }

    # --- Step 3: Extract cited source document URIs ---
    # Bedrock returns a list of "citations" — each citation points to the
    # specific document chunks it used to generate part of the answer.
    # We collect the unique S3 URIs so the frontend can show the user
    # which source files the answer came from.
    #
    # Response structure (simplified):
    #   rag_response
    #     └── citations[]
    #           └── retrievedReferences[]
    #                 └── location.s3Location.uri  ← the S3 file path
    s3_locations: list[str] = []
    seen: set[str] = set()  # used to deduplicate without changing order
    for citation in rag_response.get("citations", []):
        for ref in citation.get("retrievedReferences", []):
            uri = ref.get("location", {}).get("s3Location", {}).get("uri", "")
            if uri and uri not in seen:
                s3_locations.append(uri)
                seen.add(uri)

    # --- Step 4: Return the result ---
    result = {
        "query": query,
        "generated_response": rag_response["output"]["text"],  # Claude's answer
        "s3_locations": s3_locations,                          # cited source files
    }

    print(f"Query: {query!r} | Sources: {s3_locations}")  # logged to CloudWatch

    # API Gateway expects this exact shape: statusCode, headers, body (as a string).
    return {
        "statusCode": 200,
        "headers": CORS_HEADERS,
        "body": json.dumps(result),
    }
