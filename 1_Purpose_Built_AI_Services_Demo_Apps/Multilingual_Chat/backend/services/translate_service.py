import boto3
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from botocore.exceptions import ClientError
from typing import Dict, Any, List
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import AWS_REGION, logger

logger = logging.getLogger(__name__)


class TranslateService:
    def __init__(self, region_name: str = None):
        self.region_name = region_name or AWS_REGION
        self.client = boto3.client('translate', region_name=self.region_name)
        self.executor = ThreadPoolExecutor(max_workers=5)
    
    def _translate_text_sync(self, text: str, target_language: str, source_language: str = 'auto') -> Dict[str, Any]:
        """Translate text (sync)."""
        if not text or len(text.strip()) == 0:
            return {
                "translated_text": "",
                "source_language": source_language,
                "target_language": target_language
            }
        
        try:
            response = self.client.translate_text(
                Text=text,
                SourceLanguageCode=source_language,
                TargetLanguageCode=target_language
            )
            
            return {
                "translated_text": response.get('TranslatedText', ''),
                "source_language": response.get('SourceLanguageCode', source_language),
                "target_language": target_language
            }
            
        except ClientError as e:
            error_msg = f"Translate ClientError: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Error translating text: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise Exception(error_msg) from e
    
    async def translate_text(self, text: str, target_language: str, source_language: str = 'auto') -> Dict[str, Any]:
        """Translate text (async)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._translate_text_sync,
            text,
            target_language,
            source_language
        )
    
    async def translate_to_multiple(self, text: str, target_languages: List[str], source_language: str = 'auto') -> Dict[str, str]:
        """
        Translate text to multiple target languages in parallel.
        Returns a dictionary mapping target language codes to translated text.
        """
        if not text or len(text.strip()) == 0:
            return {lang: "" for lang in target_languages}
        
        # Create translation tasks for all target languages
        tasks = [
            self.translate_text(text, target_lang, source_language)
            for target_lang in target_languages
        ]
        
        # Execute all translations in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Build result dictionary
        translated_dict = {}
        for i, target_lang in enumerate(target_languages):
            if isinstance(results[i], Exception):
                logger.error(f"Translation error for {target_lang}: {results[i]}")
                translated_dict[target_lang] = text  # Fallback to original text
            else:
                translated_dict[target_lang] = results[i].get("translated_text", text)
        
        return translated_dict

