"""
Dependency injection for FastAPI services.
"""
from functools import lru_cache
from services.textract_service import TextractService
from services.comprehend_service import ComprehendService
from services.translate_service import TranslateService
from services.polly_service import PollyService
from services.rekognition_service import RekognitionService
from config import AWS_REGION, TEXTRACT_S3_BUCKET


@lru_cache()
def get_textract_service() -> TextractService:
    """Get Textract service instance (singleton)."""
    return TextractService(region_name=AWS_REGION, s3_bucket=TEXTRACT_S3_BUCKET)


@lru_cache()
def get_comprehend_service() -> ComprehendService:
    """Get Comprehend service instance (singleton)."""
    return ComprehendService(region_name=AWS_REGION)


@lru_cache()
def get_translate_service() -> TranslateService:
    """Get Translate service instance (singleton)."""
    return TranslateService(region_name=AWS_REGION)


@lru_cache()
def get_polly_service() -> PollyService:
    """Get Polly service instance (singleton)."""
    return PollyService(region_name=AWS_REGION)


@lru_cache()
def get_rekognition_service() -> RekognitionService:
    """Get Rekognition service instance (singleton)."""
    return RekognitionService(region_name=AWS_REGION)

