#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { RagS3VectorsStack } from './rag-stack';

const app = new cdk.App();

new RagS3VectorsStack(app, 'RagS3VectorsStack', {
  env: { region: 'us-east-1' },
});
