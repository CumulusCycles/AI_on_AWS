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