// TypeScript type definitions: 
// defines interfaces and types used throughout the application
export interface ClaimFormData {
    claim_description: string;
    accident_photo: File | undefined;
  }

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