# ---------------------------------------------------------------------------
# Bedrock Agent
# ---------------------------------------------------------------------------

resource "awscc_bedrock_agent" "main" {
  agent_name                  = "${var.prefix}-assistant"
  description                 = "AI Agent Insure claims and policy assistant — powered by Amazon Bedrock Agents"
  agent_resource_role_arn     = aws_iam_role.agent.arn
  foundation_model            = var.foundation_model
  instruction                 = local.agent_instruction
  idle_session_ttl_in_seconds = 1800

  # Attach the Knowledge Base
  knowledge_bases = [{
    description          = "AI Agent Insure product and coverage knowledge base"
    knowledge_base_id    = awscc_bedrock_knowledge_base.main.knowledge_base_id
    knowledge_base_state = "ENABLED"
  }]

  # Attach the action group
  action_groups = [{
    action_group_name  = "ClaimsPolicyActions"
    description        = "Submit claims, check claim status, look up policies, and get coverage summaries"
    action_group_state = "ENABLED"

    action_group_executor = {
      lambda = aws_lambda_function.claims.arn
    }

    api_schema = {
      payload = local.openapi_schema
    }
  }]

  # Prepare the agent automatically after creation/update
  auto_prepare = true

  # Required: allows destroy to succeed even when the alias still exists.
  # Without this, terraform destroy fails with "agent has active aliases".
  skip_resource_in_use_check_on_delete = true

  depends_on = [
    aws_iam_role_policy.agent_policy,
    aws_lambda_permission.bedrock_agent,
    awscc_bedrock_knowledge_base.main,
    null_resource.kb_sync,
  ]
}

# ---------------------------------------------------------------------------
# Agent alias — stable reference for the app to use
# ---------------------------------------------------------------------------

resource "awscc_bedrock_agent_alias" "live" {
  agent_id         = awscc_bedrock_agent.main.agent_id
  agent_alias_name = "live"
  description      = "Production alias"

  depends_on = [awscc_bedrock_agent.main]
}
