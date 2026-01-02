# Purpose-Built AI Services Demo Apps

This folder contains full-stack demonstration applications that showcase AWS Purpose-Built AI Services in real-world scenarios. Each app demonstrates different combinations of AWS AI services and use cases.

## Demo Applications

### [Multilingual Chat](./Multilingual_Chat/)

A real-time multilingual chat application that enables three users to communicate in different languages (English, Spanish, French) with automatic translation and sentiment analysis.

**Key Features:**
- Real-time WebSocket-based communication
- Automatic message translation
- Sentiment analysis with color-coded messages
- Parallel processing for minimal latency

**AWS Services Used:** Translate, Comprehend

**Tech Stack:** FastAPI (Python) with WebSockets + React + TypeScript

See the [Multilingual Chat README](./Multilingual_Chat/README.md) for detailed setup and usage instructions.

---

### [Insurance Claim Submission](./Insurance_Claim_Submission/)

A comprehensive insurance claim processing application that demonstrates document processing, image analysis, and natural language understanding. The app processes claim descriptions, accident photos, and insurance forms using multiple AWS AI services.

**Key Features:**
- Multi-language support with automatic translation
- Document text extraction (PDFs and images)
- Image analysis with visual label overlay
- NLP analysis (entities, sentiment, key phrases)
- Text-to-speech generation
- Optimized service calls for efficiency

**AWS Services Used:** Textract, Comprehend, Rekognition, Translate, Polly

**Tech Stack:** FastAPI (Python) + React + TypeScript

See the [Insurance Claim Submission README](./Insurance_Claim_Submission/README.md) for detailed setup and usage instructions.

---

## Getting Started

Each demo app includes:
- **README.md** - Comprehensive documentation, features, and setup instructions
- **QUICKSTART.md** - Quick start guide for getting up and running
- **Backend** - FastAPI Python application
- **Frontend** - React + TypeScript application

Both apps use:
- **uv** - Fast Python package installer for backend dependencies
- **npm** - Node package manager for frontend dependencies
- **.env** files - For AWS credentials and configuration

## Prerequisites

- Python 3.8+ and **uv** (for backend)
- Node.js and npm (for frontend)
- AWS Account with appropriate IAM permissions
- AWS Credentials configured
