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