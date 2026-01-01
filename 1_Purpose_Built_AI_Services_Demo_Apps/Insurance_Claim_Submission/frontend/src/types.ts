export interface ProcessingResult {
  detected_language: string;
  claim_description: ClaimDescriptionResult;
  files: FileResult[];
  processing_status: Record<string, string>;
}

export interface ClaimDescriptionResult {
  original_text: string;
  detected_language: string;
  language_score: number;
  comprehend: ComprehendResult;
  translated_comprehend?: ComprehendResult;
  polly?: PollyResult;
  error?: string;
}

export interface FileResult {
  filename: string;
  file_type: string;
  textract?: TextractResult;
  rekognition?: RekognitionResult;
  comprehend?: ComprehendResult;
  translated_textract?: TextractResult;
  translated_comprehend?: ComprehendResult;
  polly?: PollyResult;
  error?: string;
}

export interface TextractResult {
  full_text: string;
  forms: any[];
  tables: any[];
  key_value_pairs: Array<{ key: string; value: string }>;
  translated_text?: string;
  error?: string;
}

export interface RekognitionResult {
  labels: Array<{
    name: string;
    confidence: number;
    categories?: string[];
    translated_name?: string;
    instances?: Array<{
      bounding_box: {
        width: number;
        height: number;
        left: number;
        top: number;
      };
      confidence: number;
    }>;
  }>;
  text_detections: Array<{
    text: string;
    confidence: number;
    type: string;
  }>;
  error?: string;
}

export interface ComprehendResult {
  entities: Array<{
    text: string;
    type: string;
    score: number;
    translated_text?: string;
  }>;
  key_phrases: Array<{
    text: string;
    score: number;
    translated_text?: string;
  }>;
  sentiment: {
    sentiment: string;
    scores: {
      Positive?: number;
      Negative?: number;
      Neutral?: number;
      Mixed?: number;
    };
  };
  error?: string;
}

export interface PollyResult {
  audio_url: string;
  text: string;
  voice_id: string;
  error?: string;
}

export interface ProcessingStatus {
  [key: string]: 'processing' | 'completed' | 'error';
}

