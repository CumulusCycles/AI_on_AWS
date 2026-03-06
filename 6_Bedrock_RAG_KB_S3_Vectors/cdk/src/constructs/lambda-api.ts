import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as apigwv2 from 'aws-cdk-lib/aws-apigatewayv2';
import { HttpLambdaIntegration } from 'aws-cdk-lib/aws-apigatewayv2-integrations';
import { Construct } from 'constructs';

export interface LambdaApiProps {
  /** Bedrock Knowledge Base ID (token resolved at deploy time). */
  knowledgeBaseId: string;
  /** Local path to the directory containing the Lambda handler. */
  lambdaCodePath: string;
}

/**
 * Creates the Lambda function (Python) and HTTP API:
 *   IAM role  →  Lambda  →  HttpApi (POST /chat, CORS)
 */
export class LambdaApi extends Construct {
  public readonly apiUrl: string;

  constructor(scope: Construct, id: string, props: LambdaApiProps) {
    super(scope, id);

    const region = cdk.Stack.of(this).region;
    // Amazon Nova Lite — KB-supported, first-party; often no Marketplace subscription required.
    const foundationModelArn =
      `arn:aws:bedrock:${region}::foundation-model/amazon.nova-lite-v1:0`;

    // ── Lambda execution role ───────────────────────────────────────
    const lambdaRole = new iam.Role(this, 'LambdaRole', {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName(
          'service-role/AWSLambdaBasicExecutionRole',
        ),
      ],
    });

    lambdaRole.addToPolicy(
      new iam.PolicyStatement({
        sid: 'BedrockRAG',
        actions: ['bedrock:RetrieveAndGenerate', 'bedrock:Retrieve'],
        resources: [`arn:aws:bedrock:${region}:*:knowledge-base/*`],
      }),
    );

    lambdaRole.addToPolicy(
      new iam.PolicyStatement({
        sid: 'BedrockInvokeModel',
        actions: ['bedrock:InvokeModel'],
        resources: [foundationModelArn],
      }),
    );

    // Required for Bedrock to complete/check Marketplace subscription when invoking the model.
    lambdaRole.addToPolicy(
      new iam.PolicyStatement({
        sid: 'BedrockMarketplace',
        actions: ['aws-marketplace:ViewSubscriptions', 'aws-marketplace:Subscribe'],
        resources: ['*'],
      }),
    );

    // ── Lambda function ─────────────────────────────────────────────
    const fn = new lambda.Function(this, 'ChatHandler', {
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'lambda.lambda_handler',
      code: lambda.Code.fromAsset(props.lambdaCodePath),
      role: lambdaRole,
      timeout: cdk.Duration.seconds(30),
      environment: {
        KNOWLEDGE_BASE_ID: props.knowledgeBaseId,
        FOUNDATION_MODEL_ARN: foundationModelArn,
      },
    });

    // ── API Gateway HTTP API ────────────────────────────────────────
    const httpApi = new apigwv2.HttpApi(this, 'HttpApi', {
      corsPreflight: {
        allowOrigins: ['*'],
        allowMethods: [apigwv2.CorsHttpMethod.POST],
        allowHeaders: ['Content-Type'],
      },
    });

    httpApi.addRoutes({
      path: '/chat',
      methods: [apigwv2.HttpMethod.POST],
      integration: new HttpLambdaIntegration('ChatIntegration', fn),
    });

    this.apiUrl = `${httpApi.apiEndpoint}/chat`;
  }
}
