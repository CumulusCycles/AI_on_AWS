import boto3
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from botocore.exceptions import ClientError
from typing import Dict, Any
from pathlib import Path
import sys
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
from exceptions import PollyError
from config import POLLY_MAX_LENGTH, POLLY_AUDIO_SNIPPET_LENGTH, AUDIO_DIR

logger = logging.getLogger(__name__)


class PollyService:
    def __init__(self, region_name: str = "us-east-1"):
        self.client = boto3.client('polly', region_name=region_name)
        self.executor = ThreadPoolExecutor(max_workers=5)
    
    def _synthesize_speech_sync(self, text: str, voice_id: str) -> Dict[str, Any]:
        """Synthesize speech from text (sync)."""
        if not text or len(text.strip()) == 0:
            raise PollyError("Text is required for speech synthesis")
        
        # Polly has a 3000 character limit
        text_to_synthesize = text[:POLLY_MAX_LENGTH] if len(text) > POLLY_MAX_LENGTH else text
        
        try:
            response = self.client.synthesize_speech(
                Text=text_to_synthesize,
                OutputFormat='mp3',
                VoiceId=voice_id,
                Engine='neural'
            )
            
            # Save audio file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            audio_filename = f"audio_{timestamp}.mp3"
            audio_path = AUDIO_DIR / audio_filename
            
            with open(audio_path, 'wb') as f:
                f.write(response['AudioStream'].read())
            
            return {
                "audio_url": f"/static/audio/{audio_filename}",
                "text": text_to_synthesize,
                "voice_id": voice_id
            }
            
        except ClientError as e:
            error_msg = f"Polly ClientError: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise PollyError(error_msg) from e
        except Exception as e:
            error_msg = f"Error synthesizing speech: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise PollyError(error_msg) from e
    
    async def synthesize_speech(self, text: str, voice_id: str) -> Dict[str, Any]:
        """Synthesize speech from text (async)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._synthesize_speech_sync,
            text,
            voice_id
        )

