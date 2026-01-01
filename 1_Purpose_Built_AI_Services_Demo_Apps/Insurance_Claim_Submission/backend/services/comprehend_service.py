import boto3
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from botocore.exceptions import ClientError
from typing import Dict, Any, Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from exceptions import ComprehendError
from config import COMPREHEND_MAX_LENGTH

logger = logging.getLogger(__name__)


class ComprehendService:
    def __init__(self, region_name: str = "us-east-1"):
        self.client = boto3.client('comprehend', region_name=region_name)
        self.executor = ThreadPoolExecutor(max_workers=5)
    
    def _detect_language_sync(self, text: str) -> Dict[str, Any]:
        """Detect the dominant language of the text."""
        try:
            response = self.client.detect_dominant_language(Text=text)
            languages = response.get('Languages', [])
            if languages:
                dominant_language = languages[0]
                return {
                    "language_code": dominant_language.get('LanguageCode', 'en'),
                    "score": dominant_language.get('Score', 0.0)
                }
            return {"language_code": "en", "score": 1.0}
        except ClientError as e:
            logger.error(f"Error detecting language: {str(e)}")
            return {"language_code": "en", "score": 1.0}
    
    async def detect_language(self, text: str) -> Dict[str, Any]:
        """Detect the dominant language of the text (async)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._detect_language_sync,
            text
        )
    
    def _analyze_text_sync(self, text: str, language_code: str = 'en') -> Dict[str, Any]:
        """Analyze text using Comprehend (sync)."""
        if not text or len(text.strip()) == 0:
            return {
                "entities": [],
                "key_phrases": [],
                "sentiment": {"sentiment": "NEUTRAL", "scores": {}}
            }
        
        text_to_analyze = text[:COMPREHEND_MAX_LENGTH] if len(text) > COMPREHEND_MAX_LENGTH else text
        
        try:
            # Detect entities
            entities_response = self.client.detect_entities(
                Text=text_to_analyze,
                LanguageCode=language_code
            )
            
            # Detect key phrases
            key_phrases_response = self.client.detect_key_phrases(
                Text=text_to_analyze,
                LanguageCode=language_code
            )
            
            # Detect sentiment
            sentiment_response = self.client.detect_sentiment(
                Text=text_to_analyze,
                LanguageCode=language_code
            )
            
            return {
                "entities": [
                    {
                        "text": entity.get('Text', ''),
                        "type": entity.get('Type', ''),
                        "score": entity.get('Score', 0)
                    }
                    for entity in entities_response.get('Entities', [])
                ],
                "key_phrases": [
                    {
                        "text": phrase.get('Text', ''),
                        "score": phrase.get('Score', 0)
                    }
                    for phrase in key_phrases_response.get('KeyPhrases', [])
                ],
                "sentiment": {
                    "sentiment": sentiment_response.get('Sentiment', 'NEUTRAL'),
                    "scores": sentiment_response.get('SentimentScore', {})
                }
            }
            
        except ClientError as e:
            error_msg = f"Comprehend ClientError: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise ComprehendError(error_msg) from e
        except Exception as e:
            error_msg = f"Error analyzing text: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise ComprehendError(error_msg) from e
    
    async def analyze_text(self, text: str, language_code: str = 'en') -> Dict[str, Any]:
        """Analyze text using Comprehend (async)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._analyze_text_sync,
            text,
            language_code
        )

