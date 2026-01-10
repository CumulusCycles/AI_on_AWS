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