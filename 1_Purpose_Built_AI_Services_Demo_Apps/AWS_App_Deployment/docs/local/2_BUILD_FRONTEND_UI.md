# Frontend UI Build Guide

This guide will help you build out the UI components and layout for the claim submission form. This focuses on look-and-feel only - no backend API calls will be implemented yet.

## Overview

We'll build:
- A two-column layout (form on left, placeholder for results on right)
- A form with 2 fields: Claim Description (textarea) and Accident Photo (file upload with drag-and-drop)
- Proper validation and error handling
- Clean, modern UI matching the reference app's design

## Step-by-Step Build

### Step 1: Create Directory Structure

Create the necessary directories for organizing your code:

```bash
cd frontend
mkdir -p src/components src/lib
```

### Step 2: Create Type Definitions

Create `src/types.ts` with basic type definitions:

```typescript
export interface ClaimFormData {
  claim_description: string;
  accident_photo: File | undefined;
}
```

**Note:** The `accident_photo` field uses `File | undefined` to match the Zod schema validation.

### Step 3: Create Validation Schema

Create `src/lib/validation.ts` with Zod validation schemas:

```typescript
import { z } from 'zod';

export const claimFormSchema = z
  .object({
    claim_description: z
      .string()
      .min(10, 'Claim description must be at least 10 characters')
      .max(2500, 'Claim description must not exceed 2500 characters'),
    accident_photo: z.instanceof(File).optional(),
  })
  .refine(
    (data) => data.accident_photo !== undefined,
    {
      message: 'Please upload an accident photo',
      path: ['accident_photo'],
    }
  )
  .refine(
    (data) => {
      if (!data.accident_photo) return true;
      return data.accident_photo.size <= 5 * 1024 * 1024;
    },
    {
      message: 'File must be less than 5MB',
      path: ['accident_photo'],
    }
  )
  .refine(
    (data) => {
      if (!data.accident_photo) return true;
      const ext = '.' + data.accident_photo.name.split('.').pop()?.toLowerCase();
      return ['.png', '.jpg', '.jpeg', '.gif', '.bmp'].includes(ext);
    },
    {
      message: 'Accident photo must be an image file (PNG, JPG, JPEG, GIF, or BMP)',
      path: ['accident_photo'],
    }
  );

type ClaimFormData = z.infer<typeof claimFormSchema>;
export type { ClaimFormData };
```

**What this does:**
- Validates claim description length (10-2500 characters)
- Validates file size (max 5MB)
- Validates file type (image formats only)

### Step 4: Create SingleFileUpload Component

Create `src/components/SingleFileUpload.tsx`:

```typescript
import { useRef, useState, useCallback } from 'react';

interface SingleFileUploadProps {
  file: File | null | undefined;
  onFileChange: (file: File | null) => void;
  disabled?: boolean;
  error?: string;
  accept?: string;
  label?: string;
}

export default function SingleFileUpload({ 
  file, 
  onFileChange, 
  disabled, 
  error,
  accept = '.png,.jpg,.jpeg,.gif,.bmp',
  label = 'Drag and drop a file here, or click to select'
}: SingleFileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled) {
      setIsDragging(true);
    }
  }, [disabled]);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (disabled) return;

    const droppedFiles = Array.from(e.dataTransfer.files);
    if (droppedFiles.length > 0) {
      onFileChange(droppedFiles[0]);
    }
  }, [onFileChange, disabled]);

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      onFileChange(e.target.files[0]);
    }
  };

  const removeFile = () => {
    onFileChange(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const getFileThumbnail = (file: File): string | null => {
    if (file.type.startsWith('image/')) {
      return URL.createObjectURL(file);
    }
    return null;
  };

  return (
    <div className="space-y-2">
      <div
        onDragEnter={handleDragEnter}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
          isDragging
            ? 'border-blue-500 bg-blue-50'
            : disabled
            ? 'border-gray-300 bg-gray-50'
            : 'border-gray-400 hover:border-gray-500 cursor-pointer'
        }`}
        onClick={() => !disabled && fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={accept}
          onChange={handleFileInputChange}
          disabled={disabled}
          className="hidden"
        />
        <p className="text-gray-600">
          {isDragging ? 'Drop file here' : label}
        </p>
        <p className="text-sm text-gray-500 mt-1">
          Max 5MB
        </p>
      </div>

      {error && (
        <p className="text-red-600 text-sm">{error}</p>
      )}

      {file && (
        <div className="border border-gray-300 rounded p-3 flex items-center space-x-3">
          {getFileThumbnail(file) ? (
            <img
              src={getFileThumbnail(file)!}
              alt={file.name}
              className="w-16 h-16 object-cover rounded"
            />
          ) : (
            <div className="w-16 h-16 bg-gray-200 rounded flex items-center justify-center">
              <span className="text-xs">File</span>
            </div>
          )}
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">{file.name}</p>
            <p className="text-xs text-gray-500">
              {(file.size / 1024 / 1024).toFixed(2)} MB
            </p>
          </div>
          {!disabled && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                removeFile();
              }}
              className="text-red-600 hover:text-red-800 text-xl font-bold"
              type="button"
            >
              ×
            </button>
          )}
        </div>
      )}
    </div>
  );
}
```

**What this component does:**
- Provides drag-and-drop file upload functionality
- Shows file preview thumbnail for images
- Displays file name and size
- Allows file removal
- Handles disabled state

### Step 5: Create ClaimForm Component

Create `src/components/ClaimForm.tsx`:

```typescript
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { claimFormSchema } from '../lib/validation';
import type { ClaimFormData } from '../lib/validation';
import SingleFileUpload from './SingleFileUpload';

interface ClaimFormProps {
  onSubmit: (data: ClaimFormData) => void;
  disabled?: boolean;
}

export default function ClaimForm({ onSubmit, disabled }: ClaimFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
    watch,
  } = useForm<ClaimFormData>({
    resolver: zodResolver(claimFormSchema),
    defaultValues: {
      claim_description: '',
      accident_photo: undefined,
    },
  });

  const accidentPhoto = watch('accident_photo');
  const claimDescription = watch('claim_description');

  const handleAccidentPhotoChange = (file: File | null) => {
    setValue('accident_photo', file || undefined, { shouldValidate: true });
  };

  const onFormSubmit = (data: ClaimFormData) => {
    onSubmit(data);
  };

  return (
    <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-6">
      <div>
        <label htmlFor="claim_description" className="block text-sm font-medium text-gray-700 mb-1">
          Description of Claim *
        </label>
        <textarea
          {...register('claim_description')}
          id="claim_description"
          rows={10}
          disabled={disabled}
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
          placeholder="Enter your claim description here..."
        />
        {errors.claim_description && (
          <p className="mt-1 text-sm text-red-600">{errors.claim_description.message}</p>
        )}
        <p className="mt-1 text-xs text-gray-500">
          {claimDescription?.length || 0} / 2500 characters
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Accident Photo *
        </label>
        <SingleFileUpload
          file={accidentPhoto}
          onFileChange={handleAccidentPhotoChange}
          disabled={disabled}
          error={errors.accident_photo?.message}
          accept=".png,.jpg,.jpeg,.gif,.bmp"
          label="Drag and drop accident photo here, or click to select"
        />
      </div>

      <button
        type="submit"
        disabled={disabled}
        className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
      >
        {disabled ? 'Processing...' : 'Submit Claim'}
      </button>
    </form>
  );
}
```

**What this component does:**
- Integrates react-hook-form with Zod validation
- Displays form fields with proper labels
- Shows character count for textarea
- Handles form submission
- Displays validation errors

### Step 6: Update App.tsx

Replace the entire contents of `src/App.tsx` with the following code. This will replace the default Vite template code:

```typescript
import { useState } from 'react';
import type { ClaimFormData } from './lib/validation';
import ClaimForm from './components/ClaimForm';

function App() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (data: ClaimFormData) => {
    setLoading(true);
    setError(null);

    try {
      // TODO: Add API call here in future step
      console.log('Form submitted:', data);
      
      // Simulate processing delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      alert('Form submitted successfully! (Backend integration coming soon)');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred';
      setError(errorMessage);
      console.error('Error submitting claim:', err);
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

        {/* Right Column - Placeholder for Results */}
        <div className="bg-gray-100 border-l border-gray-300 px-4 py-4" style={{ width: '30%' }}>
          <div className="text-gray-500 text-center mt-8">
            <p>Results will appear here after processing</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
```

**What this does:**
- Creates the two-column layout (70% left, 30% right)
- Adds header with app title
- Includes error banner that can be dismissed
- Integrates the ClaimForm component
- Provides placeholder for future results display
- Handles form submission (currently just logs to console)

### Step 7: Test the Application

Start the development server and test the form:

```bash
npm run dev
```
The app will start and Vite will display the local URL (typically `http://localhost:5173`). Open this URL in your browser to view the application.

**What you should see:**

1. **Header**: A white header bar at the top with "Claim Processor" title
2. **Two-column layout**:
   - **Left column (70% width)**: White card with "Submit Claim" heading containing:
     - "Description of Claim *" textarea with placeholder text
     - Character counter showing "0 / 2500 characters"
     - "Accident Photo *" section with drag-and-drop area
     - "Submit Claim" button (blue, full width)
   - **Right column (30% width)**: Gray background with centered text "Results will appear here after processing"
3. **Form functionality**:
   - Textarea accepts text input and character count updates
   - File upload area responds to hover (border changes)
   - Drag-and-drop works for image files
   - Click-to-select works for file upload
   - Form validation shows errors for invalid input
4. **Styling**: Clean, modern UI with Tailwind CSS styling matching the reference app

**To stop the server:**
Press `Ctrl+C` (or `Cmd+C` on Mac) in the terminal where the server is running.