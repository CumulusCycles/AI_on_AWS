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