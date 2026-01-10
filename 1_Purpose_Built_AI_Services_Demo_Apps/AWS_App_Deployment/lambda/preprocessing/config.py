"""
Configuration file for the preprocessing Lambda function.
Sets up AWS service clients (Comprehend, Rekognition, Lambda) and loads environment variables.
"""
import os
import logging
import boto3
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')
load_dotenv('.env')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# AWS clients
region = os.getenv('REGION', 'us-east-1')
comprehend_client = boto3.client('comprehend', region_name=region)
rekognition_client = boto3.client('rekognition', region_name=region)
lambda_client = boto3.client('lambda', region_name=region)

# Configuration
AGGREGATE_LAMBDA_FUNCTION_NAME = os.getenv('AGGREGATE_LAMBDA_FUNCTION_NAME')
AGGREGATE_LAMBDA_LOCAL_URL = os.getenv('AGGREGATE_LAMBDA_LOCAL_URL')