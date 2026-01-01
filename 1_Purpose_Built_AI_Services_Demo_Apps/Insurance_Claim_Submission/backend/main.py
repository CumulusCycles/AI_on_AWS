from fastapi import FastAPI, File, UploadFile, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import List, Dict, Any, Optional
import logging
import os
from models.response_models import (
    ProcessingResult,
    ClaimDescriptionResult,
    FileResult,
    TextractResult,
    RekognitionResult,
    ComprehendResult,
    TranslateResult,
    PollyResult
)
from dependencies import (
    get_textract_service,
    get_comprehend_service,
    get_translate_service,
    get_polly_service,
    get_rekognition_service
)
from services.textract_service import TextractService
from services.comprehend_service import ComprehendService
from services.translate_service import TranslateService
from services.polly_service import PollyService
from services.rekognition_service import RekognitionService
from config import (
    AWS_REGION,
    BACKEND_HOST,
    BACKEND_PORT,
    CORS_ORIGINS,
    STATIC_DIR,
    MAX_FILE_SIZE_BYTES,
    SUPPORTED_EXTENSIONS,
    SUPPORTED_IMAGE_EXTENSIONS,
    POLLY_AUDIO_SNIPPET_LENGTH,
    LANGUAGE_VOICE_MAP,
    DEFAULT_VOICE,
    ENABLE_TRANSLATION,
    ENABLE_POLLY,
    ENABLE_REKOGNITION,
    logger
)

app = FastAPI(
    title="Claim Processing API",
    version="1.0.0",
    description="API for processing insurance claims using AWS AI services"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for audio
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    Returns the status of the API service.
    """
    return {
        "status": "healthy",
        "service": "Claim Processing API",
        "version": "1.0.0"
    }


def get_voice_for_language(language_code: str) -> str:
    """Get Polly voice ID for a given language code."""
    return LANGUAGE_VOICE_MAP.get(language_code, DEFAULT_VOICE)


async def translate_text_content(
    text: str,
    target_language: str,
    translate_service: TranslateService
) -> Optional[str]:
    """Translate text content."""
    if not text or target_language == "en":
        return None
    try:
        result = await translate_service.translate_text(text, target_language)
        return result.get("translated_text")
    except Exception as e:
        logger.error(f"Translation error: {str(e)}")
        return None


async def translate_labels(
    labels: List[Dict[str, Any]],
    target_language: str,
    translate_service: TranslateService
) -> List[Dict[str, Any]]:
    """Translate Rekognition labels using batch translation for efficiency."""
    if target_language == "en" or not ENABLE_TRANSLATION:
        return labels
    try:
        # Extract all label names
        label_names = [label.get("name", "") for label in labels if label.get("name")]
        
        if not label_names:
            return labels
        
        # Batch translate all labels at once
        translated_names = await translate_service.translate_batch(
            label_names, target_language
        )
        
        # Map translations back to labels
        translated = []
        name_index = 0
        for label in labels:
            label_name = label.get("name", "")
            if label_name and name_index < len(translated_names):
                translated_label = label.copy()
                translated_label["translated_name"] = translated_names[name_index]
                translated.append(translated_label)
                name_index += 1
            else:
                translated.append(label)
        
        return translated
    except Exception as e:
        logger.error(f"Label translation error: {str(e)}")
        return labels


async def translate_comprehend_results(
    comprehend_result: Dict[str, Any],
    target_language: str,
    translate_service: TranslateService
) -> Dict[str, Any]:
    """
    Translate Comprehend results (entities and key phrases) using batch translation.
    This reduces API calls from N+M to 1-2 calls.
    """
    if target_language == "en" or not ENABLE_TRANSLATION or not comprehend_result:
        return comprehend_result
    
    try:
        # Collect all texts to translate
        entity_texts = [entity.get("text", "") for entity in comprehend_result.get("entities", []) if entity.get("text")]
        phrase_texts = [phrase.get("text", "") for phrase in comprehend_result.get("key_phrases", []) if phrase.get("text")]
        
        # Batch translate entities
        translated_entities = []
        if entity_texts:
            translated_entity_texts = await translate_service.translate_batch(
                entity_texts, target_language
            )
            
            for i, entity in enumerate(comprehend_result.get("entities", [])):
                entity_text = entity.get("text", "")
                if entity_text and i < len(translated_entity_texts):
                    translated_entity = entity.copy()
                    translated_entity["translated_text"] = translated_entity_texts[i]
                    translated_entities.append(translated_entity)
                else:
                    translated_entities.append(entity)
        else:
            translated_entities = comprehend_result.get("entities", [])
        
        # Batch translate key phrases
        translated_key_phrases = []
        if phrase_texts:
            translated_phrase_texts = await translate_service.translate_batch(
                phrase_texts, target_language
            )
            
            for i, phrase in enumerate(comprehend_result.get("key_phrases", [])):
                phrase_text = phrase.get("text", "")
                if phrase_text and i < len(translated_phrase_texts):
                    translated_phrase = phrase.copy()
                    translated_phrase["translated_text"] = translated_phrase_texts[i]
                    translated_key_phrases.append(translated_phrase)
                else:
                    translated_key_phrases.append(phrase)
        else:
            translated_key_phrases = comprehend_result.get("key_phrases", [])
        
        return {
            "entities": translated_entities,
            "key_phrases": translated_key_phrases,
            "sentiment": comprehend_result.get("sentiment", {})
        }
    except Exception as e:
        logger.error(f"Comprehend translation error: {str(e)}")
        return comprehend_result


@app.post("/process-claim", response_model=ProcessingResult)
async def process_claim(
    claim_description: str = Form(..., description="Claim description text"),
    accident_photo: UploadFile = File(..., description="Accident photo (image file)"),
    insurance_forms: List[UploadFile] = File(..., description="Insurance forms (PDF or PNG files)"),
    textract_service: TextractService = Depends(get_textract_service),
    comprehend_service: ComprehendService = Depends(get_comprehend_service),
    translate_service: TranslateService = Depends(get_translate_service),
    polly_service: PollyService = Depends(get_polly_service),
    rekognition_service: RekognitionService = Depends(get_rekognition_service),
):
    """
    Process a claim with description text, accident photo, and insurance forms.
    Auto-detects language, processes files, and translates all results.
    """
    processing_status = {}
    
    # Step 1: Detect language from claim description
    logger.info("Detecting language from claim description")
    try:
        language_result = await comprehend_service.detect_language(claim_description)
        detected_language = language_result.get("language_code", "en")
        language_score = language_result.get("score", 1.0)
        processing_status["language_detection"] = "completed"
    except Exception as e:
        logger.error(f"Language detection failed: {str(e)}")
        detected_language = "en"
        language_score = 1.0
        processing_status["language_detection"] = f"error: {str(e)}"
    
    # Step 2: Process claim description
    logger.info(f"Processing claim description (language: {detected_language})")
    claim_comprehend_result = None
    claim_translated_comprehend = None
    claim_polly_result = None
    
    try:
        claim_comprehend_result = await comprehend_service.analyze_text(
            claim_description, language_code=detected_language
        )
        processing_status["claim_comprehend"] = "completed"
    except Exception as e:
        logger.error(f"Claim Comprehend error: {str(e)}")
        claim_comprehend_result = {
            "entities": [],
            "key_phrases": [],
            "sentiment": {"sentiment": "NEUTRAL", "scores": {}}
        }
        processing_status["claim_comprehend"] = f"error: {str(e)}"
    
    # Translate claim description results if needed (using batch translation)
    claim_translated_comprehend = None
    if detected_language != "en" and claim_comprehend_result and ENABLE_TRANSLATION:
        try:
            claim_translated_comprehend = await translate_comprehend_results(
                claim_comprehend_result, detected_language, translate_service
            )
            processing_status["claim_translation"] = "completed"
        except Exception as e:
            logger.error(f"Claim translation error: {str(e)}")
            processing_status["claim_translation"] = f"error: {str(e)}"
    
    # Generate Polly audio for claim description (if enabled)
    claim_polly_result = None
    if ENABLE_POLLY:
        try:
            voice_id = get_voice_for_language(detected_language)
            audio_text = claim_description[:POLLY_AUDIO_SNIPPET_LENGTH] if len(claim_description) > POLLY_AUDIO_SNIPPET_LENGTH else claim_description
            claim_polly_result = await polly_service.synthesize_speech(audio_text, voice_id)
            processing_status["claim_polly"] = "completed"
        except Exception as e:
            logger.error(f"Claim Polly error: {str(e)}")
            processing_status["claim_polly"] = f"error: {str(e)}"
    
    # Build claim description result
    claim_description_result = ClaimDescriptionResult(
        original_text=claim_description,
        detected_language=detected_language,
        language_score=language_score,
        comprehend=ComprehendResult(**claim_comprehend_result) if claim_comprehend_result else ComprehendResult(
            entities=[], key_phrases=[], sentiment={"sentiment": "NEUTRAL", "scores": {}}
        ),
        translated_comprehend=ComprehendResult(**claim_translated_comprehend) if claim_translated_comprehend else None,
        polly=PollyResult(**claim_polly_result) if claim_polly_result else None
    )
    
    # Step 3: Process files
    file_results = []
    
    # Process accident photo first (single image file)
    # Mark accident photo for special processing (skip Textract, keep Rekognition)
    all_files = [(accident_photo, True)] + [(form, False) for form in insurance_forms]
    
    for file, is_accident_photo in all_files:
        if not file.filename:
            continue
        
        file_result = FileResult(
            filename=file.filename,
            file_type="unknown"
        )
        
        try:
            # Read file content
            file_content = await file.read()
            
            # Validate file is not empty
            if len(file_content) == 0:
                file_result.error = "File is empty"
                file_results.append(file_result)
                logger.warning(f"File {file.filename} is empty")
                continue
            
            # Validate file size
            if len(file_content) > MAX_FILE_SIZE_BYTES:
                file_result.error = f"File size exceeds {MAX_FILE_SIZE_BYTES / (1024*1024):.1f} MB"
                file_results.append(file_result)
                continue
            
            # Determine file type
            file_extension = os.path.splitext(file.filename)[1].lower()
            if file_extension not in SUPPORTED_EXTENSIONS:
                file_result.error = f"Unsupported file type: {file_extension}"
                file_results.append(file_result)
                continue
            
            is_pdf = file_extension == '.pdf'
            is_image = file_extension in SUPPORTED_IMAGE_EXTENSIONS
            file_result.file_type = "pdf" if is_pdf else "image"
            
            logger.info(f"Processing {file.filename} (type: {file_result.file_type}, size: {len(file_content)} bytes, accident_photo: {is_accident_photo})")
            
            # Process with Textract
            # Skip Textract for accident photos (they're photos, not documents)
            textract_result = None
            textract_error = None
            if not is_accident_photo:
                try:
                    logger.info(f"Starting Textract analysis for {file.filename} (PDF: {is_pdf})")
                    textract_result = await textract_service.analyze_document(file_content, is_pdf=is_pdf)
                    if textract_result:
                        text_length = len(textract_result.get("full_text", ""))
                        logger.info(f"Textract completed for {file.filename}: extracted {text_length} characters")
                    processing_status[f"{file.filename}_textract"] = "completed"
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"Textract error for {file.filename}: {error_msg}", exc_info=True)
                    processing_status[f"{file.filename}_textract"] = f"error: {error_msg}"
                    textract_error = error_msg
                    # Create a TextractResult with error for better visibility
                    textract_result = {
                        "full_text": "",
                        "forms": [],
                        "tables": [],
                        "key_value_pairs": [],
                        "error": error_msg
                    }
            else:
                logger.info(f"Skipping Textract for accident photo {file.filename} (photos don't need text extraction)")
                processing_status[f"{file.filename}_textract"] = "skipped (accident photo)"
            
            # Process with Rekognition
            # Only call Rekognition for accident photos (not for insurance forms)
            rekognition_result = None
            if is_image and ENABLE_REKOGNITION and is_accident_photo:
                try:
                    rekognition_result = await rekognition_service.analyze_image(file_content)
                    processing_status[f"{file.filename}_rekognition"] = "completed"
                except Exception as e:
                    logger.error(f"Rekognition error for {file.filename}: {str(e)}")
                    processing_status[f"{file.filename}_rekognition"] = f"error: {str(e)}"
            elif is_image and not is_accident_photo:
                logger.info(f"Skipping Rekognition for insurance form {file.filename} (forms don't need visual analysis)")
                processing_status[f"{file.filename}_rekognition"] = "skipped (insurance form)"
            
            # Process with Comprehend (if text extracted)
            comprehend_result = None
            if textract_result and textract_result.get("full_text"):
                try:
                    comprehend_result = await comprehend_service.analyze_text(
                        textract_result["full_text"]
                    )
                    processing_status[f"{file.filename}_comprehend"] = "completed"
                except Exception as e:
                    logger.error(f"Comprehend error for {file.filename}: {str(e)}")
                    processing_status[f"{file.filename}_comprehend"] = f"error: {str(e)}"
            
            # Translate all results if needed (using batch translation)
            translated_textract = None
            translated_comprehend = None
            translated_rekognition = None
            
            if detected_language != "en" and ENABLE_TRANSLATION:
                # Translate Textract text
                if textract_result and textract_result.get("full_text"):
                    try:
                        translated_text = await translate_text_content(
                            textract_result["full_text"],
                            detected_language,
                            translate_service
                        )
                        if translated_text:
                            translated_textract = textract_result.copy()
                            translated_textract["translated_text"] = translated_text
                            processing_status[f"{file.filename}_translation"] = "completed"
                    except Exception as e:
                        logger.error(f"Translation error for {file.filename}: {str(e)}")
                
                # Translate Comprehend results (using batch translation)
                if comprehend_result:
                    try:
                        translated_comprehend = await translate_comprehend_results(
                            comprehend_result, detected_language, translate_service
                        )
                    except Exception as e:
                        logger.error(f"Comprehend translation error for {file.filename}: {str(e)}")
                
                # Translate Rekognition labels (using batch translation)
                if rekognition_result:
                    try:
                        translated_labels = await translate_labels(
                            rekognition_result.get("labels", []),
                            detected_language,
                            translate_service
                        )
                        translated_rekognition = rekognition_result.copy()
                        translated_rekognition["labels"] = translated_labels
                    except Exception as e:
                        logger.error(f"Rekognition translation error for {file.filename}: {str(e)}")
            
            # Note: Polly is only called for user-provided text, not for extracted text from files
            # This makes sense because audio of machine-extracted text is not useful to users
            file_polly_result = None
            
            # Build file result
            file_result.textract = TextractResult(**textract_result) if textract_result else None
            file_result.rekognition = RekognitionResult(**rekognition_result) if rekognition_result else None
            file_result.comprehend = ComprehendResult(**comprehend_result) if comprehend_result else None
            file_result.translated_textract = TextractResult(**translated_textract) if translated_textract else None
            file_result.translated_comprehend = ComprehendResult(**translated_comprehend) if translated_comprehend else None
            file_result.polly = PollyResult(**file_polly_result) if file_polly_result else None
            
        except Exception as e:
            logger.error(f"Error processing file {file.filename}: {str(e)}", exc_info=True)
            file_result.error = str(e)
        
        file_results.append(file_result)
    
    return ProcessingResult(
        detected_language=detected_language,
        claim_description=claim_description_result,
        files=file_results,
        processing_status=processing_status
    )


if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting server on {BACKEND_HOST}:{BACKEND_PORT}")
    uvicorn.run(app, host=BACKEND_HOST, port=BACKEND_PORT)

