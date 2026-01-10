import { PutCommand } from '@aws-sdk/lib-dynamodb';
import { dynamoDBClient, DYNAMODB_TABLE_NAME } from '../config';

export interface DynamoDBItem {
  claimId: string;
  timestamp: string;
  claimDescription: string;
  imageFilename: string;
  s3Key: string;
  s3Url: string;
  comprehendResult: any;
  rekognitionResult: any;
  processingStatus: string;
}

export async function storeMetadataInDynamoDB(item: DynamoDBItem): Promise<void> {
  if (!DYNAMODB_TABLE_NAME) {
    throw new Error('DYNAMODB_TABLE_NAME is not configured');
  }

  console.log(`[STEP] Storing metadata in DynamoDB - table: ${DYNAMODB_TABLE_NAME}, claimId: ${item.claimId}`);
  await dynamoDBClient.send(
    new PutCommand({
      TableName: DYNAMODB_TABLE_NAME,
      Item: item,
    })
  );
  console.log(`[STEP] Metadata stored in DynamoDB successfully`);
}