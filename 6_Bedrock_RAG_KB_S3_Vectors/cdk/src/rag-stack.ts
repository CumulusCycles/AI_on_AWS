import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as path from 'path';
import { KnowledgeBase } from './constructs/knowledge-base';
import { LambdaApi } from './constructs/lambda-api';

export class RagS3VectorsStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const kb = new KnowledgeBase(this, 'KnowledgeBase', {
      docsAssetPath: path.join(__dirname, '..', '..', '..', '4_Bedrock_RAG_KB', 'assets'),
    });

    const api = new LambdaApi(this, 'LambdaApi', {
      knowledgeBaseId: kb.knowledgeBaseId,
      lambdaCodePath: path.join(__dirname, '..', '..', 'lambda'),
    });

    new cdk.CfnOutput(this, 'ApiUrl', {
      value: api.apiUrl,
      description: 'Full API endpoint — use as VITE_API_URL in frontend/.env',
    });

    new cdk.CfnOutput(this, 'KnowledgeBaseId', {
      value: kb.knowledgeBaseId,
      description: 'Bedrock Knowledge Base ID',
    });

    new cdk.CfnOutput(this, 'DocsBucketName', {
      value: kb.docsBucketName,
      description: 'S3 bucket containing the KB source documents',
    });
  }
}
