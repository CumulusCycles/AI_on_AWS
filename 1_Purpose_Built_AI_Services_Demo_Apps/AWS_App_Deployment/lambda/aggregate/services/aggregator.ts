import { v4 as uuidv4 } from 'uuid';
import { AggregateRequest, AggregateResponse } from '../types';
import { uploadImageToS3 } from './s3';
import { storeMetadataInDynamoDB, DynamoDBItem } from './dynamodb';
import { S3_BUCKET_NAME, DYNAMODB_TABLE_NAME } from '../config';

export async function aggregateAndStore(payload: AggregateRequest): Promise<AggregateResponse> {
  const {
    claim_description,
    image_bytes,
    image_filename,
    comprehend_result,
    rekognition_result,
  } = payload;

  if (!S3_BUCKET_NAME || !DYNAMODB_TABLE_NAME) {
    throw new Error('Server configuration error: S3_BUCKET_NAME or DYNAMODB_TABLE_NAME is not set');
  }

  console.log(
    `[REQUEST] Aggregate Lambda invoked - filename: ${image_filename}, description length: ${claim_description?.length || 0} chars`
  );

  const claimId = uuidv4();
  const timestamp = new Date().toISOString();
  console.log(`[STEP] Generated claimId: ${claimId}`);

  const imageBuffer = Buffer.from(image_bytes, 'hex');
  console.log(`[STEP] Image buffer created - size: ${imageBuffer.length} bytes`);

  // Upload to S3
  const { s3Key, s3Url } = await uploadImageToS3(imageBuffer, claimId, image_filename, timestamp);

  // Store in DynamoDB
  const dynamoDBItem: DynamoDBItem = {
    claimId,
    timestamp,
    claimDescription: claim_description,
    imageFilename: image_filename,
    s3Key,
    s3Url,
    comprehendResult: comprehend_result,
    rekognitionResult: rekognition_result,
    processingStatus: 'completed',
  };
  await storeMetadataInDynamoDB(dynamoDBItem);

  // Build response
  const response: AggregateResponse = {
    claimId,
    timestamp,
    detected_language: comprehend_result?.detected_language,
    claim_description: {
      original_text: claim_description,
      detected_language: comprehend_result?.detected_language,
      language_score: comprehend_result?.language_score,
      comprehend: comprehend_result,
    },
    files: [
      {
        filename: image_filename,
        file_type: 'image',
        s3_key: s3Key,
        s3_url: s3Url,
        rekognition: rekognition_result,
      },
    ],
    storage: {
      s3_bucket: S3_BUCKET_NAME,
      s3_key: s3Key,
      s3_url: s3Url,
      dynamodb_table: DYNAMODB_TABLE_NAME,
      dynamodb_item_id: claimId,
    },
    processing_status: {
      language_detection: 'completed',
      claim_comprehend: 'completed',
      image_rekognition: 'completed',
      storage: 'completed',
    },
  };

  console.log(
    `[RESPONSE] Returning aggregated response - claimId: ${claimId}, s3_url: ${s3Url}, dynamodb_item_id: ${claimId}`
  );
  return response;
}