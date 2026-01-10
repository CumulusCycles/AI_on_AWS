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