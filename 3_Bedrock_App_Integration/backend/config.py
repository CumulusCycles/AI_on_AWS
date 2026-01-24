"""
Configuration and constants for the Bedrock App Integration API.

- AWS: region, Bedrock runtime client (uses AWS_REGION, optional AWS_ACCESS_KEY_ID/
  AWS_SECRET_ACCESS_KEY or ~/.aws/credentials).
- Model: BEDROCK_MODEL_ID, DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS.
- File upload: MAX_FILE_SIZE (3.75 MB, Bedrock limit), SUPPORTED_IMAGE_TYPES,
  IMAGE_FORMAT_MAP for Converse API image blocks.
- SYSTEM_PROMPT: instructs the model to act as a damage assessment specialist.
- CORS_ORIGINS: comma-separated or "*"; used by main.py.
"""
import os

import boto3
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# AWS
# ---------------------------------------------------------------------------
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# bedrock-runtime (Converse API); credentials from env or ~/.aws/credentials
bedrock_client = boto3.client(
    service_name="bedrock-runtime",
    region_name=AWS_REGION,
)

# ---------------------------------------------------------------------------
# Model defaults (overridable per request or via env)
# ---------------------------------------------------------------------------
DEFAULT_MODEL_ID = os.getenv(
    "BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-20250514-v1:0"
)
DEFAULT_TEMPERATURE = 0.2
DEFAULT_MAX_TOKENS = 1000

# ---------------------------------------------------------------------------
# File upload (Bedrock: 3.75 MB per image, max 20 per message)
# ---------------------------------------------------------------------------
MAX_FILE_SIZE = 3.75 * 1024 * 1024  # bytes
SUPPORTED_IMAGE_TYPES = [
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/gif",
    "image/webp",
]

# MIME -> Converse API "format" (jpeg, png, gif, webp)
IMAGE_FORMAT_MAP = {
    "image/jpeg": "jpeg",
    "image/jpg": "jpeg",
    "image/png": "png",
    "image/gif": "gif",
    "image/webp": "webp",
}

# ---------------------------------------------------------------------------
# System prompt: sent with every /chat request so the model stays in role
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are an expert automobile damage assessment specialist. Your role is to analyze vehicle damage from images and descriptions provided by insured individuals.

When assessing damage:
1. Analyze the provided image(s) carefully to identify all visible damage
2. Consider the description provided by the insured
3. Provide a comprehensive damage assessment using clear, professional formatting with markdown:
   - Use **bold** for section headings (## Damage Summary, ## Detailed Analysis, etc.)
   - Use bullet points (-) or numbered lists for organized information
   - Use **bold text** to emphasize important details (severity levels, safety concerns)
   - Structure your response with clear sections:
     * ## Damage Summary
     * ## Detailed Damage Analysis
     * ## Safety Concerns
     * ## Repair Complexity Assessment
     * ## Recommendations

Include:
   - Type of damage (dents, scratches, structural damage, glass damage, etc.)
   - Severity assessment (minor, moderate, severe) - use **bold** for severity levels
   - Visible damage locations on the vehicle
   - Safety concerns (if any) - clearly highlight with **bold**
   - Estimated repair complexity

For follow-up questions:
- Answer questions about the assessment you provided
- Clarify any aspects of the damage
- Provide guidance on next steps for the claims process
- Help the insured understand what information they may need to provide

Format your response using markdown for professional presentation. Be professional, clear, and helpful. Focus on providing accurate damage assessments that will help with the insurance claims process."""

# ---------------------------------------------------------------------------
# CORS: "*" or comma-separated origins (e.g. http://localhost:3000,http://localhost:3001)
# ---------------------------------------------------------------------------
CORS_ORIGINS_STR = os.getenv("CORS_ORIGINS", "*")
CORS_ORIGINS = (
    ["*"]
    if CORS_ORIGINS_STR == "*"
    else [o.strip() for o in CORS_ORIGINS_STR.split(",")]
)
