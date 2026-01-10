import { Router, Request, Response } from 'express';
import { aggregateAndStore } from '../services/aggregator';
import { AggregateRequest } from '../types';

const router = Router();

/**
 * @swagger
 * /aggregate:
 *   post:
 *     summary: Aggregate AI analysis results and store in S3/DynamoDB
 *     tags: [Aggregate]
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - claim_description
 *               - image_bytes
 *               - image_filename
 *               - comprehend_result
 *               - rekognition_result
 *             properties:
 *               claim_description:
 *                 type: string
 *                 description: The claim description text
 *               image_bytes:
 *                 type: string
 *                 description: Image file as hex string
 *               image_filename:
 *                 type: string
 *                 description: Original filename of the image
 *               comprehend_result:
 *                 type: object
 *                 description: Amazon Comprehend analysis results
 *               rekognition_result:
 *                 type: object
 *                 description: Amazon Rekognition analysis results
 *     responses:
 *       200:
 *         description: Successfully aggregated and stored results
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 claimId:
 *                   type: string
 *                 timestamp:
 *                   type: string
 *                 detected_language:
 *                   type: string
 *                 storage:
 *                   type: object
 *                   properties:
 *                     s3_url:
 *                       type: string
 *                     dynamodb_item_id:
 *                       type: string
 *       500:
 *         description: Error processing request
 */
router.post('/aggregate', async (req: Request, res: Response) => {
  try {
    const response = await aggregateAndStore(req.body as AggregateRequest);
    res.json(response);
  } catch (error: any) {
    console.error(`[ERROR] Error in aggregate endpoint - ${error.message}`, error);
    res.status(500).json({
      error: 'Error aggregating results',
      message: error.message,
    });
  }
});

export default router;