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