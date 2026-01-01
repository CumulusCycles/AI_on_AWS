# Quick Start Guide

## Prerequisites

1. Python 3.11+ installed
2. [uv](https://github.com/astral-sh/uv) installed (fast Python package installer)
3. Node.js 18+ installed
4. AWS credentials configured (access key and secret key)
5. AWS services enabled: Textract, Comprehend, Rekognition, Translate, Polly
6. An S3 bucket for temporary PDF storage (required for PDF processing with Textract)

## Setup Steps

### 1. Configure AWS Credentials

Create a `.env` file in the Insurance_Claim_Submission directory:

```bash
cp .env.example .env
```

Edit `.env` and add your AWS credentials:
```
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
TEXTRACT_S3_BUCKET=your-s3-bucket-name
```

**Note:** The `TEXTRACT_S3_BUCKET` is required for PDF processing. Create an S3 bucket in your AWS account and ensure your AWS credentials have permissions to:
- `s3:PutObject` (to upload PDFs temporarily)
- `s3:DeleteObject` (to clean up after processing)
- `textract:StartDocumentAnalysis` (to start PDF analysis)
- `textract:GetDocumentAnalysis` (to retrieve results)

### 2. Start Backend

```bash
cd backend
uv venv --python=python3.12
source .venv/bin/activate
uv pip install -r requirements.txt -q
python main.py
```

Backend will run on `http://localhost:8000`

### 3. Start Frontend (in a new terminal)

```bash
cd frontend
npm install
npm run dev
```

Frontend will run on `http://localhost:3000`

### 4. Use the App

1. Open `http://localhost:3000` in your browser
2. Enter a claim description (supports multiple languages)
3. Upload an accident photo (image file: PNG, JPG, JPEG, GIF, or BMP)
4. Upload insurance forms (PDF or PNG files - can upload multiple)
5. Click "Submit Claim"
6. View results in the two-column layout:
   - Accident photo will display with Rekognition labels overlaid
   - Extracted text and analysis from insurance forms
   - Button will change to "Claim Processed" and be disabled after successful submission

## Testing with Demo Files

You can use the files in the `assets/` folder for testing:
- **Accident Photo**: `Accident_Pic.png` (upload in the "Accident Photo" section)
- **Insurance Forms**: 
  - `Insurance_Claim_Packet.pdf` (upload in the "Insurance Forms" section)
  - `Insureance_Intake_Form_Scan.png` (upload in the "Insurance Forms" section)
  - `Repair_Invoice.pdf` (upload in the "Insurance Forms" section)

**Note:** The app is optimized to use different AWS services for different file types:
- **Accident Photo**: Uses Rekognition for visual analysis (objects, scenes, labels). Textract is skipped.
- **Insurance Forms**: Uses Textract for text extraction. Rekognition is skipped.
- This optimization reduces API calls from 50-80+ to 17-25 per submission.

## Troubleshooting

### Backend won't start
- Check that Python 3.11+ is installed
- Verify `uv` is installed: `uv --version`
- Verify `.env` file exists and has correct AWS credentials
- Ensure all dependencies are installed: `uv pip install -r requirements.txt`

### Frontend won't start
- Check that Node.js 18+ is installed
- Run `npm install` to install dependencies
- Check that port 3000 is not in use

### AWS Service Errors
- Verify AWS credentials are correct
- Check that AWS services are enabled in your AWS account
- Ensure your AWS region supports all services (us-east-1 recommended)
- For PDF processing errors: Verify `TEXTRACT_S3_BUCKET` is set in `.env` and the bucket exists
- Ensure your AWS credentials have S3 and Textract permissions (see setup section above)

### CORS Errors
- Make sure backend is running on port 8000
- Check that `FRONTEND_URL` in `.env` matches your frontend URL

