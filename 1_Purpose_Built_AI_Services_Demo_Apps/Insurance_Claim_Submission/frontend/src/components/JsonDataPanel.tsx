import JsonView from 'react18-json-view';
import { ProcessingResult } from '../types';
import CollapsibleSection from './CollapsibleSection';

interface JsonDataPanelProps {
  result: ProcessingResult;
}

export default function JsonDataPanel({ result }: JsonDataPanelProps) {
  return (
    <div className="h-full overflow-y-auto">
      <h2 className="text-xl font-bold mb-4 sticky top-0 bg-white pb-2">JSON Data</h2>
      
      <CollapsibleSection title="Claim Description" defaultOpen={false}>
        <JsonView
          src={result.claim_description}
          theme="monokai"
          collapsed={1}
        />
      </CollapsibleSection>

      {result.files.map((file, idx) => (
        <CollapsibleSection key={idx} title={`File: ${file.filename}`} defaultOpen={false}>
          <div className="space-y-2">
            {file.textract && (
              <div>
                <h4 className="font-semibold mb-1">Textract:</h4>
                <JsonView
                  src={file.textract}
                  theme="monokai"
                  collapsed={2}
                />
              </div>
            )}
            
            {file.rekognition && (
              <div>
                <h4 className="font-semibold mb-1">Rekognition:</h4>
                <JsonView
                  src={file.rekognition}
                  theme="monokai"
                  collapsed={2}
                />
              </div>
            )}
            
            {file.comprehend && (
              <div>
                <h4 className="font-semibold mb-1">Comprehend:</h4>
                <JsonView
                  src={file.comprehend}
                  theme="monokai"
                  collapsed={2}
                />
              </div>
            )}
            
            {file.translated_textract && (
              <div>
                <h4 className="font-semibold mb-1">Translated Textract:</h4>
                <JsonView
                  src={file.translated_textract}
                  theme="monokai"
                  collapsed={2}
                />
              </div>
            )}
            
            {file.translated_comprehend && (
              <div>
                <h4 className="font-semibold mb-1">Translated Comprehend:</h4>
                <JsonView
                  src={file.translated_comprehend}
                  theme="monokai"
                  collapsed={2}
                />
              </div>
            )}
            
            {file.polly && (
              <div>
                <h4 className="font-semibold mb-1">Polly:</h4>
                <JsonView
                  src={file.polly}
                  theme="monokai"
                  collapsed={2}
                />
              </div>
            )}
            
            {file.error && (
              <div className="text-red-600 text-sm">Error: {file.error}</div>
            )}
          </div>
        </CollapsibleSection>
      ))}

      <CollapsibleSection title="Processing Status" defaultOpen={false}>
        <JsonView
          src={result.processing_status}
          theme="monokai"
          collapsed={1}
        />
      </CollapsibleSection>
    </div>
  );
}

