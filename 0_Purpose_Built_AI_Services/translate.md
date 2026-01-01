![Amazon Translate](img/translate.png)

# Amazon Translate: Language Translation

Amazon Translate is a neural machine translation service for translating text between languages.

## Features
- Neural machine translation for high-quality translations
- Real-time translation API for interactive applications
- Support for 75+ languages and language variants
- Automatic language detection
- Custom terminology support for domain-specific translations

## Use Cases
- Translating website content for international audiences
- Real-time chat and messaging translation
- Localizing mobile applications
- E-commerce product description translation
- Translating customer support communications

## Example
### Using AWS SDK (Python boto3) to translate text

```python
import boto3

client = boto3.client('translate')
text = "Hello, world!"

response = client.translate_text(
    Text=text,
    SourceLanguageCode='en',
    TargetLanguageCode='es'
)

print(f"Original text: {text}")
print(f"Translated text: {response['TranslatedText']}")
```

[Back to menu](README.md)
