import boto3
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from botocore.exceptions import ClientError
from typing import Dict, Any
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from exceptions import RekognitionError

logger = logging.getLogger(__name__)


class RekognitionService:
    def __init__(self, region_name: str = "us-east-1"):
        self.client = boto3.client('rekognition', region_name=region_name)
        self.executor = ThreadPoolExecutor(max_workers=5)
    
    def _analyze_image_sync(self, image_bytes: bytes) -> Dict[str, Any]:
        """Analyze image using Rekognition (sync)."""
        try:
            # Detect labels
            labels_response = self.client.detect_labels(
                Image={'Bytes': image_bytes},
                MaxLabels=10,
                MinConfidence=70.0
            )
            
            # Detect text
            text_response = self.client.detect_text(
                Image={'Bytes': image_bytes}
            )
            
            # Extract labels with bounding boxes
            labels_with_boxes = []
            for label in labels_response.get('Labels', []):
                label_data = {
                    "name": label.get('Name', ''),
                    "confidence": label.get('Confidence', 0),
                    "categories": [
                        cat.get('Name', '') 
                        for cat in label.get('Categories', [])
                    ],
                    "instances": []
                }
                # Extract bounding boxes from instances
                for instance in label.get('Instances', []):
                    bbox = instance.get('BoundingBox', {})
                    label_data["instances"].append({
                        "bounding_box": {
                            "width": bbox.get('Width', 0),
                            "height": bbox.get('Height', 0),
                            "left": bbox.get('Left', 0),
                            "top": bbox.get('Top', 0)
                        },
                        "confidence": instance.get('Confidence', 0)
                    })
                labels_with_boxes.append(label_data)
            
            return {
                "labels": labels_with_boxes,
                "text_detections": [
                    {
                        "text": detection.get('DetectedText', ''),
                        "confidence": detection.get('Confidence', 0),
                        "type": detection.get('Type', '')
                    }
                    for detection in text_response.get('TextDetections', [])
                    if detection.get('Type') == 'LINE'
                ]
            }
            
        except ClientError as e:
            error_msg = f"Rekognition ClientError: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise RekognitionError(error_msg) from e
        except Exception as e:
            error_msg = f"Error analyzing image: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise RekognitionError(error_msg) from e
    
    async def analyze_image(self, image_bytes: bytes) -> Dict[str, Any]:
        """Analyze image using Rekognition (async)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._analyze_image_sync,
            image_bytes
        )

