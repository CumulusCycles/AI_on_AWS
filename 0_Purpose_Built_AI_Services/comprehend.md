![Amazon Comprehend](img/comprehend.png)

# Amazon Comprehend: Natural Language Processing

Amazon Comprehend is a natural language processing (NLP) service that uses machine learning to find insights and relationships in text.

## Features
- Entity recognition (people, places, organizations, dates, etc.)
- Sentiment analysis (positive, negative, neutral, mixed)
- Key phrase extraction from documents
- PII (Personally Identifiable Information) detection and redaction
- Custom entity recognition and classification models

## Use Cases
- Analyzing customer feedback and reviews
- Automating content moderation for user-generated content
- Social media monitoring and sentiment tracking
- Customer support ticket routing and prioritization
- Extracting insights from documents and reports

## Example
### Using AWS SDK (Python boto3) to analyze sentiment and entities

```python
import boto3

client = boto3.client('comprehend')
text = "AWS makes cloud AI easy."

# Detect sentiment
sentiment = client.detect_sentiment(Text=text, LanguageCode='en')
print('Sentiment:', sentiment['Sentiment'])
print('Sentiment Scores:', sentiment['SentimentScore'])

# Detect entities
entities = client.detect_entities(Text=text, LanguageCode='en')
print('\nEntities found:')
for entity in entities['Entities']:
    print(f"  Entity: {entity['Text']}, Type: {entity['Type']}, Confidence: {entity['Score']:.2f}")
```

[Back to menu](README.md)
