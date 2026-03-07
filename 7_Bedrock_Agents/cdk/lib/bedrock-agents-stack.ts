import * as path from 'path';
import * as fs from 'fs';
import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as s3deploy from 'aws-cdk-lib/aws-s3-deployment';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as bedrock from 'aws-cdk-lib/aws-bedrock';
import * as s3vectors from 'aws-cdk-lib/aws-s3vectors';
import * as cr from 'aws-cdk-lib/custom-resources';
import { Construct } from 'constructs';

const PREFIX = 'ai-agent-insure';
/** Foundation model for the agent; use one that supports direct foundation-model invocation (like 6_*). */
const FOUNDATION_MODEL = 'anthropic.claude-3-haiku-20240307-v1:0';
const EMBEDDING_MODEL = 'amazon.titan-embed-text-v2:0';
const EMBEDDING_DIMENSIONS = 1024;
const IDLE_SESSION_TTL = 1800;

/** Path to KB docs (shared with 4_Bedrock_RAG_KB). From cdk/lib, ../../ = 7_Bedrock_Agents, ../../../ = repo root. */
const KB_DOCS_PATH = path.join(__dirname, '../../../4_Bedrock_RAG_KB/assets');

export class BedrockAgentsStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const account = this.account;
    const region = this.region;

    // ── Expiry dates for demo policies (days from now) ─────────────────
    const now = new Date();
    const expiry180 = new Date(now.getTime() + 180 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10);
    const expiry90 = new Date(now.getTime() + 90 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10);
    const expiry270 = new Date(now.getTime() + 270 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10);

    // ── S3 docs bucket ─────────────────────────────────────────────────
    const docsBucket = new s3.Bucket(this, 'DocsBucket', {
      bucketName: `${PREFIX}-docs-${account}`,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
    });

    new s3deploy.BucketDeployment(this, 'DeployKbDocs', {
      sources: [s3deploy.Source.asset(KB_DOCS_PATH)],
      destinationBucket: docsBucket,
      contentType: 'text/markdown',
    });

    // ── S3 Vectors (vector bucket + index) ───────────────────────────
    const vectorBucket = new s3vectors.CfnVectorBucket(this, 'VectorBucket', {
      vectorBucketName: `${PREFIX}-vectors-${account}`,
    });

    const vectorBucketName = `${PREFIX}-vectors-${account}`;
    const vectorIndex = new s3vectors.CfnIndex(this, 'VectorIndex', {
      vectorBucketArn: vectorBucket.attrVectorBucketArn,
      indexName: `${PREFIX}-index`,
      dataType: 'float32',
      dimension: EMBEDDING_DIMENSIONS,
      distanceMetric: 'cosine',
      metadataConfiguration: {
        nonFilterableMetadataKeys: ['AMAZON_BEDROCK_TEXT'],
      },
    });
    vectorIndex.addDependency(vectorBucket);

    // ── DynamoDB tables ──────────────────────────────────────────────
    const claimsTable = new dynamodb.Table(this, 'ClaimsTable', {
      tableName: `${PREFIX}-claims`,
      partitionKey: { name: 'claim_id', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    const policiesTable = new dynamodb.Table(this, 'PoliciesTable', {
      tableName: `${PREFIX}-policies`,
      partitionKey: { name: 'policy_id', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // ── Lambda (claims action group) ──────────────────────────────────
    const lambdaRole = new iam.Role(this, 'LambdaRole', {
      roleName: `${PREFIX}-lambda-role`,
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
    });
    lambdaRole.addManagedPolicy(
      iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
    );
    claimsTable.grantReadWriteData(lambdaRole);
    policiesTable.grantReadWriteData(lambdaRole);

    const claimsLambda = new lambda.Function(this, 'ClaimsLambda', {
      functionName: `${PREFIX}-claims`,
      description: 'AI Agent Insure — Bedrock Agent action group handler',
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'claims_lambda.lambda_handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../action_groups')),
      timeout: cdk.Duration.seconds(30),
      memorySize: 256,
      role: lambdaRole,
      environment: {
        CLAIMS_TABLE: claimsTable.tableName,
        POLICIES_TABLE: policiesTable.tableName,
      },
    });

    claimsLambda.addPermission('AllowBedrockAgentInvoke', {
      principal: new iam.ServicePrincipal('bedrock.amazonaws.com'),
      action: 'lambda:InvokeFunction',
      sourceArn: `arn:aws:bedrock:${region}:${account}:agent/*`,
    });

    // ── KB IAM role ──────────────────────────────────────────────────
    const kbRole = new iam.Role(this, 'KbRole', {
      roleName: `${PREFIX}-kb-role`,
      assumedBy: new iam.ServicePrincipal('bedrock.amazonaws.com').withConditions({
        StringEquals: { 'aws:SourceAccount': account },
      }),
    });
    kbRole.addToPolicy(
      new iam.PolicyStatement({
        actions: ['s3:GetObject', 's3:ListBucket'],
        resources: [docsBucket.bucketArn, `${docsBucket.bucketArn}/*`],
      }),
    );
    kbRole.addToPolicy(
      new iam.PolicyStatement({
        actions: [
          's3vectors:GetIndex',
          's3vectors:PutVectors',
          's3vectors:GetVectors',
          's3vectors:DeleteVectors',
          's3vectors:QueryVectors',
        ],
        resources: ['*'],
      }),
    );
    kbRole.addToPolicy(
      new iam.PolicyStatement({
        actions: ['bedrock:InvokeModel'],
        resources: [`arn:aws:bedrock:${region}::foundation-model/${EMBEDDING_MODEL}`],
      }),
    );

    // ── Bedrock Knowledge Base ────────────────────────────────────────
    const kb = new bedrock.CfnKnowledgeBase(this, 'KB', {
      name: `${PREFIX}-kb`,
      description: 'AI Agent Insure product and coverage knowledge base',
      roleArn: kbRole.roleArn,
      knowledgeBaseConfiguration: {
        type: 'VECTOR',
        vectorKnowledgeBaseConfiguration: {
          embeddingModelArn: `arn:aws:bedrock:${region}::foundation-model/${EMBEDDING_MODEL}`,
          embeddingModelConfiguration: {
            bedrockEmbeddingModelConfiguration: {
              dimensions: EMBEDDING_DIMENSIONS,
              embeddingDataType: 'FLOAT32',
            },
          },
        },
      },
      storageConfiguration: {
        type: 'S3_VECTORS',
        s3VectorsConfiguration: {
          vectorBucketArn: vectorBucket.attrVectorBucketArn,
          indexArn: vectorIndex.attrIndexArn,
        },
      },
    });
    kb.node.addDependency(kbRole);
    kb.node.addDependency(vectorIndex);

    // ── Data source (S3 docs) ────────────────────────────────────────
    const dataSource = new bedrock.CfnDataSource(this, 'DataSource', {
      name: `${PREFIX}-docs`,
      description: 'AI Agent Insure product documents',
      knowledgeBaseId: kb.ref,
      dataSourceConfiguration: {
        type: 'S3',
        s3Configuration: { bucketArn: docsBucket.bucketArn },
      },
      vectorIngestionConfiguration: {
        chunkingConfiguration: {
          chunkingStrategy: 'FIXED_SIZE',
          fixedSizeChunkingConfiguration: {
            maxTokens: 512,
            overlapPercentage: 20,
          },
        },
      },
    });
    dataSource.node.addDependency(docsBucket);

    // ── KB ingestion custom resource (start job + wait) ────────────────
    const ingestionHandler = new lambda.Function(this, 'IngestionHandler', {
      runtime: lambda.Runtime.NODEJS_20_X,
      handler: 'index.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../lambdas/kb-ingestion')),
      timeout: cdk.Duration.minutes(6),
    });
    ingestionHandler.addToRolePolicy(
      new iam.PolicyStatement({
        actions: ['bedrock:StartIngestionJob', 'bedrock:GetIngestionJob'],
        resources: ['*'],
      }),
    );

    const ingestionProvider = new cr.Provider(this, 'IngestionProvider', {
      onEventHandler: ingestionHandler,
    });

    const ingestionCr = new cdk.CustomResource(this, 'KbIngestion', {
      serviceToken: ingestionProvider.serviceToken,
      properties: {
        KnowledgeBaseId: kb.ref,
        DataSourceId: dataSource.attrDataSourceId,
        Region: region,
      },
    });
    ingestionCr.node.addDependency(dataSource);

    // ── DynamoDB seed (demo policies) ──────────────────────────────────
    const seedHandler = new lambda.Function(this, 'SeedPoliciesHandler', {
      runtime: lambda.Runtime.NODEJS_20_X,
      handler: 'index.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../lambdas/seed-policies')),
      timeout: cdk.Duration.seconds(30),
    });
    policiesTable.grantReadWriteData(seedHandler);

    const seedProvider = new cr.Provider(this, 'SeedProvider', {
      onEventHandler: seedHandler,
    });

    const policiesItems = [
      {
        policy_id: { S: 'POL-001' },
        holder: { S: 'Acme AI Corp' },
        product: { S: 'Agentic AI Liability Insurance' },
        coverage_limit: { N: '5000000' },
        deductible: { N: '25000' },
        status: { S: 'active' },
        expiry: { S: expiry180 },
      },
      {
        policy_id: { S: 'POL-002' },
        holder: { S: 'NeuralOps Ltd' },
        product: { S: 'AI Infrastructure & Operations Protection' },
        coverage_limit: { N: '2000000' },
        deductible: { N: '10000' },
        status: { S: 'active' },
        expiry: { S: expiry90 },
      },
      {
        policy_id: { S: 'POL-003' },
        holder: { S: 'RoboFleet Systems' },
        product: { S: 'Autonomous Systems & Robotics Coverage' },
        coverage_limit: { N: '10000000' },
        deductible: { N: '50000' },
        status: { S: 'active' },
        expiry: { S: expiry270 },
      },
    ];

    new cdk.CustomResource(this, 'SeedPolicies', {
      serviceToken: seedProvider.serviceToken,
      properties: {
        TableName: policiesTable.tableName,
        Policies: policiesItems,
      },
    }).node.addDependency(policiesTable);

    // ── Agent IAM role ───────────────────────────────────────────────
    const agentRole = new iam.Role(this, 'AgentRole', {
      roleName: `${PREFIX}-bedrock-agent-role`,
      assumedBy: new iam.ServicePrincipal('bedrock.amazonaws.com').withConditions({
        StringEquals: { 'aws:SourceAccount': account },
      }),
    });
    agentRole.addToPolicy(
      new iam.PolicyStatement({
        actions: ['bedrock:InvokeModel', 'bedrock:InvokeModelWithResponseStream'],
        resources: [`arn:aws:bedrock:${region}::foundation-model/${FOUNDATION_MODEL}`],
      }),
    );
    agentRole.addToPolicy(
      new iam.PolicyStatement({
        actions: ['lambda:InvokeFunction'],
        resources: [claimsLambda.functionArn],
      }),
    );
    agentRole.addToPolicy(
      new iam.PolicyStatement({
        actions: ['bedrock:Retrieve', 'bedrock:RetrieveAndGenerate'],
        resources: [`arn:aws:bedrock:${region}:${account}:knowledge-base/*`],
      }),
    );

    // ── Agent instruction and OpenAPI schema (from files) ───────────────
    const agentInstruction = fs.readFileSync(
      path.join(__dirname, '../../assets/agent_instruction.md'),
      'utf-8',
    );
    const openapiSchema = fs.readFileSync(
      path.join(__dirname, '../../action_groups/openapi_schema.json'),
      'utf-8',
    );

    // ── Bedrock Agent ─────────────────────────────────────────────────
    const agent = new bedrock.CfnAgent(this, 'Agent', {
      agentName: `${PREFIX}-assistant`,
      description: 'AI Agent Insure claims and policy assistant — powered by Amazon Bedrock Agents',
      agentResourceRoleArn: agentRole.roleArn,
      foundationModel: FOUNDATION_MODEL,
      instruction: agentInstruction,
      idleSessionTtlInSeconds: IDLE_SESSION_TTL,
      autoPrepare: true,
      skipResourceInUseCheckOnDelete: true,
      knowledgeBases: [
        {
          knowledgeBaseId: kb.ref,
          description: 'AI Agent Insure product and coverage knowledge base',
          knowledgeBaseState: 'ENABLED',
        },
      ],
      actionGroups: [
        {
          actionGroupName: 'ClaimsPolicyActions',
          description:
            'Submit claims, check claim status, look up policies, and get coverage summaries',
          actionGroupState: 'ENABLED',
          actionGroupExecutor: {
            lambda: claimsLambda.functionArn,
          },
          apiSchema: {
            payload: openapiSchema,
          },
        },
      ],
    });
    agent.node.addDependency(agentRole);
    agent.node.addDependency(claimsLambda);
    agent.node.addDependency(kb);
    agent.node.addDependency(ingestionCr);

    // ── Agent alias ───────────────────────────────────────────────────
    const agentAlias = new bedrock.CfnAgentAlias(this, 'AgentAlias', {
      agentId: agent.ref,
      agentAliasName: 'live',
      description: 'Production alias',
    });
    agentAlias.node.addDependency(agent);

    // ── Outputs ──────────────────────────────────────────────────────
    new cdk.CfnOutput(this, 'AgentIdOutput', {
      description: 'Bedrock Agent ID — set as AGENT_ID in backend/.env',
      value: agent.ref,
      exportName: `${PREFIX}-agent-id`,
    });
    new cdk.CfnOutput(this, 'AgentAliasIdOutput', {
      description: 'Bedrock Agent alias ID — set as AGENT_ALIAS_ID in backend/.env',
      value: agentAlias.ref,
      exportName: `${PREFIX}-agent-alias-id`,
    });
    new cdk.CfnOutput(this, 'KnowledgeBaseIdOutput', {
      description: 'Bedrock Knowledge Base ID',
      value: kb.ref,
    });
    new cdk.CfnOutput(this, 'DataSourceIdOutput', {
      description: 'Bedrock Data Source ID (for manual KB sync: start-ingestion-job)',
      value: dataSource.attrDataSourceId,
    });
    new cdk.CfnOutput(this, 'LambdaArnOutput', {
      description: 'Claims action group Lambda ARN',
      value: claimsLambda.functionArn,
    });
    new cdk.CfnOutput(this, 'DocsBucketName', {
      description: 'S3 bucket containing KB source documents',
      value: docsBucket.bucketName,
    });
    new cdk.CfnOutput(this, 'VectorBucketName', {
      description: 'S3 vector bucket name',
      value: vectorBucketName,
    });
    new cdk.CfnOutput(this, 'ClaimsTableOutput', {
      description: 'DynamoDB claims table name',
      value: claimsTable.tableName,
    });
    new cdk.CfnOutput(this, 'PoliciesTableOutput', {
      description: 'DynamoDB policies table name',
      value: policiesTable.tableName,
    });
  }
}
