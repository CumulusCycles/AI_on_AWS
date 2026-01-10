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