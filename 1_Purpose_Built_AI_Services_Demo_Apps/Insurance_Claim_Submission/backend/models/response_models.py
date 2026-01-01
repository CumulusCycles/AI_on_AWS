from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class TextractResult(BaseModel):
    full_text: str
    forms: List[Dict[str, Any]] = []
    tables: List[Dict[str, Any]] = []
    key_value_pairs: List[Dict[str, str]] = []
    translated_text: Optional[str] = None
    error: Optional[str] = None


class ComprehendResult(BaseModel):
    entities: List[Dict[str, Any]]
    key_phrases: List[Dict[str, Any]]
    sentiment: Dict[str, Any]
    translated_entities: Optional[List[Dict[str, Any]]] = None
    translated_key_phrases: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


class RekognitionResult(BaseModel):
    labels: List[Dict[str, Any]]
    text_detections: List[Dict[str, Any]] = []
    translated_labels: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


class TranslateResult(BaseModel):
    translated_text: str
    source_language: str
    target_language: str
    error: Optional[str] = None


class PollyResult(BaseModel):
    audio_url: str
    text: str
    voice_id: str
    error: Optional[str] = None


class ClaimDescriptionResult(BaseModel):
    original_text: str
    detected_language: str
    language_score: float
    comprehend: ComprehendResult
    translated_comprehend: Optional[ComprehendResult] = None
    polly: Optional[PollyResult] = None
    error: Optional[str] = None


class FileResult(BaseModel):
    filename: str
    file_type: str
    textract: Optional[TextractResult] = None
    rekognition: Optional[RekognitionResult] = None
    comprehend: Optional[ComprehendResult] = None
    translated_textract: Optional[TextractResult] = None
    translated_comprehend: Optional[ComprehendResult] = None
    polly: Optional[PollyResult] = None
    error: Optional[str] = None


class ProcessingResult(BaseModel):
    detected_language: str
    claim_description: ClaimDescriptionResult
    files: List[FileResult]
    processing_status: Dict[str, str] = {}

