# ---------------------------------------------------------------------------
# Lambda execution role
# ---------------------------------------------------------------------------

resource "aws_iam_role" "lambda" {
  name = "${var.prefix}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "lambda_dynamodb" {
  name = "${var.prefix}-lambda-dynamodb"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:Scan",
      ]
      Resource = [
        aws_dynamodb_table.claims.arn,
        aws_dynamodb_table.policies.arn,
      ]
    }]
  })
}

# ---------------------------------------------------------------------------
# Bedrock Agent role
# ---------------------------------------------------------------------------

resource "aws_iam_role" "agent" {
  name = "${var.prefix}-bedrock-agent-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "bedrock.amazonaws.com" }
      Action    = "sts:AssumeRole"
      Condition = {
        StringEquals = {
          "aws:SourceAccount" = local.account_id
        }
      }
    }]
  })
}

resource "aws_iam_role_policy" "agent_policy" {
  name = "${var.prefix}-bedrock-agent-policy"
  role = aws_iam_role.agent.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"]
        Resource = "arn:aws:bedrock:${local.region}::foundation-model/${var.foundation_model}"
      },
      {
        Effect   = "Allow"
        Action   = "lambda:InvokeFunction"
        Resource = aws_lambda_function.claims.arn
      },
      {
        Effect   = "Allow"
        Action   = ["bedrock:Retrieve", "bedrock:RetrieveAndGenerate"]
        Resource = "arn:aws:bedrock:${local.region}:${local.account_id}:knowledge-base/*"
      },
    ]
  })
}

# ---------------------------------------------------------------------------
# Bedrock Knowledge Base role
# ---------------------------------------------------------------------------

resource "aws_iam_role" "kb" {
  name = "${var.prefix}-kb-role"

  # No Condition — Cloud Control API may not send SourceArn when creating the KB,
  # so Bedrock must be able to assume this role without context conditions.
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "bedrock.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "kb_policy" {
  name = "${var.prefix}-kb-policy"
  role = aws_iam_role.kb.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = ["s3:GetObject", "s3:ListBucket"]
        Resource = [
          aws_s3_bucket.docs.arn,
          "${aws_s3_bucket.docs.arn}/*",
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3vectors:GetIndex",
          "s3vectors:PutVectors",
          "s3vectors:GetVectors",
          "s3vectors:DeleteVectors",
          "s3vectors:QueryVectors",
        ]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = "bedrock:InvokeModel"
        Resource = "arn:aws:bedrock:${local.region}::foundation-model/${var.embedding_model}"
      },
    ]
  })
}
