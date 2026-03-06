import * as cdk from 'aws-cdk-lib';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as s3deploy from 'aws-cdk-lib/aws-s3-deployment';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as bedrock from 'aws-cdk-lib/aws-bedrock';
import * as s3vectors from 'aws-cdk-lib/aws-s3vectors';
import { Construct } from 'constructs';

const VECTOR_INDEX_NAME = 'rag-kb-index';
const TITAN_EMBED_DIMENSION = 1024;

export interface KnowledgeBaseProps {
  /** Local path to the directory containing KB corpus documents. */
  docsAssetPath: string;
}

/**
 * Creates the full Bedrock Knowledge Base backed by S3 Vectors:
 *   S3 docs bucket  →  BucketDeployment (uploads corpus)
 *   S3 VectorBucket  →  VectorIndex
 *   IAM role (Bedrock trust)
 *   CfnKnowledgeBase  →  CfnDataSource (S3)
 */
export class KnowledgeBase extends Construct {
  public readonly knowledgeBaseId: string;
  public readonly dataSourceId: string;
  public readonly docsBucketName: string;

  constructor(scope: Construct, id: string, props: KnowledgeBaseProps) {
    super(scope, id);

    const region = cdk.Stack.of(this).region;
    const embeddingModelArn =
      `arn:aws:bedrock:${region}::foundation-model/amazon.titan-embed-text-v2:0`;

    // ── S3 docs bucket ──────────────────────────────────────────────
    const docsBucket = new s3.Bucket(this, 'DocsBucket', {
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    });

    new s3deploy.BucketDeployment(this, 'DeployDocs', {
      sources: [s3deploy.Source.asset(props.docsAssetPath)],
      destinationBucket: docsBucket,
    });

    // ── S3 Vectors (vector bucket + index) ──────────────────────────
    const vectorBucket = new s3vectors.CfnVectorBucket(this, 'VectorBucket', {});

    const vectorIndex = new s3vectors.CfnIndex(this, 'VectorIndex', {
      vectorBucketArn: vectorBucket.attrVectorBucketArn,
      indexName: VECTOR_INDEX_NAME,
      dimension: TITAN_EMBED_DIMENSION,
      distanceMetric: 'cosine',
      dataType: 'float32',
    });
    vectorIndex.addDependency(vectorBucket);

    // ── Knowledge Base IAM role ─────────────────────────────────────
    const kbRole = new iam.Role(this, 'KbRole', {
      assumedBy: new iam.ServicePrincipal('bedrock.amazonaws.com'),
    });

    kbRole.addToPolicy(
      new iam.PolicyStatement({
        sid: 'S3ReadDocs',
        actions: ['s3:GetObject', 's3:ListBucket'],
        resources: [docsBucket.bucketArn, `${docsBucket.bucketArn}/*`],
      }),
    );

    kbRole.addToPolicy(
      new iam.PolicyStatement({
        sid: 'BedrockInvokeEmbeddingsModel',
        actions: ['bedrock:InvokeModel'],
        resources: [embeddingModelArn],
      }),
    );

    kbRole.addToPolicy(
      new iam.PolicyStatement({
        sid: 'S3VectorsAccess',
        actions: [
          's3vectors:PutVectors',
          's3vectors:GetVectors',
          's3vectors:DeleteVectors',
          's3vectors:QueryVectors',
          's3vectors:GetIndex',
        ],
        resources: [vectorIndex.attrIndexArn],
      }),
    );

    // ── Bedrock Knowledge Base ──────────────────────────────────────
    const kb = new bedrock.CfnKnowledgeBase(this, 'KB', {
      name: 'rag-s3-vectors-kb',
      roleArn: kbRole.roleArn,
      knowledgeBaseConfiguration: {
        type: 'VECTOR',
        vectorKnowledgeBaseConfiguration: { embeddingModelArn },
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

    // ── Data source (S3 docs) ───────────────────────────────────────
    const dataSource = new bedrock.CfnDataSource(this, 'DataSource', {
      name: 'rag-s3-docs',
      knowledgeBaseId: kb.ref,
      dataSourceConfiguration: {
        type: 'S3',
        s3Configuration: { bucketArn: docsBucket.bucketArn },
      },
    });

    // ── Exposed values ──────────────────────────────────────────────
    this.knowledgeBaseId = kb.ref;
    this.dataSourceId = dataSource.ref;
    this.docsBucketName = docsBucket.bucketName;
  }
}
