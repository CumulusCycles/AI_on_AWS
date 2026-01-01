import { ProcessingResult } from '../types';
import { getAudioUrl } from '../lib/api';
import ImageWithLabels from './ImageWithLabels';

interface UserReadableResultsProps {
  result: ProcessingResult;
  accidentPhoto: File | null;
}

export default function UserReadableResults({ result, accidentPhoto }: UserReadableResultsProps) {
  const { claim_description, files, detected_language } = result;
  
  // Use translated results if available, otherwise use original
  const claimComprehend = claim_description.translated_comprehend || claim_description.comprehend;
  const userLanguage = detected_language;

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Results</h2>

      {/* Claim Description Section */}
      <div className="border border-gray-300 rounded-lg p-4">
        <h3 className="text-xl font-semibold mb-3">📝 Claim Description</h3>
        <div className="mb-4">
          <p className="text-sm text-gray-600 mb-2">
            Detected Language: <span className="font-semibold">{userLanguage.toUpperCase()}</span>
          </p>
          <div className="bg-gray-50 p-3 rounded border">
            <p className="whitespace-pre-wrap">{claim_description.original_text}</p>
          </div>
        </div>

        {/* Key Information */}
        {claimComprehend.entities.length > 0 && (
          <div className="mb-4">
            <h4 className="font-semibold mb-2">Key Information Extracted:</h4>
            <div className="grid grid-cols-2 gap-2">
              {claimComprehend.entities.map((entity, idx) => (
                <div key={idx} className="text-sm">
                  <span className="font-medium">{entity.type}:</span>{' '}
                  <span>{entity.translated_text || entity.text}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Key Phrases */}
        {claimComprehend.key_phrases.length > 0 && (
          <div className="mb-4">
            <h4 className="font-semibold mb-2">Key Phrases:</h4>
            <div className="flex flex-wrap gap-2">
              {claimComprehend.key_phrases.map((phrase, idx) => (
                <span
                  key={idx}
                  className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-sm"
                >
                  {phrase.translated_text || phrase.text}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Sentiment */}
        {claimComprehend.sentiment && (
          <div className="mb-4">
            <h4 className="font-semibold mb-2">Sentiment:</h4>
            <div className={`inline-block px-3 py-1 rounded ${
              claimComprehend.sentiment.sentiment === 'POSITIVE' ? 'bg-green-100 text-green-800' :
              claimComprehend.sentiment.sentiment === 'NEGATIVE' ? 'bg-red-100 text-red-800' :
              'bg-gray-100 text-gray-800'
            }`}>
              {claimComprehend.sentiment.sentiment} (
              {claimComprehend.sentiment.scores && (
                <>
                  Positive: {(claimComprehend.sentiment.scores.Positive || 0) * 100}% | 
                  Negative: {(claimComprehend.sentiment.scores.Negative || 0) * 100}% | 
                  Neutral: {(claimComprehend.sentiment.scores.Neutral || 0) * 100}%
                </>
              )}
              )
            </div>
          </div>
        )}

        {/* Audio Player */}
        {claim_description.polly && (
          <div>
            <h4 className="font-semibold mb-2">🎵 Audio Summary</h4>
            <audio controls className="w-full">
              <source src={getAudioUrl(claim_description.polly.audio_url)} type="audio/mpeg" />
              Your browser does not support the audio element.
            </audio>
          </div>
        )}
      </div>

      {/* Files Section */}
      {files.map((file, fileIdx) => {
        const fileTextract = file.translated_textract || file.textract;
        const fileComprehend = file.translated_comprehend || file.comprehend;
        const fileRekognition = file.rekognition;
        
        // Check if this is the accident photo (first file, has Rekognition, no Textract)
        const isAccidentPhoto = fileIdx === 0 && fileRekognition && !fileTextract;

        return (
          <div key={fileIdx} className="border border-gray-300 rounded-lg p-4">
            <h3 className="text-xl font-semibold mb-3">
              {isAccidentPhoto ? '📷' : '📄'} {file.filename} ({file.file_type.toUpperCase()})
            </h3>

            {/* Accident Photo with Labels Overlay */}
            {isAccidentPhoto && accidentPhoto && fileRekognition?.labels && fileRekognition.labels.length > 0 && (
              <div className="mb-4">
                <h4 className="font-semibold mb-2">Accident Photo with Detected Objects:</h4>
                <ImageWithLabels 
                  imageFile={accidentPhoto} 
                  labels={fileRekognition.labels}
                />
              </div>
            )}

            {/* Extracted Text */}
            {fileTextract?.full_text && (
              <div className="mb-4">
                <h4 className="font-semibold mb-2">Extracted Text:</h4>
                <div className="bg-gray-50 p-3 rounded border max-h-48 overflow-y-auto">
                  <p className="whitespace-pre-wrap text-sm">
                    {fileTextract.translated_text || fileTextract.full_text}
                  </p>
                </div>
              </div>
            )}

            {/* Form Fields */}
            {fileTextract?.key_value_pairs && fileTextract.key_value_pairs.length > 0 && (
              <div className="mb-4">
                <h4 className="font-semibold mb-2">Form Fields:</h4>
                <div className="space-y-1">
                  {fileTextract.key_value_pairs.map((kv, idx) => (
                    <div key={idx} className="text-sm">
                      <span className="font-medium">{kv.key}:</span> {kv.value}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Image Labels (for non-accident photos or if no bounding boxes) */}
            {fileRekognition?.labels && fileRekognition.labels.length > 0 && !isAccidentPhoto && (
              <div className="mb-4">
                <h4 className="font-semibold mb-2">Detected in Images:</h4>
                <div className="flex flex-wrap gap-2">
                  {fileRekognition.labels.map((label, idx) => (
                    <span
                      key={idx}
                      className="bg-purple-100 text-purple-800 px-2 py-1 rounded text-sm"
                    >
                      {label.translated_name || label.name} ({label.confidence.toFixed(1)}%)
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* File Audio */}
            {file.polly && (
              <div>
                <h4 className="font-semibold mb-2">🎵 Audio Summary</h4>
                <audio controls className="w-full">
                  <source src={getAudioUrl(file.polly.audio_url)} type="audio/mpeg" />
                  Your browser does not support the audio element.
                </audio>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

