import { PutObjectCommand } from '@aws-sdk/client-s3';
import { s3Client, S3_BUCKET_NAME, REGION } from '../config';

function getContentType(filename: string): string {
  const ext = filename.split('.').pop()?.toLowerCase();
  const contentTypes: Record<string, string> = {
    jpg: 'image/jpeg',
    jpeg: 'image/jpeg',
    png: 'image/png',
    gif: 'image/gif',
    bmp: 'image/bmp',
  };
  return contentTypes[ext || ''] || 'application/octet-stream';
}

export async function uploadImageToS3(
  imageBuffer: Buffer,
  claimId: string,
  imageFilename: string,
  timestamp: string
): Promise<{ s3Key: string; s3Url: string }> {
  if (!S3_BUCKET_NAME) {
    throw new Error('S3_BUCKET_NAME is not configured');
  }

  const s3Key = `claims/${claimId}/${imageFilename}`;
  console.log(`[STEP] Uploading image to S3 - bucket: ${S3_BUCKET_NAME}, key: ${s3Key}`);

  await s3Client.send(
    new PutObjectCommand({
      Bucket: S3_BUCKET_NAME,
      Key: s3Key,
      Body: imageBuffer,
      ContentType: getContentType(imageFilename),
      Metadata: {
        claimId,
        originalFilename: imageFilename,
        uploadedAt: timestamp,
      },
    })
  );

  const s3Url = `https://${S3_BUCKET_NAME}.s3.${REGION}.amazonaws.com/${s3Key}`;
  console.log(`[STEP] Image uploaded to S3 successfully - URL: ${s3Url}`);
  return { s3Key, s3Url };
}