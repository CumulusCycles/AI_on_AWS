"""
Configuration module for the AWS AI Services Demo API.
"""
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# AWS Configuration
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

# Textract S3 Configuration (required for PDF processing)
TEXTRACT_S3_BUCKET = os.getenv("TEXTRACT_S3_BUCKET")

# Server Configuration
BACKEND_HOST = os.getenv("BACKEND_HOST", "0.0.0.0")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))

# CORS Configuration
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
CORS_ORIGINS = [
    FRONTEND_URL,
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# File Upload Configuration
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
SUPPORTED_IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.gif', '.bmp']
SUPPORTED_PDF_EXTENSIONS = ['.pdf']
SUPPORTED_EXTENSIONS = SUPPORTED_PDF_EXTENSIONS + SUPPORTED_IMAGE_EXTENSIONS

# AWS Service Limits
COMPREHEND_MAX_LENGTH = 4500
TRANSLATE_MAX_LENGTH = 9500
POLLY_MAX_LENGTH = 2900
POLLY_AUDIO_SNIPPET_LENGTH = 1000

# Static Files Configuration
STATIC_DIR = Path(__file__).parent / "static"
AUDIO_DIR = STATIC_DIR / "audio"
STATIC_DIR.mkdir(exist_ok=True)
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# Language to Voice Mapping
LANGUAGE_VOICE_MAP = {
    "es": "Lupe",  # Spanish - female
    "en": "Joanna",  # English - female
    "fr": "Celine",  # French - female
    "de": "Marlene",  # German - female
    "it": "Carla",  # Italian - female
    "pt": "Camila",  # Portuguese - female
    "ja": "Mizuki",  # Japanese - female
    "ko": "Seoyeon",  # Korean - female
    "zh": "Zhiyu",  # Chinese - female
}

# Default voice if language not found
DEFAULT_VOICE = "Joanna"

# Service Feature Flags (set to False to disable and reduce API calls)
ENABLE_TRANSLATION = os.getenv("ENABLE_TRANSLATION", "true").lower() == "true"
ENABLE_POLLY = os.getenv("ENABLE_POLLY", "true").lower() == "true"
ENABLE_REKOGNITION = os.getenv("ENABLE_REKOGNITION", "true").lower() == "true"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

