import boto3
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from botocore.exceptions import ClientError
from typing import Dict, Any
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import AWS_REGION, logger

logger = logging.getLogger(__name__)


class ComprehendService:
    def __init__(self, region_name: str = None):
        self.region_name = region_name or AWS_REGION
        self.client = boto3.client('comprehend', region_name=self.region_name)
        self.executor = ThreadPoolExecutor(max_workers=5)
    
    def _detect_sentiment_sync(self, text: str, language_code: str = 'en') -> Dict[str, Any]:
        """Detect sentiment of text (sync)."""
        if not text or len(text.strip()) == 0:
            return {
                "sentiment": "NEUTRAL",
                "scores": {
                    "Positive": 0.0,
                    "Negative": 0.0,
                    "Neutral": 1.0,
                    "Mixed": 0.0
                }
            }
        
        try:
            response = self.client.detect_sentiment(
                Text=text,
                LanguageCode=language_code
            )
            
            return {
                "sentiment": response.get('Sentiment', 'NEUTRAL'),
                "scores": response.get('SentimentScore', {})
            }
            
        except ClientError as e:
            error_msg = f"Comprehend ClientError: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "sentiment": "NEUTRAL",
                "scores": {
                    "Positive": 0.0,
                    "Negative": 0.0,
                    "Neutral": 1.0,
                    "Mixed": 0.0
                }
            }
        except Exception as e:
            error_msg = f"Error detecting sentiment: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "sentiment": "NEUTRAL",
                "scores": {
                    "Positive": 0.0,
                    "Negative": 0.0,
                    "Neutral": 1.0,
                    "Mixed": 0.0
                }
            }
    
    async def detect_sentiment(self, text: str, language_code: str = 'en') -> Dict[str, Any]:
        """Detect sentiment of text (async)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._detect_sentiment_sync,
            text,
            language_code
        )

