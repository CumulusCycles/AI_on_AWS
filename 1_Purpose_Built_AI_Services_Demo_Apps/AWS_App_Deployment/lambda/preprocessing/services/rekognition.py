import logging
from config import rekognition_client, logger

def analyze_image_with_rekognition(image_bytes: bytes) -> dict:
    """
    Analyze image with Amazon Rekognition.
    Returns labels and text detections.
    """
    try:
        # Detect labels
        labels_response = rekognition_client.detect_labels(
            Image={'Bytes': image_bytes},
            MaxLabels=10,
            MinConfidence=70
        )
        
        # Detect text
        text_response = rekognition_client.detect_text(
            Image={'Bytes': image_bytes}
        )
        
        return {
            "labels": [
                {
                    "name": label['Name'],
                    "confidence": label['Confidence'],
                    "categories": [cat['Name'] for cat in label.get('Categories', [])]
                }
                for label in labels_response['Labels']
            ],
            "text_detections": [
                {
                    "text": detection['DetectedText'],
                    "confidence": detection['Confidence'],
                    "type": detection['Type']
                }
                for detection in text_response['TextDetections']
            ]
        }
    except Exception as e:
        logger.error(f"Error in Rekognition analysis: {str(e)}", exc_info=True)
        raise