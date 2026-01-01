![Amazon Transcribe](img/transcribe.png)

# Amazon Transcribe: Speech-to-Text

Amazon Transcribe is an automatic speech recognition (ASR) service that makes it easy to add speech-to-text capabilities to applications.

## Features
- Real-time and batch transcription
- Speaker identification (speaker diarization)
- Custom vocabulary for domain-specific terms
- Automatic language detection
- Redaction of personally identifiable information (PII)

## Use Cases
- Transcribing customer service calls for analysis
- Captioning videos for accessibility and SEO
- Meeting transcription and documentation
- Medical dictation and clinical documentation
- Voice-driven analytics and business intelligence

## Example
### Using AWS SDK (Python boto3) to start a transcription job

```python
import boto3

client = boto3.client('transcribe')
job_name = 'example-job'
job_uri = 's3://your-bucket/input.wav'

response = client.start_transcription_job(
    TranscriptionJobName=job_name,
    Media={'MediaFileUri': job_uri},
    MediaFormat='wav',
    LanguageCode='en-US'
)
print('Transcription job started:', response['TranscriptionJob']['TranscriptionJobName'])
```

[Back to menu](README.md)
