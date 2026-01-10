from aws_cdk import (
    Duration,
    Stack,
    aws_lambda as lambda_,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
)
from constructs import Construct
from pathlib import Path
from typing import Tuple

# Import bundling helpers
import sys
# Add parent directory to path to import bundling helpers
_bundler_path = Path(__file__).parent.parent
sys.path.insert(0, str(_bundler_path))
from lambda_bundling.python_bundler import python_lambda_bundling
from lambda_bundling.nodejs_bundler import nodejs_lambda_bundling


class ComputeConstruct(Construct):
    """Construct for creating Lambda functions and their IAM roles."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        project_root: Path,
        images_bucket: s3.Bucket,
        claims_table: dynamodb.Table,
        stack: Stack,
    ) -> None:
        super().__init__(scope, construct_id)

        # Create IAM roles first
        preprocessing_role, aggregate_role = self._create_lambda_roles(
            images_bucket, claims_table
        )

        # Create Lambda functions (Aggregate first so Preprocessing can reference it)
        self.aggregate_lambda = self._create_aggregate_lambda(
            project_root, aggregate_role, images_bucket, claims_table, stack
        )
        self.preprocessing_lambda = self._create_preprocessing_lambda(
            project_root, preprocessing_role, self.aggregate_lambda, stack
        )

        # Grant Preprocessing Lambda permission to invoke Aggregate Lambda
        self._grant_invoke_permission(preprocessing_role, self.aggregate_lambda)

    def _create_lambda_roles(
        self,
        images_bucket: s3.Bucket,
        claims_table: dynamodb.Table,
    ) -> Tuple[iam.Role, iam.Role]:
        """Create IAM roles for Lambda functions with necessary permissions."""
        # IAM role for Preprocessing Lambda
        preprocessing_lambda_role = iam.Role(
            self,
            "PreprocessingLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ],
        )

        # Grant permissions for Comprehend and Rekognition
        preprocessing_lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "comprehend:DetectDominantLanguage",
                    "comprehend:DetectSentiment",
                    "comprehend:DetectEntities",
                    "comprehend:DetectKeyPhrases",
                    "rekognition:DetectLabels",
                    "rekognition:DetectText",
                ],
                resources=["*"],
            )
        )

        # IAM role for Aggregate Lambda
        aggregate_lambda_role = iam.Role(
            self,
            "AggregateLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ],
        )

        # Grant S3 write permissions
        images_bucket.grant_write(aggregate_lambda_role)

        # Grant DynamoDB write permissions
        claims_table.grant_write_data(aggregate_lambda_role)

        return preprocessing_lambda_role, aggregate_lambda_role

    def _create_aggregate_lambda(
        self,
        project_root: Path,
        aggregate_role: iam.Role,
        images_bucket: s3.Bucket,
        claims_table: dynamodb.Table,
        stack: Stack,
    ) -> lambda_.Function:
        """Create Aggregate Lambda function (Node.js/TypeScript)."""
        return lambda_.Function(
            self,
            "AggregateLambda",
            function_name="demo-claim-app-aggregate",
            runtime=lambda_.Runtime.NODEJS_20_X,
            handler="index.handler",
            code=lambda_.Code.from_asset(
                str(project_root / "lambda" / "aggregate"),
                bundling=nodejs_lambda_bundling(
                    entry=str(project_root / "lambda" / "aggregate"),
                ),
            ),
            role=aggregate_role,
            timeout=Duration.seconds(30),
            memory_size=256,  # Minimal memory to keep costs low
            environment={
                "REGION": stack.region,
                "S3_BUCKET_NAME": images_bucket.bucket_name,
                "DYNAMODB_TABLE_NAME": claims_table.table_name,
            },
        )

    def _create_preprocessing_lambda(
        self,
        project_root: Path,
        preprocessing_role: iam.Role,
        aggregate_lambda: lambda_.Function,
        stack: Stack,
    ) -> lambda_.Function:
        """Create Preprocessing Lambda function (Python/FastAPI)."""
        return lambda_.Function(
            self,
            "PreprocessingLambda",
            function_name="demo-claim-app-preprocessing",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="index.handler",
            code=lambda_.Code.from_asset(
                str(project_root / "lambda" / "preprocessing"),
                bundling=python_lambda_bundling(
                    entry=str(project_root / "lambda" / "preprocessing"),
                ),
            ),
            role=preprocessing_role,
            timeout=Duration.seconds(30),
            memory_size=256,  # Minimal memory to keep costs low
            environment={
                "REGION": stack.region,
                "AGGREGATE_LAMBDA_FUNCTION_NAME": aggregate_lambda.function_name,
            },
        )

    def _grant_invoke_permission(
        self,
        preprocessing_role: iam.Role,
        aggregate_lambda: lambda_.Function,
    ) -> None:
        """Grant Preprocessing Lambda permission to invoke Aggregate Lambda."""
        preprocessing_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["lambda:InvokeFunction"],
                resources=[aggregate_lambda.function_arn],
            )
        )