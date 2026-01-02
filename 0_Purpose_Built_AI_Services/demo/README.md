# AWS Purpose-Built AI Services - Demo Notebook

This folder contains a Jupyter notebook with hands-on code examples demonstrating AWS Purpose-Built AI services. The notebook provides practical examples for integrating these services into your applications.

## Contents

- **`aws_ai_services_examples.ipynb`** - Interactive Jupyter notebook with code examples
- **`requirements.txt`** - Python dependencies for the notebook
- **`assets/`** - Sample files used in the examples (audio and image files)

## AWS Services Demonstrated

The notebook includes examples for the following AWS AI services:

1. **Amazon Transcribe** - Speech-to-text transcription from audio files
2. **Amazon Polly** - Text-to-speech synthesis
3. **Amazon Translate** - Language translation between different languages
4. **Amazon Comprehend** - Natural language processing (sentiment analysis, entity detection)
5. **Amazon Rekognition** - Image and video analysis (label detection, object recognition)

## Prerequisites

Before running the notebook, ensure you have:

- **Python 3.8+** - Required for running the notebook
- **uv** - Fast Python package installer and resolver ([Install uv](https://github.com/astral-sh/uv))
- **AWS Account** - With appropriate IAM credentials and permissions
- **AWS Credentials** - Configured via `.env` file, `aws configure`, or environment variables

## Setup Instructions

### 1. Create and Activate Virtual Environment

Create a virtual environment using `uv` (if it doesn't already exist):

```bash
uv venv
```

Activate the virtual environment:

```bash
source .venv/bin/activate
```

**Note:** If you use `uv run` for subsequent commands (like launching Jupyter Lab), you don't need to activate the venv manually as `uv run` automatically uses it.

### 2. Install Dependencies

Install all required packages using `uv`:

```bash
uv pip install -r requirements.txt
```

### 3. Configure AWS Credentials

You can configure AWS credentials in one of three ways:

**Option A: Using a `.env` file (Recommended)**

Create a `.env` file in this directory with your AWS credentials:

```bash
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
AWS_DEFAULT_REGION=us-east-1
```

**Option B: Using AWS CLI**

```bash
aws configure
```

**Option C: Using Environment Variables**

```bash
export AWS_ACCESS_KEY_ID=your_access_key_id
export AWS_SECRET_ACCESS_KEY=your_secret_access_key
export AWS_DEFAULT_REGION=us-east-1
```

### 4. Register Jupyter Kernel

Register the virtual environment as a Jupyter kernel so Jupyter Lab can use it:

```bash
uv run python -m ipykernel install --user --name=aws-ai-services --display-name "Python (AWS AI Services)"
```

**Note:** This only needs to be done once. It registers the venv kernel so you can select it in Jupyter Lab.

### 5. Launch Jupyter Lab

Start Jupyter Lab using `uv run`. This automatically uses the virtual environment:

```bash
uv run jupyter lab
```

**Important:** When Jupyter Lab opens, select the "Python (AWS AI Services)" kernel from the kernel selector in the top right corner of the notebook.

## Using the Notebook

1. Open `aws_ai_services_examples.ipynb` in Jupyter Lab
2. Select the "Python (AWS AI Services)" kernel
3. Run cells sequentially to see each service in action
4. Modify the code examples to experiment with different inputs and configurations

## Additional Configuration

Some examples in the notebook use environment variables for configuration. You can set these in your `.env` file:

- `S3_BUCKET` - S3 bucket name for Transcribe input files
- `TRANSCRIBE_S3_KEY` - S3 key for the audio file to transcribe
- `TRANSCRIBE_MEDIA_FORMAT` - Media format (mp3, wav, etc.) - auto-detected if not specified
- `TRANSCRIBE_OUTPUT_BUCKET` - S3 bucket for transcription output (defaults to input bucket)
- `TRANSCRIBE_OUTPUT_KEY` - S3 key for transcription output JSON file

## Notes

- The notebook supports loading configuration from a `.env` file using `python-dotenv`
- Credentials are loaded in this priority order: `.env` file > environment variables > `~/.aws/credentials` > IAM role
- Some examples (like Transcribe) require files to be uploaded to S3 first
- Make sure you have the necessary IAM permissions for each AWS service you want to use

## Related Documentation

For detailed information about each AWS AI service, see the documentation in the parent directory:

- [Introduction to AI on AWS](../intro-to-ai-on-aws.md)
- [Amazon Transcribe](../transcribe.md)
- [Amazon Polly](../polly.md)
- [Amazon Translate](../translate.md)
- [Amazon Comprehend](../comprehend.md)
- [Amazon Rekognition](../rekognition.md)
- [Amazon Textract](../textract.md)
- [Amazon Lex](../lex.md)

