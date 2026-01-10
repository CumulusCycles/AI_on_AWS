import logging
from config import comprehend_client, logger

def analyze_text_with_comprehend(text: str) -> dict:
    """
    Analyze text with Amazon Comprehend.
    Returns sentiment, entities, and key phrases.
    """
    try:
        # Detect dominant language
        lang_response = comprehend_client.detect_dominant_language(Text=text)
        detected_language = lang_response['Languages'][0]['LanguageCode']
        language_score = lang_response['Languages'][0]['Score']
        
        # Detect sentiment
        sentiment_response = comprehend_client.detect_sentiment(
            Text=text,
            LanguageCode=detected_language
        )
        
        # Detect entities
        entities_response = comprehend_client.detect_entities(
            Text=text,
            LanguageCode=detected_language
        )
        
        # Extract key phrases
        key_phrases_response = comprehend_client.detect_key_phrases(
            Text=text,
            LanguageCode=detected_language
        )
        
        return {
            "detected_language": detected_language,
            "language_score": language_score,
            "sentiment": {
                "sentiment": sentiment_response['Sentiment'],
                "scores": sentiment_response['SentimentScore']
            },
            "entities": [
                {
                    "text": entity['Text'],
                    "type": entity['Type'],
                    "score": entity['Score']
                }
                for entity in entities_response['Entities']
            ],
            "key_phrases": [
                {
                    "text": phrase['Text'],
                    "score": phrase['Score']
                }
                for phrase in key_phrases_response['KeyPhrases']
            ]
        }
    except Exception as e:
        logger.error(f"Error in Comprehend analysis: {str(e)}", exc_info=True)
        raise