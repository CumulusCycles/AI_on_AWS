# Claim Processor

A full-stack application that demonstrates AWS Purpose-built AI Services for processing insurance claims. The app processes claim descriptions and documents using Textract, Comprehend, Rekognition, Translate, and Polly.

## Features

- **Multi-language Support**: Auto-detects language from user input and translates all results
- **Structured Form**: Separate sections for accident photo and insurance forms
- **Document Processing**: Handles PDFs and images (PNG, JPG, JPEG, GIF, BMP)
- **Text Extraction**: Extracts text, forms, and tables from documents
- **Image Analysis**: Detects labels and text in images with visual overlay
- **Visual Label Overlay**: Accident photos display with Rekognition labels and bounding boxes
- **NLP Analysis**: Extracts entities, key phrases, and sentiment
- **Audio Generation**: Converts user-provided text to speech in the user's language
- **Optimized Service Calls**: Intelligent service selection reduces API calls from 50-80+ to 17-25 per submission
- **Two-Column Layout**: User-readable results on left, JSON data on right

## Tech Stack

### Backend
- FastAPI (Python)
- uv (Python package manager)
- boto3 (AWS SDK)
- Pydantic (validation)

### Frontend
- Vite + React + TypeScript
- Tailwind CSS
- React Hook Form + Zod (form validation)
- react-json-view (JSON display)

## AWS Services Used

1. **Comprehend** - Language detection and NLP analysis
2. **Textract** - Document text extraction
3. **Rekognition** - Image analysis (labels, text detection)
4. **Translate** - Text translation
5. **Polly** - Text-to-speech

## Setup

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (fast Python package installer)
- Node.js 18+
- AWS credentials with access to the AI services
- npm or yarn

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment using uv:
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
uv pip install -r requirements.txt
```

4. Create a `.env` file in the Insurance_Claim_Submission directory (copy from `.env.example` if it exists):
```bash
cp .env.example .env
```

5. Edit `.env` and add your AWS credentials:
```
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
```

6. Start the backend server:
```bash
python main.py
```

The backend will run on `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The frontend will run on `http://localhost:3000`

## Usage

1. Open `http://localhost:3000` in your browser
2. Enter a claim description in the textarea (supports multiple languages)
3. Upload an accident photo (image file: PNG, JPG, JPEG, GIF, or BMP)
4. Upload one or more insurance forms (PDF or PNG files)
5. Click "Submit Claim"
6. View results:
   - **Left column**: User-readable results with extracted information
     - Accident photo displayed with Rekognition labels overlaid
     - Extracted text and analysis from insurance forms
   - **Right column**: Complete JSON response data (collapsible sections)
7. Button will change to "Claim Processed" and be disabled after successful submission

## Project Structure

```
.
├── backend/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration
│   ├── dependencies.py      # Dependency injection
│   ├── exceptions.py        # Custom exceptions
│   ├── models/              # Pydantic models
│   ├── services/            # AWS service wrappers
│   └── static/audio/       # Generated audio files
├── frontend/
│   ├── src/
│   │   ├── App.tsx          # Main application component
│   │   ├── components/      # React components
│   │   ├── lib/             # Utilities (API, validation)
│   │   └── types.ts         # TypeScript types
│   └── package.json
└── assets/                  # Demo files (not used by app)
```

## API Endpoints

### POST /process-claim

Processes a claim with description text, accident photo, and insurance forms.

**Request:**
- `claim_description` (form data): Text description
- `accident_photo` (file): Single image file (PNG, JPG, JPEG, GIF, BMP)
- `insurance_forms` (form data): One or more files (PDF or PNG)

**Response:**
- `detected_language`: Detected language code
- `claim_description`: Analysis results for the claim text
- `files`: Array of file processing results (accident photo first, then insurance forms)
- `processing_status`: Status of each processing step

## Notes

- The app auto-detects the language from the user's text input
- All results are translated to the user's language (using batch translation for efficiency)
- Audio is generated only for user-provided text (not for extracted text from files)
- Files are processed with optimized service selection:
  - **Accident Photo**: Rekognition (visual analysis) - Textract is skipped
  - **Insurance Forms**: Textract (text extraction) + Comprehend (if text extracted) - Rekognition is skipped
- This optimization reduces API calls from 50-80+ to 17-25 per submission
- Processing continues even if individual services fail (partial results)
- Accident photos display with visual overlay showing Rekognition labels and bounding boxes

## License

MIT

