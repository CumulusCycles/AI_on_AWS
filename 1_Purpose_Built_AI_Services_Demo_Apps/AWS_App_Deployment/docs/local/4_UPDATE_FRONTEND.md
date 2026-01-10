# Frontend API Integration Guide

This guide will help you connect the frontend application to the Preprocessing Lambda backend. This will enable the form to submit real data and display AI analysis results.

## Overview

We'll:
- Create an API client to communicate with the Preprocessing Lambda
- Update the App component to use real API calls
- Handle errors gracefully
- Display JSON response in the right panel
- Configure environment variables for API URL

## Prerequisites

- Frontend UI built (from `2_BUILD_FRONTEND_UI.md`)
- Preprocessing Lambda running locally (from `3_BUILD_PREPROCESSING_LAMBDA.md`)
- Preprocessing Lambda accessible at `http://localhost:8000`

## Step-by-Step Integration

### Step 1: Create Environment Variables File

Navigate to the frontend directory:

```bash
cd frontend
```

First, create `.env.example` (this file should be committed to git as a template):

```bash
# API endpoint for the Preprocessing Lambda
# For local development, point to the locally running Lambda
VITE_API_URL=http://localhost:8000
```

Then copy `.env.example` to `.env.local`:

```bash
cp .env.example .env.local
```

**Note:** Vite requires environment variables to be prefixed with `VITE_` to be accessible in the browser. The `.env.local` file is for your local development and should not be committed to git (it should be in `.gitignore`).

### Step 2: Create API Client

Create `src/lib/api.ts`:

```typescript
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface ProcessClaimResponse {
  claimId: string;
  timestamp: string;
  detected_language?: string;
  claim_description: {
    original_text: string;
    detected_language: string;
    language_score: number;
    comprehend: {
      detected_language: string;
      language_score: number;
      sentiment: {
        sentiment: string;
        scores: {
          Positive?: number;
          Negative?: number;
          Neutral?: number;
          Mixed?: number;
        };
      };
      entities: Array<{
        text: string;
        type: string;
        score: number;
      }>;
      key_phrases: Array<{
        text: string;
        score: number;
      }>;
    };
  };
  files: Array<{
    filename: string;
    file_type: string;
    s3_key: string;
    s3_url: string;
    rekognition: {
      labels: Array<{
        name: string;
        confidence: number;
        categories?: string[];
      }>;
      text_detections: Array<{
        text: string;
        confidence: number;
        type: string;
      }>;
    };
  }>;
  storage: {
    s3_bucket: string;
    s3_key: string;
    s3_url: string;
    dynamodb_table: string;
    dynamodb_item_id: string;
  };
  processing_status: {
    language_detection: string;
    claim_comprehend: string;
    image_rekognition: string;
    storage: string;
  };
  error?: string;
}

export async function processClaim(
  claimDescription: string,
  accidentPhoto: File
): Promise<ProcessClaimResponse> {
  const formData = new FormData();
  formData.append('claim_description', claimDescription);
  formData.append('accident_photo', accidentPhoto);

  const response = await fetch(`${API_URL}/process-claim`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(
      errorData.detail || `HTTP error! status: ${response.status}`
    );
  }

  return response.json();
}
```

**What this does:**
- Creates a FormData object with the claim description and photo
- Sends a POST request to the Preprocessing Lambda
- Handles errors and returns typed response data
- Uses environment variable for API URL

### Step 3: Update Types

Replace the entire contents of `src/types.ts` with the following code:

```typescript
export interface ClaimFormData {
  claim_description: string;
  accident_photo: File | undefined;
}
```

**Note:** The `accident_photo` field uses `File | undefined` to match the Zod schema validation.

```typescript
export interface ProcessingResult {
  claimId: string;
  timestamp: string;
  detected_language?: string;
  claim_description: {
    original_text: string;
    detected_language: string;
    language_score: number;
    comprehend: {
      detected_language: string;
      language_score: number;
      sentiment: {
        sentiment: string;
        scores: {
          Positive?: number;
          Negative?: number;
          Neutral?: number;
          Mixed?: number;
        };
      };
      entities: Array<{
        text: string;
        type: string;
        score: number;
      }>;
      key_phrases: Array<{
        text: string;
        score: number;
      }>;
    };
  };
  files: Array<{
    filename: string;
    file_type: string;
    s3_key: string;
    s3_url: string;
    rekognition: {
      labels: Array<{
        name: string;
        confidence: number;
        categories?: string[];
      }>;
      text_detections: Array<{
        text: string;
        confidence: number;
        type: string;
      }>;
    };
  }>;
  storage: {
    s3_bucket: string;
    s3_key: string;
    s3_url: string;
    dynamodb_table: string;
    dynamodb_item_id: string;
  };
  processing_status: {
    language_detection: string;
    claim_comprehend: string;
    image_rekognition: string;
    storage: string;
  };
  error?: string;
}
```

### Step 4: Update App.tsx

Replace the entire contents of `src/App.tsx` with the following code:

```typescript
import { useState } from 'react';
import type { ClaimFormData } from './lib/validation';
import { processClaim } from './lib/api';
import type { ProcessingResult } from './types';
import ClaimForm from './components/ClaimForm';

function App() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ProcessingResult | null>(null);

  const handleSubmit = async (data: ClaimFormData) => {
    if (!data.accident_photo) {
      setError('Accident photo is required');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await processClaim(data.claim_description, data.accident_photo);
      setResult(response as ProcessingResult);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred while processing your claim';
      setError(errorMessage);
      console.error('Error processing claim:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-full px-4 py-3">
          <h1 className="text-2xl font-bold text-gray-900">Claim Processor</h1>
        </div>
      </header>

      {/* Error Banner */}
      {error && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4 mx-4 mt-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <span className="text-red-500">⚠️</span>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
            <div className="ml-auto pl-3">
              <button
                onClick={() => setError(null)}
                className="text-red-500 hover:text-red-700"
                type="button"
              >
                ×
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main Content - Two Column Layout */}
      <div className="flex h-[calc(100vh-80px)]">
        {/* Left Column - Form */}
        <div className="flex-1 overflow-y-auto px-4 py-4" style={{ width: '70%' }}>
          <div className="max-w-4xl mx-auto space-y-6">
            {/* Form Section */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-bold mb-4">Submit Claim</h2>
              <ClaimForm
                onSubmit={handleSubmit}
                disabled={loading}
              />
            </div>
          </div>
        </div>

        {/* Right Column - JSON Data */}
        <div className="bg-gray-100 border-l border-gray-300 px-4 py-4" style={{ width: '30%' }}>
          {result ? (
            <div className="mt-4">
              <h3 className="font-semibold mb-2">JSON Response</h3>
              <pre className="text-xs bg-white p-3 rounded overflow-auto max-h-[calc(100vh-150px)]">
                {JSON.stringify(result, null, 2)}
              </pre>
            </div>
          ) : (
            <div className="text-gray-500 text-center mt-8">
              <p>Results will appear here after processing</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
```

**What this does:**
- Replaces placeholder code with real API call
- Handles errors gracefully
- Shows JSON response in the right column with complete results
- Maintains the two-column layout (form on left, JSON results on right)

### Step 5: Update .gitignore

Ensure `frontend/.gitignore` includes:

```gitignore
# Environment variables
.env.local
.env*.local
```

### Step 6: Test the Integration

1. **Start the Preprocessing Lambda** (if not already running):
   ```bash
   cd lambda/preprocessing
   python run_local.py
   ```

2. **Start the frontend** (if not already running):
   ```bash
   cd frontend
   npm run dev
   ```

3. **Test the flow:**
   - Open the frontend in your browser
   - Fill in the claim description
   - Upload an accident photo
   - Click "Submit Claim"
   - You should see:
     - Loading state while processing
     - Either a JSON response in the right column OR an error message (depending on backend configuration)

**What to expect:**

**If the backend is fully configured with AWS credentials and services:**
- ✅ Form submission works
- ✅ JSON response displays in the right column with complete results
- ✅ Results include:
  - `claimId` - Unique identifier for the claim
  - `claim_description` - Original text with Comprehend analysis
  - `files` - Array with image file info and Rekognition analysis
  - `storage` - S3 and DynamoDB storage information
  - `processing_status` - Status of each processing step

**If the backend is not fully configured (more likely at this stage):**
- ✅ Form submission works (frontend integration is complete)
- ✅ API call is made to the backend
- ⚠️ You may see an error message in the error banner if AWS services aren't configured
- ⚠️ The backend may return an error response that will be displayed in the right column
- **Note:** Full functionality requires AWS credentials, S3 buckets, DynamoDB tables, and proper IAM permissions to be configured. The frontend integration is complete and will work once the backend infrastructure is fully set up.
