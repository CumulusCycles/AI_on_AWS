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