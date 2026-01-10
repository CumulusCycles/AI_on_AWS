import * as dotenv from 'dotenv';
import * as path from 'path';
import { S3Client } from '@aws-sdk/client-s3';
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient } from '@aws-sdk/lib-dynamodb';

// Load environment variables (only when running locally, not in Lambda)
// In Lambda, environment variables are provided by AWS
if (!process.env.AWS_LAMBDA_FUNCTION_NAME) {
  dotenv.config({ path: path.join(__dirname, '.env.local') });
  dotenv.config({ path: path.join(__dirname, '.env') });
}

// AWS clients
const region = process.env.REGION || 'us-east-1';
export const s3Client = new S3Client({ region });
export const dynamoDBClient = DynamoDBDocumentClient.from(new DynamoDBClient({ region }));

// Configuration
export const S3_BUCKET_NAME = process.env.S3_BUCKET_NAME;
export const DYNAMODB_TABLE_NAME = process.env.DYNAMODB_TABLE_NAME;
export const REGION = region;