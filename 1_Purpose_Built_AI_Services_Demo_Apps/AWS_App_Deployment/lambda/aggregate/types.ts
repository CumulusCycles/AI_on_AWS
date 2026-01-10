export interface AggregateRequest {
    claim_description: string;
    image_bytes: string; // Hex string
    image_filename: string;
    comprehend_result: any;
    rekognition_result: any;
  }
  
  export interface AggregateResponse {
    claimId: string;
    timestamp: string;
    detected_language?: string;
    claim_description: {
      original_text: string;
      detected_language?: string;
      language_score?: number;
      comprehend: any;
    };
    files: Array<{
      filename: string;
      file_type: string;
      s3_key: string;
      s3_url: string;
      rekognition: any;
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
  }