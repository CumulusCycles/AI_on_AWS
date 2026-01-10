import os
import subprocess
from pathlib import Path
from aws_cdk import BundlingOptions, DockerImage
from constructs import Construct


def python_lambda_bundling(
    entry: str,
    output_dir: str = "dist",
    requirements_file: str = "requirements.txt",
) -> BundlingOptions:
    """
    Create bundling options for Python Lambda functions.
    
    Args:
        entry: Path to the Lambda function directory
        output_dir: Output directory name within the Lambda directory
        requirements_file: Name of requirements file
    
    Returns:
        BundlingOptions for CDK Lambda construct
    """
    lambda_dir = Path(entry)
    requirements_path = lambda_dir / requirements_file
    
    return BundlingOptions(
        image=DockerImage.from_registry("public.ecr.aws/sam/build-python3.12:latest"),
        command=[
            "bash",
            "-c",
            f"""
            cd /asset-input &&
            pip install -r {requirements_file} -t /asset-output --no-cache-dir --platform manylinux2014_x86_64 --only-binary=:all: --python-version 3.12 --implementation cp &&
            cp -r /asset-input/* /asset-output/ 2>/dev/null || true &&
            find /asset-output -type d -name '__pycache__' -exec rm -rf {{}} + 2>/dev/null || true &&
            find /asset-output -type f -name '*.pyc' -delete 2>/dev/null || true
            """,
        ],
    )