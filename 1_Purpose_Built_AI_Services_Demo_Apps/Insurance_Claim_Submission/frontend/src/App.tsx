import { useState } from 'react';
import { ClaimFormData } from './lib/validation';
import { processClaim as apiProcessClaim } from './lib/api';
import { ProcessingResult } from './types';
import ClaimForm from './components/ClaimForm';
import UserReadableResults from './components/UserReadableResults';
import JsonDataPanel from './components/JsonDataPanel';

function App() {
  const [result, setResult] = useState<ProcessingResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [processingStatus, setProcessingStatus] = useState<Record<string, string>>({});
  const [accidentPhoto, setAccidentPhoto] = useState<File | null>(null);

  const handleSubmit = async (data: ClaimFormData) => {
    setLoading(true);
    setError(null);
    setResult(null);
    setProcessingStatus({});
    setAccidentPhoto(data.accident_photo); // Store accident photo for display

    try {
      // Simulate processing status updates
      setProcessingStatus({
        language_detection: 'processing',
        claim_comprehend: 'processing',
      });

      const response = await apiProcessClaim(data.claim_description, data.accident_photo, data.insurance_forms);
      
      setResult(response);
      setProcessingStatus(response.processing_status || {});
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
              >
                ×
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main Content - Two Column Layout */}
      <div className="flex h-[calc(100vh-80px)]">
        {/* Left Column - Form and Results */}
        <div className="flex-1 overflow-y-auto px-4 py-4" style={{ width: '70%' }}>
          <div className="max-w-4xl mx-auto space-y-6">
            {/* Form Section */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-bold mb-4">Submit Claim</h2>
              <ClaimForm
                onSubmit={handleSubmit}
                disabled={loading}
                processingStatus={processingStatus}
                isProcessed={!!result}
              />
            </div>

            {/* User Readable Results */}
            {result && (
              <div className="bg-white rounded-lg shadow p-6">
                <UserReadableResults result={result} accidentPhoto={accidentPhoto} />
              </div>
            )}
          </div>
        </div>

        {/* Right Column - JSON Data */}
        <div className="bg-gray-100 border-l border-gray-300 px-4 py-4" style={{ width: '30%' }}>
          {result ? (
            <JsonDataPanel result={result} />
          ) : (
            <div className="text-gray-500 text-center mt-8">
              <p>JSON data will appear here after processing</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;

