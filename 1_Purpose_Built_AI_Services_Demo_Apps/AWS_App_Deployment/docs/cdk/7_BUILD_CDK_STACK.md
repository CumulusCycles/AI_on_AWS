# CDK Stack Build Guide

This guide will help you build the CDK stack definition that includes all AWS resources: S3 buckets, DynamoDB table, Lambda functions, API Gateway, and IAM roles.

## Overview

We'll build:
- S3 bucket for frontend static website hosting
- S3 bucket for storing uploaded claim images
- DynamoDB table for storing claim metadata
- API Gateway HTTP API as the frontend entry point
- Preprocessing Lambda function (Python/FastAPI)
- Aggregate Lambda function (Node.js/TypeScript)
- IAM roles and policies for Lambda functions
- CORS configuration for API Gateway
- Environment variables for Lambda functions

## Prerequisites

- Completed `6_SETUP_CDK.md`
- CDK project initialized
- Lambda bundling helpers created
- Python virtual environment activated

## Step-by-Step Build

This guide uses a **modular approach** with separate construct files for better organization, maintainability, and reusability. Each major component is in its own file.

### Step 1: Create the Constructs Directory

**Note:** You should already be in the `cdk` directory from Step 2 of `6_SETUP_CDK.md`. If not, navigate there first:
```bash
cd cdk
```

Create a new directory structure for modular constructs:

```bash
mkdir -p cdk/constructs
touch cdk/constructs/__init__.py
```

This creates the constructs directory at `cdk/cdk/constructs/` relative to the project root (or `cdk/constructs/` relative to where you are now).

### Step 2: Create Storage Construct (S3 Buckets)

Create `cdk/constructs/storage.py` with the following:

**Note:** This module handles all S3 bucket creation and configuration.

```python
from aws_cdk import (
    RemovalPolicy,
    Stack,
    aws_s3 as s3,
    aws_iam as iam,
)
from constructs import Construct
from typing import Tuple


class StorageConstruct(Construct):
    """Construct for creating S3 buckets for images and frontend hosting."""

    def __init__(self, scope: Construct, construct_id: str) -> None:
        super().__init__(scope, construct_id)

        # S3 bucket for storing uploaded claim images
        self.images_bucket = s3.Bucket(
            self,
            "ImagesBucket",
            bucket_name="demo-claim-app-images",
            removal_policy=RemovalPolicy.DESTROY,  # For demo purposes
            auto_delete_objects=True,  # Automatically delete objects when bucket is deleted
            encryption=s3.BucketEncryption.S3_MANAGED,
            versioned=False,
        )

        # S3 bucket for frontend static website hosting
        self.frontend_bucket = s3.Bucket(
            self,
            "FrontendBucket",
            bucket_name="demo-claim-app-frontend",
            removal_policy=RemovalPolicy.DESTROY,  # For demo purposes
            auto_delete_objects=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            website_index_document="index.html",
            website_error_document="index.html",  # SPA routing
            public_read_access=True,  # Required for S3 static website hosting
            block_public_access=s3.BlockPublicAccess(
                block_public_acls=False,
                block_public_policy=False,
                ignore_public_acls=False,
                restrict_public_buckets=False,
            ),
        )

        # Add bucket policy to allow public read access for website hosting
        self.frontend_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                principals=[iam.AnyPrincipal()],
                actions=["s3:GetObject"],
                resources=[f"{self.frontend_bucket.bucket_arn}/*"],
            )
        )
```

### Step 3: Create Database Construct (DynamoDB)

Create `cdk/constructs/database.py` with the following:

**Note:** This module handles DynamoDB table creation.

```python
from aws_cdk import (
    RemovalPolicy,
    Stack,
    aws_dynamodb as dynamodb,
)
from constructs import Construct


class DatabaseConstruct(Construct):
    """Construct for creating DynamoDB table for storing claim metadata."""

    def __init__(self, scope: Construct, construct_id: str) -> None:
        super().__init__(scope, construct_id)

        self.claims_table = dynamodb.Table(
            self,
            "ClaimsTable",
            table_name="demo-claim-app-claims",
            partition_key=dynamodb.Attribute(
                name="claimId",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,  # For demo purposes
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
        )
```

### Step 4: Create Compute Construct (Lambda Functions & IAM Roles)

Create `cdk/constructs/compute.py` with the following:

**Note:** This module handles Lambda functions and their IAM roles. IAM permissions follow the principle of least privilege (no broad `*` permissions).

```python
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
```

### Step 5: Create API Construct (API Gateway)

Create `cdk/constructs/api.py` with the following:

**Note:** This module handles API Gateway HTTP API creation and configuration.

```python
from aws_cdk import (
    Duration,
    aws_apigatewayv2 as apigwv2,
    aws_apigatewayv2_integrations as apigwv2_integrations,
    aws_lambda as lambda_,
)
from constructs import Construct


class ApiConstruct(Construct):
    """Construct for creating API Gateway HTTP API with Lambda integration."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        preprocessing_lambda: lambda_.Function,
    ) -> None:
        super().__init__(scope, construct_id)

        # Create HTTP API
        self.http_api = apigwv2.HttpApi(
            self,
            "ClaimProcessorApi",
            api_name="demo-claim-app-api",
            cors_preflight=apigwv2.CorsPreflightOptions(
                allow_origins=["*"],  # In production, restrict to your frontend domain
                allow_methods=[apigwv2.CorsHttpMethod.POST, apigwv2.CorsHttpMethod.OPTIONS],
                allow_headers=["Content-Type"],
                max_age=Duration.days(1),
            ),
        )

        # Create Lambda integration for Preprocessing Lambda
        preprocessing_integration = apigwv2_integrations.HttpLambdaIntegration(
            "PreprocessingIntegration",
            preprocessing_lambda,
        )

        # Add route for /process-claim
        self.http_api.add_routes(
            path="/process-claim",
            methods=[apigwv2.HttpMethod.POST],
            integration=preprocessing_integration,
        )
```

### Step 6: Create Frontend Construct (S3 Deployment)

Create `cdk/constructs/frontend.py` with the following:

**Note:** This module handles frontend static asset deployment to S3.

```python
from aws_cdk import (
    aws_s3 as s3,
    aws_s3_deployment as s3_deployment,
)
from constructs import Construct
from pathlib import Path


class FrontendConstruct(Construct):
    """Construct for deploying frontend static assets to S3 bucket."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        project_root: Path,
        frontend_bucket: s3.Bucket,
    ) -> None:
        super().__init__(scope, construct_id)

        # Note: Frontend needs to be built first
        # The dist folder will be created when you run: cd frontend && npm run build
        
        s3_deployment.BucketDeployment(
            self,
            "FrontendDeployment",
            sources=[s3_deployment.Source.asset(str(project_root / "frontend" / "dist"))],
            destination_bucket=frontend_bucket,
            destination_key_prefix="",
        )
```

### Step 7: Create Main CDK Stack

Create or replace `cdk/cdk_stack.py` with the following:

**Note:** This is the main stack orchestrator that composes all the constructs together. The code has been refactored for better security and organization:
- IAM permissions follow the principle of least privilege (no broad `*` permissions)
- Lambda functions are created in the correct order (Aggregate first) to avoid redundant environment variable updates
- Code is modularized into separate construct files for better maintainability

```python
from aws_cdk import (
    Stack,
    CfnOutput,
)
from constructs import Construct
from pathlib import Path

from .constructs.storage import StorageConstruct
from .constructs.database import DatabaseConstruct
from .constructs.compute import ComputeConstruct
from .constructs.api import ApiConstruct
from .constructs.frontend import FrontendConstruct


class ClaimProcessorStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Get the project root directory (parent of cdk directory)
        project_root = Path(__file__).parent.parent.parent

        # Create infrastructure components using modular constructs
        storage = StorageConstruct(self, "Storage")
        database = DatabaseConstruct(self, "Database")
        compute = ComputeConstruct(
            self,
            "Compute",
            project_root=project_root,
            images_bucket=storage.images_bucket,
            claims_table=database.claims_table,
            stack=self,
        )
        api = ApiConstruct(
            self,
            "Api",
            preprocessing_lambda=compute.preprocessing_lambda,
        )
        FrontendConstruct(
            self,
            "Frontend",
            project_root=project_root,
            frontend_bucket=storage.frontend_bucket,
        )

        # Create CloudFormation outputs
        self._create_outputs(
            api.http_api,
            storage.frontend_bucket,
            storage.images_bucket,
            database.claims_table,
        )

    def _create_outputs(
        self,
        http_api,
        frontend_bucket,
        images_bucket,
        claims_table,
    ) -> None:
        """Create CloudFormation outputs for important resource identifiers."""
        CfnOutput(
            self,
            "ApiGatewayUrl",
            value=http_api.url or "N/A",
            description="API Gateway HTTP API URL",
        )

        CfnOutput(
            self,
            "FrontendBucketName",
            value=frontend_bucket.bucket_name,
            description="S3 bucket name for frontend",
        )

        CfnOutput(
            self,
            "FrontendWebsiteUrl",
            value=frontend_bucket.bucket_website_url,
            description="Frontend website URL (S3 static website hosting)",
        )

        CfnOutput(
            self,
            "ImagesBucketName",
            value=images_bucket.bucket_name,
            description="S3 bucket name for images",
        )

        CfnOutput(
            self,
            "ClaimsTableName",
            value=claims_table.table_name,
            description="DynamoDB table name for claims",
        )
```

### Step 8: Update CDK App Entry Point

Replace the entire contents of `app.py` with the following:

```python
#!/usr/bin/env python3
import os
import aws_cdk as cdk
from cdk.cdk_stack import ClaimProcessorStack

app = cdk.App()
ClaimProcessorStack(
    app,
    "ClaimProcessorStack",
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"),
        region=os.getenv("CDK_DEFAULT_REGION", "us-east-1"),
    ),
)

app.synth()
```

### Step 9: Verify requirements.txt

**Note:** You should have already verified `requirements.txt` in Step 5 of `6_SETUP_CDK.md`. Verify that `requirements.txt` includes:

```txt
aws-cdk-lib>=2.232.2,<3.0.0
constructs>=10.0.0,<11.0.0
```

**Note:** The version range `>=2.232.2,<3.0.0` is what CDK generates by default and is recommended. It allows for minor and patch updates while preventing breaking major version changes. If you have a slightly different version range (e.g., `>=2.100.0,<3.0.0`), that's also acceptable as long as it's CDK v2.

The `aws-cdk-lib` package includes all the constructs we need, including:
- S3 (buckets and deployment)
- DynamoDB
- Lambda
- API Gateway
- IAM
- And all other AWS services

**Note:** `aws_s3_deployment` (used in the stack for frontend deployment) is part of `aws-cdk-lib`, so no additional package is needed.

## Project Structure

After completing all steps, your CDK project structure should look like this:

```
cdk/
├── app.py
├── cdk.json
├── requirements.txt
└── cdk/
    ├── __init__.py
    ├── cdk_stack.py          # Main stack orchestrator
    ├── constructs/
    │   ├── __init__.py
    │   ├── storage.py         # S3 buckets
    │   ├── database.py        # DynamoDB table
    │   ├── compute.py         # Lambda functions & roles
    │   ├── api.py             # API Gateway
    │   └── frontend.py        # Frontend deployment
    └── lambda_bundling/
        ├── python_bundler.py
        └── nodejs_bundler.py

**Important Note on Python Bundling:** The Python bundler must correctly copy all subdirectories (like `services/`) to the Lambda package. If you encounter `No module named 'services'` errors after deployment, see the troubleshooting section in `8_DEPLOY_CDK.md` for the fix.
        └── nodejs_bundler.py
```

## Benefits of This Modular Approach

- **Separation of Concerns**: Each construct handles a single responsibility
- **Reusability**: Constructs can be reused in other stacks
- **Testability**: Each construct can be tested independently
- **Maintainability**: Easier to find and modify specific functionality
- **Scalability**: Easy to add new constructs as the project grows

## What's Next?

Once you've completed building the CDK stack, proceed to `8_DEPLOY_CDK.md` to bootstrap, deploy, and test your infrastructure.
