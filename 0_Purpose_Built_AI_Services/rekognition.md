![Amazon Rekognition](img/rekognition.png)

# Amazon Rekognition: Image & Video Analysis

Amazon Rekognition is a fully managed AWS service that enables image and video analysis using deep learning. It can detect objects, people, text, scenes, and activities, as well as recognize faces and inappropriate content. Common use cases include:

## Features
- Object and scene detection in images and videos
- Face detection, recognition, and comparison
- Unsafe content moderation (adult, violent, suggestive content)
- Text detection (OCR) in images and videos
- Custom labels for domain-specific object detection

## Use Cases
- Automated content moderation for social media platforms
- Identity verification and access control systems
- Media asset management and tagging
- Retail analytics (customer demographics, foot traffic)
- Security applications and surveillance

## Example
### Using AWS SDK (Python boto3) to analyze an image

```python
import boto3

client = boto3.client('rekognition')

with open('input.jpg', 'rb') as image_file:
    response = client.detect_labels(
        Image={'Bytes': image_file.read()},
        MaxLabels=10,
        MinConfidence=70.0
    )

for label in response['Labels']:
    print(f"Label: {label['Name']}, Confidence: {label['Confidence']:.2f}%")
```

For more details, see the [Amazon Rekognition documentation](https://docs.aws.amazon.com/rekognition/latest/dg/what-is.html).

[Back to menu](README.md)
