# ---------------------------------------------------------------------------
# Package the Lambda source into a zip
# ---------------------------------------------------------------------------

data "archive_file" "claims_lambda" {
  type        = "zip"
  source_file = "${path.module}/../action_groups/claims_lambda.py"
  output_path = "${path.module}/.terraform/claims_lambda.zip"
}

# ---------------------------------------------------------------------------
# Lambda function
# ---------------------------------------------------------------------------

resource "aws_lambda_function" "claims" {
  function_name    = "${var.prefix}-claims"
  description      = "AI Agent Insure — Bedrock Agent action group handler"
  role             = aws_iam_role.lambda.arn
  runtime          = "python3.12"
  handler          = "claims_lambda.lambda_handler"
  filename         = data.archive_file.claims_lambda.output_path
  source_code_hash = data.archive_file.claims_lambda.output_base64sha256
  timeout          = 30
  memory_size      = 256

  environment {
    variables = {
      CLAIMS_TABLE   = aws_dynamodb_table.claims.name
      POLICIES_TABLE = aws_dynamodb_table.policies.name
    }
  }

  depends_on = [aws_iam_role_policy.lambda_dynamodb]
}

# ---------------------------------------------------------------------------
# Allow Bedrock Agent to invoke the Lambda
# ---------------------------------------------------------------------------

resource "aws_lambda_permission" "bedrock_agent" {
  statement_id  = "AllowBedrockAgentInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.claims.function_name
  principal     = "bedrock.amazonaws.com"
  source_arn    = "arn:aws:bedrock:${local.region}:${local.account_id}:agent/*"
}
