# ---------------------------------------------------------------------------
# Claims table — stores submitted claims
# ---------------------------------------------------------------------------

resource "aws_dynamodb_table" "claims" {
  name         = "${var.prefix}-claims"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "claim_id"

  attribute {
    name = "claim_id"
    type = "S"
  }
}

# ---------------------------------------------------------------------------
# Policies table — stores policy records
# ---------------------------------------------------------------------------

resource "aws_dynamodb_table" "policies" {
  name         = "${var.prefix}-policies"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "policy_id"

  attribute {
    name = "policy_id"
    type = "S"
  }
}

# ---------------------------------------------------------------------------
# Seed demo policies
# ---------------------------------------------------------------------------

resource "aws_dynamodb_table_item" "policy_001" {
  table_name = aws_dynamodb_table.policies.name
  hash_key   = aws_dynamodb_table.policies.hash_key

  item = jsonencode({
    policy_id      = { S = "POL-001" }
    holder         = { S = "Acme AI Corp" }
    product        = { S = "Agentic AI Liability Insurance" }
    coverage_limit = { N = "5000000" }
    deductible     = { N = "25000" }
    status         = { S = "active" }
    expiry         = { S = local.expiry_180 }
  })

  lifecycle {
    # Don't overwrite if a claim adjuster has updated the item
    ignore_changes = [item]
  }
}

resource "aws_dynamodb_table_item" "policy_002" {
  table_name = aws_dynamodb_table.policies.name
  hash_key   = aws_dynamodb_table.policies.hash_key

  item = jsonencode({
    policy_id      = { S = "POL-002" }
    holder         = { S = "NeuralOps Ltd" }
    product        = { S = "AI Infrastructure & Operations Protection" }
    coverage_limit = { N = "2000000" }
    deductible     = { N = "10000" }
    status         = { S = "active" }
    expiry         = { S = local.expiry_90 }
  })

  lifecycle {
    ignore_changes = [item]
  }
}

resource "aws_dynamodb_table_item" "policy_003" {
  table_name = aws_dynamodb_table.policies.name
  hash_key   = aws_dynamodb_table.policies.hash_key

  item = jsonencode({
    policy_id      = { S = "POL-003" }
    holder         = { S = "RoboFleet Systems" }
    product        = { S = "Autonomous Systems & Robotics Coverage" }
    coverage_limit = { N = "10000000" }
    deductible     = { N = "50000" }
    status         = { S = "active" }
    expiry         = { S = local.expiry_270 }
  })

  lifecycle {
    ignore_changes = [item]
  }
}
