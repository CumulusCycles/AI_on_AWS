import os
import subprocess
from pathlib import Path
from aws_cdk import BundlingOptions, DockerImage
from constructs import Construct


def nodejs_lambda_bundling(
    entry: str,
    output_dir: str = "dist",
) -> BundlingOptions:
    """
    Create bundling options for Node.js/TypeScript Lambda functions.
    
    Args:
        entry: Path to the Lambda function directory
        output_dir: Output directory name within the Lambda directory
    
    Returns:
        BundlingOptions for CDK Lambda construct
    """
    lambda_dir = Path(entry)
    package_json = lambda_dir / "package.json"
    
    return BundlingOptions(
        image=DockerImage.from_registry("public.ecr.aws/sam/build-nodejs20.x:latest"),
        command=[
            "bash",
            "-c",
            f"""
            cd /asset-input &&
            export NPM_CONFIG_CACHE=/tmp/.npm &&
            npm ci --cache /tmp/.npm &&
            npm run build &&
            cp -r node_modules /asset-output/ &&
            cp -r {output_dir}/* /asset-output/ 2>/dev/null || true &&
            cp package.json /asset-output/
            """,
        ],
    )