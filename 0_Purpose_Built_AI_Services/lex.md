![Amazon Lex](img/lex.png)

# Amazon Lex: Conversational AI & Chatbots

Amazon Lex is a service for building conversational interfaces into any application using voice and text.

## Features
- Natural language understanding (NLU) powered by deep learning
- Text and voice input support
- Multi-turn conversation management with intent recognition
- Built-in integration with AWS Lambda for fulfillment
- Integration with Amazon Connect for contact centers

## Use Cases
- Customer service chatbots and virtual assistants
- Voice-enabled applications and smart devices
- Automated help desks and support systems
- Order processing and e-commerce assistants
- Contact center automation

## Example
### Using AWS SDK (Python boto3) to interact with a Lex bot

```python
import boto3
import json

client = boto3.client('lex-runtime-v2')

# Text input to Lex bot
response = client.recognize_text(
    botId='YOUR_BOT_ID',
    botAliasId='YOUR_BOT_ALIAS_ID',
    localeId='en_US',
    sessionId='unique-session-id',
    text='I want to book a flight to New York'
)

# Process the response
intent = response['sessionState']['intent']['name']
slots = response['sessionState']['intent']['slots']
messages = response['messages']

print(f"Intent: {intent}")
print(f"Slots: {json.dumps(slots, indent=2)}")
for message in messages:
    print(f"Bot: {message['content']}")
```

[Back to menu](README.md)

