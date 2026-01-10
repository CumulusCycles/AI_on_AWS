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