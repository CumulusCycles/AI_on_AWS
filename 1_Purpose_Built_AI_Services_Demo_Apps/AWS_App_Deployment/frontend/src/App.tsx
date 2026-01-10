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