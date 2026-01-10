# CDK Setup Guide

This guide will help you set up AWS CDK (Python) for the Claim Processor application. This includes CDK CLI installation, project initialization, and Lambda bundling helpers.

## Overview

We'll set up:
- AWS CDK CLI installation
- CDK Python project initialization
- Python virtual environment
- CDK dependencies
- Lambda bundling helpers for Python and Node.js/TypeScript

## Prerequisites

- Python 3.12 or higher
- Node.js and npm (for CDK CLI)
- AWS CLI configured with credentials
- Docker (required for Lambda bundling)
- Access to AWS services: S3, DynamoDB, Lambda, API Gateway, IAM, CloudWatch
- Basic knowledge of AWS CDK (Python)

**Why Docker is Required:** AWS Lambda functions run on Linux. When bundling Lambda functions with dependencies (especially Python packages with native extensions like NumPy or pandas), CDK needs to install and compile these dependencies for the Linux platform. Docker containers provide a Linux build environment that matches Lambda's runtime, ensuring binary compatibility. Without Docker, dependencies compiled on macOS or Windows won't work correctly in Lambda's Linux environment.

## Step-by-Step Setup

### Step 1: Install AWS CDK CLI

If you haven't already, install the AWS CDK CLI globally:

```bash
npm install -g aws-cdk
```

Verify installation:
```bash
cdk --version
```

### Step 2: Create CDK Directory Structure

Create the CDK app directory in the project root:

```bash
cd 1_Purpose_Built_AI_Services_Demo_Apps/AWS_App_Deployment
mkdir -p cdk
cd cdk
```

### Step 3: Initialize CDK Python Project

Initialize a new CDK Python project:

```bash
cdk init app --language python
```

This creates:
- `app.py` - CDK app entry point
- `cdk.json` - CDK configuration
- `requirements.txt` - Python dependencies
- `source.bat` / `setup.py` - Python package setup
- `cdk/` directory - Your stack code
- `.venv/` directory - Python virtual environment (created automatically)

### Step 4: Install CDK Dependencies

**Note:** `cdk init` in Step 3 automatically created a virtual environment. You just need to activate it.

Activate the existing Python virtual environment:

```bash
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows
```

You should see `(.venv)` in your terminal prompt, indicating the virtual environment is active.

Install CDK dependencies:

```bash
pip install -r requirements.txt
```

### Step 5: Verify CDK Dependencies

The `cdk init` command should have already created a `requirements.txt` with the necessary dependencies. Verify that `requirements.txt` includes:

```txt
aws-cdk-lib>=2.232.2,<3.0.0
constructs>=10.0.0,<11.0.0
```

**Note:** The version range `>=2.232.2,<3.0.0` allows for minor and patch updates while preventing breaking major version changes. If you see a different version in your `requirements.txt`, that's fine as long as it's CDK v2 (>=2.0.0,<3.0.0).

If you need to install or update:

```bash
pip install -r requirements.txt
```

The `aws-cdk-lib` package includes all the constructs we need, including:
- S3 (buckets and deployment)
- DynamoDB
- Lambda
- API Gateway
- IAM
- And all other AWS services

### Step 6: Create Lambda Bundling Helpers

Create a directory for Lambda bundling utilities:

```bash
mkdir -p cdk/lambda_bundling
```

Create `cdk/lambda_bundling/python_bundler.py`:

**Important:** The bundling command must copy all files and subdirectories (like `services/`), not just root-level `.py` files. The command below uses `cp -r /asset-input/* /asset-output/` to ensure subdirectories are included. If you copy from another source, make sure it includes subdirectories or you'll get `No module named 'services'` errors at runtime.

```python
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
```

Create `cdk/lambda_bundling/nodejs_bundler.py`:

```python
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
```

## What's Next?

Once you've completed these setup steps, proceed to `7_BUILD_CDK_STACK.md` to build the CDK stack definition with all AWS resources.
