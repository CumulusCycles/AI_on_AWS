import boto3
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from botocore.exceptions import ClientError
from typing import Dict, Any, List
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from exceptions import TranslateError
from config import TRANSLATE_MAX_LENGTH

logger = logging.getLogger(__name__)


class TranslateService:
    def __init__(self, region_name: str = "us-east-1"):
        self.client = boto3.client('translate', region_name=region_name)
        self.executor = ThreadPoolExecutor(max_workers=5)
    
    def _translate_text_sync(self, text: str, target_language: str, source_language: str = 'auto') -> Dict[str, Any]:
        """Translate text (sync)."""
        if not text or len(text.strip()) == 0:
            return {
                "translated_text": "",
                "source_language": source_language,
                "target_language": target_language
            }
        
        # Translate has a 10000 byte limit
        text_to_translate = text[:TRANSLATE_MAX_LENGTH] if len(text) > TRANSLATE_MAX_LENGTH else text
        
        try:
            response = self.client.translate_text(
                Text=text_to_translate,
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
            raise TranslateError(error_msg) from e
        except Exception as e:
            error_msg = f"Error translating text: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise TranslateError(error_msg) from e
    
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
    
    async def translate_list(self, items: List[str], target_language: str, source_language: str = 'auto') -> List[str]:
        """Translate a list of strings (makes individual calls - use translate_batch for optimization)."""
        translated = []
        for item in items:
            if item:
                result = await self.translate_text(item, target_language, source_language)
                translated.append(result.get('translated_text', item))
            else:
                translated.append(item)
        return translated
    
    def _translate_batch_sync(self, texts: List[str], target_language: str, source_language: str = 'auto', delimiter: str = " ||| ") -> Dict[str, List[str]]:
        """
        Translate multiple texts in a single API call by batching them together.
        Uses a delimiter to separate texts, then splits the result.
        This reduces API calls from N to 1 (or a few if batching is needed due to size limits).
        """
        if not texts or all(not text or len(text.strip()) == 0 for text in texts):
            return {"translated_texts": [""] * len(texts)}
        
        # Filter out empty texts but keep track of indices
        non_empty_texts = []
        indices = []
        for i, text in enumerate(texts):
            if text and len(text.strip()) > 0:
                non_empty_texts.append(text)
                indices.append(i)
        
        if not non_empty_texts:
            return {"translated_texts": [""] * len(texts)}
        
        # Batch texts with delimiter, respecting 10KB limit
        batches = []
        current_batch = []
        current_size = 0
        
        for text in non_empty_texts:
            text_size = len(text.encode('utf-8'))
            delimiter_size = len(delimiter.encode('utf-8'))
            
            # If single text exceeds limit, truncate it
            if text_size > TRANSLATE_MAX_LENGTH:
                text = text[:TRANSLATE_MAX_LENGTH]
                text_size = TRANSLATE_MAX_LENGTH
            
            # Check if adding this text would exceed limit
            if current_batch and (current_size + delimiter_size + text_size) > TRANSLATE_MAX_LENGTH:
                batches.append((current_batch, current_size))
                current_batch = [text]
                current_size = text_size
            else:
                current_batch.append(text)
                current_size += text_size + (delimiter_size if current_batch else 0)
        
        if current_batch:
            batches.append((current_batch, current_size))
        
        # Translate each batch
        all_translated = []
        for batch_texts, _ in batches:
            try:
                # Join texts with delimiter
                combined_text = delimiter.join(batch_texts)
                
                # Translate combined text
                response = self.client.translate_text(
                    Text=combined_text,
                    SourceLanguageCode=source_language,
                    TargetLanguageCode=target_language
                )
                
                translated_combined = response.get('TranslatedText', '')
                
                # Split by delimiter to get individual translations
                translated_batch = translated_combined.split(delimiter)
                
                # Ensure we have the same number of translations as inputs
                while len(translated_batch) < len(batch_texts):
                    translated_batch.append("")
                
                all_translated.extend(translated_batch[:len(batch_texts)])
                
            except ClientError as e:
                error_msg = f"Translate batch ClientError: {str(e)}"
                logger.error(error_msg, exc_info=True)
                # Fallback: return empty translations for this batch
                all_translated.extend([""] * len(batch_texts))
            except Exception as e:
                error_msg = f"Error in batch translation: {str(e)}"
                logger.error(error_msg, exc_info=True)
                all_translated.extend([""] * len(batch_texts))
        
        # Map translations back to original indices
        translated_texts = [""] * len(texts)
        for i, idx in enumerate(indices):
            if i < len(all_translated):
                translated_texts[idx] = all_translated[i]
        
        return {"translated_texts": translated_texts}
    
    async def translate_batch(self, texts: List[str], target_language: str, source_language: str = 'auto') -> List[str]:
        """
        Translate multiple texts efficiently using batching.
        Reduces API calls by combining multiple texts into single Translate API calls.
        Returns list of translated texts in the same order as input.
        """
        if not texts:
            return []
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.executor,
            self._translate_batch_sync,
            texts,
            target_language,
            source_language
        )
        return result.get("translated_texts", [""] * len(texts))

