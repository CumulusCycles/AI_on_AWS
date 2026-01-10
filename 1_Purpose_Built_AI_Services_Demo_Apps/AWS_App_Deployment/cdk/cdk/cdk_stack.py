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