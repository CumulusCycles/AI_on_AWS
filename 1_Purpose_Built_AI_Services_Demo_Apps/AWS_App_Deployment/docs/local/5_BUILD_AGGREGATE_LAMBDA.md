# Aggregate Lambda Build Guide

This guide will help you build the Aggregate Lambda function. This Lambda receives AI analysis results from the Preprocessing Lambda, stores the image in S3, stores metadata in DynamoDB, and returns aggregated JSON results.

## Overview

We'll build a modular Lambda function with the following structure:
- **Main application** (`index.ts`): Express app, routes, and Lambda handler
- **Configuration module** (`config.ts`): AWS client initialization and environment variables
- **Type definitions** (`types.ts`): TypeScript interfaces and types
- **Service modules** (`services/`): Separate modules for each AWS service integration
  - `s3.ts`: Amazon S3 image storage
  - `dynamodb.ts`: Amazon DynamoDB metadata storage
  - `aggregator.ts`: Aggregation logic and response formatting
- Local development server for testing

This modular structure provides better separation of concerns, testability, and maintainability while keeping the deployment simple.

## Prerequisites

- Node.js 20.x or higher
- npm or yarn
- AWS CLI configured with credentials
- Access to AWS services: S3, DynamoDB
- TypeScript knowledge

## Step-by-Step Build

### Step 1: Create Directory Structure

Create the Lambda function directory and all subdirectories:

```bash
cd 1_Purpose_Built_AI_Services_Demo_Apps/AWS_App_Deployment
mkdir -p lambda/aggregate/{services,middleware,routes,handlers}
cd lambda/aggregate
```

### Step 2: Initialize Node.js Project

Initialize a new Node.js project:

```bash
npm init -y
```

### Step 3: Install Dependencies

Install production dependencies:

```bash
npm install express @aws-sdk/client-s3 @aws-sdk/client-dynamodb @aws-sdk/lib-dynamodb uuid@^9.0.1
```

Install development dependencies:

```bash
npm install -D typescript @types/node @types/express @types/uuid ts-node nodemon @typescript-eslint/eslint-plugin @typescript-eslint/parser
```

Install Swagger dependencies:

```bash
npm install swagger-ui-express swagger-jsdoc
npm install -D @types/swagger-ui-express @types/swagger-jsdoc
```

**What these do:**
- `express` - Web framework for building the API
- `@aws-sdk/client-s3` - AWS SDK v3 for S3 operations
- `@aws-sdk/client-dynamodb` - AWS SDK v3 for DynamoDB operations
- `@aws-sdk/lib-dynamodb` - DynamoDB document client (simplified API)
- `uuid` - Generate unique IDs for claims
- `typescript` - TypeScript compiler
- `ts-node` - Run TypeScript directly
- `nodemon` - Auto-reload on file changes
- `swagger-ui-express` - Serves Swagger UI for API documentation
- `swagger-jsdoc` - Generates Swagger/OpenAPI spec from JSDoc comments

### Step 4: Configure TypeScript

Create `tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "commonjs",
    "lib": ["ES2022"],
    "outDir": "./dist",
    "rootDir": "./",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "moduleResolution": "node"
  },
  "include": ["**/*.ts"],
  "exclude": ["node_modules", "dist"]
}
```

### Step 5: Create Environment Variables File

Create `.env.local.example`:

```bash
# Environment variables for local testing
# Copy this file to .env.local and update with your values
# .env.local takes precedence over .env and is gitignored

# AWS Region (used for S3 and DynamoDB)
REGION=us-east-1

# S3 Bucket name for storing uploaded images
# This bucket will be created when we deploy with CDK
# For local testing, you can use an existing bucket or create one manually
S3_BUCKET_NAME=demo-claim-app-images

# DynamoDB Table name for storing claim metadata
# This table will be created when we deploy with CDK
# For local testing, you can use an existing table or create one manually
DYNAMODB_TABLE_NAME=demo-claim-app-claims

# AWS Credentials are loaded from:
# - AWS credentials file (~/.aws/credentials)
# - Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
# - IAM role (when running on EC2/Lambda)
```

Create `.env.local` (this file should be gitignored):

```bash
cp .env.local.example .env.local
# Then edit .env.local with your values
```

**Note:** For local testing, you can use existing S3 buckets and DynamoDB tables, or create them manually in the AWS Console. They'll be created automatically when we deploy with CDK.

### Step 6: Create the Express Application

We'll organize the code into multiple files for better maintainability and testability. Create the following structure:

**Directory structure:**
```
lambda/aggregate/
├── index.ts              # Express app initialization
├── config.ts            # Configuration and AWS clients
├── types.ts             # TypeScript interfaces
├── swagger.ts           # Swagger/OpenAPI configuration
├── middleware/
│   ├── logging.ts       # Request logging middleware
│   └── cors.ts          # CORS middleware
├── routes/
│   ├── health.ts        # Health check route
│   └── aggregate.ts     # Aggregate endpoint route
├── handlers/
│   └── lambda.ts        # Lambda handler wrapper
└── services/
    ├── __init__.ts (or empty)
    ├── s3.ts            # Amazon S3 storage
    ├── dynamodb.ts      # Amazon DynamoDB storage
    └── aggregator.ts    # Aggregation logic
```

#### Step 6a: Create Type Definitions

Create `types.ts`:

```typescript
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
```

**What this does:**
- Defines TypeScript interfaces for request and response types
- Provides type safety throughout the application
- Makes the code more maintainable and self-documenting

#### Step 6b: Create Configuration Module

Create `config.ts`:

```typescript
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
```

**What this does:**
- Loads environment variables from `.env.local` and `.env` files
- Initializes AWS clients (S3, DynamoDB)
- Exports configuration variables for use in other modules

#### Step 6c: Create Services Package

Create the services directory and `__init__.ts` file:

```bash
mkdir -p services
touch services/__init__.ts
```

The `__init__.ts` file can be empty - it just makes `services` a TypeScript package.

#### Step 6d: Create S3 Service

Create `services/s3.ts`:

```typescript
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
```

**What this does:**
- Encapsulates all Amazon S3 operations
- Handles image upload with proper content type detection
- Returns S3 key and URL for use by other modules

#### Step 6e: Create DynamoDB Service

Create `services/dynamodb.ts`:

```typescript
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
```

**What this does:**
- Encapsulates all Amazon DynamoDB operations
- Handles metadata storage with proper typing
- Provides error handling for missing configuration

#### Step 6f: Create Aggregator Service

Create `services/aggregator.ts`:

```typescript
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
```

**What this does:**
- Orchestrates the aggregation workflow
- Coordinates S3 upload and DynamoDB storage
- Formats the aggregated response
- Provides a clean interface for the main application

#### Step 6g: Create Middleware

Create the middleware directory and files:

```bash
mkdir -p middleware
```

Create `middleware/logging.ts`:

```typescript
import { Request, Response, NextFunction } from 'express';

export function loggingMiddleware(req: Request, res: Response, next: NextFunction) {
  console.log(`[EXPRESS_MIDDLEWARE] Request received - method: ${req.method}, path: ${req.path}`);
  const originalJson = res.json.bind(res);
  res.json = function(body: any) {
    console.log(`[EXPRESS_MIDDLEWARE] Response sent - status: ${res.statusCode}`);
    return originalJson(body);
  };
  next();
}
```

Create `middleware/cors.ts`:

```typescript
import { Request, Response, NextFunction } from 'express';

export function corsMiddleware(req: Request, res: Response, next: NextFunction) {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') {
    res.sendStatus(200);
  } else {
    next();
  }
}
```

**What these do:**
- Separates middleware logic from the main application
- Makes middleware reusable and testable
- Follows single responsibility principle

#### Step 6h: Create Swagger Configuration

Create `swagger.ts`:

```typescript
import swaggerJsdoc from 'swagger-jsdoc';

const swaggerOptions = {
  definition: {
    openapi: '3.0.0',
    info: {
      title: 'Aggregate Lambda API',
      version: '1.0.0',
      description: 'API for aggregating AI analysis results and storing in S3/DynamoDB',
    },
    servers: [
      {
        url: 'http://localhost:8001',
        description: 'Local development server',
      },
    ],
  },
  apis: ['./routes/*.ts', './index.ts'], // Path to the API files
};

export const swaggerSpec = swaggerJsdoc(swaggerOptions);
```

**What this does:**
- Centralizes Swagger configuration
- Makes it easy to update API documentation settings
- Keeps the main application file clean

#### Step 6i: Create Routes

Create the routes directory:

```bash
mkdir -p routes
```

Create `routes/health.ts`:

```typescript
import { Router, Request, Response } from 'express';

const router = Router();

/**
 * @swagger
 * /health:
 *   get:
 *     summary: Health check endpoint
 *     tags: [Health]
 *     responses:
 *       200:
 *         description: Service is healthy
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 status:
 *                   type: string
 *                   example: healthy
 *                 service:
 *                   type: string
 *                   example: aggregate
 */
router.get('/health', (req: Request, res: Response) => {
  res.json({ status: 'healthy', service: 'aggregate' });
});

export default router;
```

Create `routes/aggregate.ts`:

```typescript
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
```

**What these do:**
- Separates route handlers into dedicated modules
- Makes routes easier to test and maintain
- Follows Express.js best practices for route organization

#### Step 6j: Create Lambda Handler

Create the handlers directory:

```bash
mkdir -p handlers
```

Create `handlers/lambda.ts`:

```typescript
import { aggregateAndStore } from '../services/aggregator';
import { AggregateRequest } from '../types';

export async function lambdaHandler(event: any) {
  console.log(`[LAMBDA_HANDLER] Lambda invoked - event keys: ${Object.keys(event).join(', ')}`);
  
  const isDirectInvocation =
    event &&
    typeof event === 'object' &&
    event.claim_description !== undefined &&
    event.image_bytes !== undefined &&
    event.image_filename !== undefined;

  if (isDirectInvocation) {
    console.log(`[LAMBDA_HANDLER] Direct Lambda invocation detected - processing payload directly`);
    return await aggregateAndStore(event as AggregateRequest);
  }

  console.log(`[LAMBDA_HANDLER] API Gateway invocation detected`);
  const httpMethod = event.requestContext?.http?.method || event.httpMethod;
  const path = event.requestContext?.http?.path || event.path || '/';
  const body = event.body || '{}';

  console.log(`[LAMBDA_HANDLER] Parsed - method: ${httpMethod}, path: ${path}`);

  try {
    if (path === '/health' && httpMethod === 'GET') {
      return {
        statusCode: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: 'healthy', service: 'aggregate' }),
      };
    }

    if (path === '/aggregate' && httpMethod === 'POST') {
      const payload = typeof body === 'string' ? JSON.parse(body) : body;
      const response = await aggregateAndStore(payload as AggregateRequest);
      return {
        statusCode: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(response),
      };
    }

    return {
      statusCode: 404,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ error: 'Not found' }),
    };
  } catch (error: any) {
    console.error(`[LAMBDA_HANDLER] Error handling request: ${error.message}`, error);
    return {
      statusCode: 500,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ error: 'Error aggregating results', message: error.message }),
    };
  }
}
```

**What this does:**
- Separates Lambda handler logic from Express app
- Makes the handler testable independently
- Keeps the main application file focused on Express setup

#### Step 6k: Create Main Application File

Create `index.ts`:

```typescript
import express from 'express';
import swaggerUi from 'swagger-ui-express';
import { swaggerSpec } from './swagger';
import { loggingMiddleware } from './middleware/logging';
import { corsMiddleware } from './middleware/cors';
import healthRoutes from './routes/health';
import aggregateRoutes from './routes/aggregate';
import { lambdaHandler } from './handlers/lambda';

const app = express();

// Middleware
app.use(loggingMiddleware);
app.use(express.json({ limit: '50mb' })); // Large limit for image data
app.use(corsMiddleware);

// Swagger documentation
app.use('/docs', swaggerUi.serve, swaggerUi.setup(swaggerSpec));

// Routes
app.use('/', healthRoutes);
app.use('/', aggregateRoutes);

// Lambda handler wrapper
export const handler = lambdaHandler;

// Export Express app for local development
export default app;
```

**What this does:**
- Initializes Express application
- Registers middleware (logging, CORS, JSON parsing)
- Sets up Swagger documentation
- Registers route handlers
- Exports Lambda handler for AWS deployment

**Benefits of this modular structure:**
- **Separation of concerns**: Each component (middleware, routes, services, handlers) has its own module
- **Testability**: All components can be tested independently
- **Maintainability**: Changes to one component don't affect others
- **Reusability**: Modules can be reused across projects
- **Clarity**: Main application file is clean and focused on app setup
- **Scalability**: Easy to add new routes, middleware, or services
- **Best practices**: Follows Express.js and Node.js architectural patterns

### Step 7: Create Local Development Server

Create `run_local.ts`:

```typescript
import app from './index';

const PORT = process.env.PORT || 8001;

app.listen(PORT, () => {
  console.log(`Aggregate Lambda running on http://localhost:${PORT}`);
  console.log(`Health check: http://localhost:${PORT}/health`);
});
```

### Step 8: Update package.json Scripts

Update `package.json` to add scripts:

```json
{
  "scripts": {
    "dev": "nodemon --exec ts-node run_local.ts",
    "build": "tsc",
    "start": "node dist/run_local.js"
  }
}
```

### Step 9: Install dotenv Package

We need `dotenv` for loading environment variables:

```bash
npm install dotenv
npm install -D @types/dotenv
```

### Step 10: Create .gitignore

Create `.gitignore`:

```gitignore
# Dependencies
node_modules/

# Build output
dist/

# Environment variables
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
npm-debug.log*
```

### Step 11: Configure AWS Credentials

Make sure AWS credentials are configured (same as Preprocessing Lambda):

```bash
aws configure
```

**Required AWS Permissions:**
- `s3:PutObject` (for uploading images)
- `dynamodb:PutItem` (for storing metadata)

### Step 12: Create S3 Bucket and DynamoDB Table (For Local Testing)

For local testing, you need to create these resources manually:

**Create S3 Bucket:**
```bash
aws s3 mb s3://demo-claim-app-images --region us-east-1
```

**Create DynamoDB Table:**
```bash
aws dynamodb create-table \
  --table-name demo-claim-app-claims \
  --attribute-definitions AttributeName=claimId,AttributeType=S \
  --key-schema AttributeName=claimId,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

**Note:** These will be created automatically when we deploy with CDK. For now, create them manually for local testing, or use existing buckets/tables and update `.env.local` accordingly.

### Step 13: Test Locally

Start the local development server:

```bash
npm run dev
```

The server will start on `http://localhost:8001`.

**Test the health endpoint:**
```bash
curl http://localhost:8001/health
```

**Expected response:**
```json
{"status": "healthy", "service": "aggregate"}
```

**View API documentation:**
Swagger UI is automatically available. Open your browser and visit:
```
http://localhost:8001/docs
```

This provides an interactive API documentation interface where you can:
- View all available endpoints
- See request/response schemas
- Test endpoints directly from the browser

### Step 14: Test with Preprocessing Lambda

Test the Lambda-to-Lambda integration between Preprocessing and Aggregate Lambdas.

1. **Start the Aggregate Lambda** (if not already running):
   ```bash
   cd lambda/aggregate
   npm run dev
   ```

2. **Start the Preprocessing Lambda** (if not already running):
   ```bash
   cd lambda/preprocessing
   python run_local.py
   ```

3. **Update Preprocessing Lambda `.env.local`** to point to local Aggregate Lambda:
   ```bash
   AGGREGATE_LAMBDA_LOCAL_URL=http://localhost:8001
   ```

4. **Test using the Preprocessing Lambda's `/docs` endpoint:**
   - Open `http://localhost:8000/docs` in your browser
   - Use the `/process-claim` endpoint
   - Submit a claim description and accident photo
   - Verify the response includes aggregated results

**What to expect:**
- ✅ Preprocessing Lambda calls Comprehend and Rekognition
- ✅ Preprocessing Lambda calls Aggregate Lambda (local)
- ✅ Aggregate Lambda stores image in S3
- ✅ Aggregate Lambda stores metadata in DynamoDB
- ✅ Aggregate Lambda returns aggregated JSON
- ✅ Preprocessing Lambda returns complete results

### Step 15: Test Full End-to-End Flow

Test the complete flow from frontend through both Lambda functions.

1. **Ensure all services are running:**
   - Aggregate Lambda: `http://localhost:8001`
   - Preprocessing Lambda: `http://localhost:8000`
   - Frontend: `http://localhost:5173` (or the port shown in your terminal)

2. **Start the frontend** (if not already running):
   ```bash
   cd frontend
   npm run dev
   ```

3. **Test the full flow:**
   - Open the frontend in your browser
   - Fill in the claim description
   - Upload an accident photo
   - Click "Submit Claim"
   - Verify results appear in the JSON panel on the right

**What to expect:**
- ✅ Frontend sends form data to Preprocessing Lambda
- ✅ Preprocessing Lambda calls Comprehend and Rekognition
- ✅ Preprocessing Lambda calls Aggregate Lambda (local)
- ✅ Aggregate Lambda stores image in S3
- ✅ Aggregate Lambda stores metadata in DynamoDB
- ✅ Aggregate Lambda returns aggregated JSON
- ✅ Preprocessing Lambda returns results to frontend
- ✅ Frontend displays complete results in JSON panel

### Step 16: Clean Up AWS Resources (Optional)

If you created S3 buckets and DynamoDB tables for local testing, you may want to clean them up to avoid ongoing costs.

**⚠️ Warning:** This will permanently delete all data in the bucket and table. Only do this if you're done testing and don't need the data.

**Empty and Delete S3 Bucket:**

1. First, empty the bucket (S3 buckets must be empty before deletion):
   ```bash
   aws s3 rm s3://demo-claim-app-images --recursive
   ```

2. Then delete the bucket:
   ```bash
   aws s3 rb s3://demo-claim-app-images --region us-east-1
   ```

**Delete DynamoDB Table:**

```bash
aws dynamodb delete-table \
  --table-name demo-claim-app-claims \
  --region us-east-1
```

**Verify Deletion:**

- Check S3 bucket is deleted:
  ```bash
  aws s3 ls | grep demo-claim-app-images
  ```
  (Should return nothing if deleted)

- Check DynamoDB table is deleted:
  ```bash
  aws dynamodb list-tables --region us-east-1 | grep demo-claim-app-claims
  ```
  (Should return nothing if deleted)

**Note:** If you're planning to deploy with CDK, you can skip manual cleanup as CDK will manage these resources. The CDK stack can be destroyed with `cdk destroy` which will clean up all resources automatically.

