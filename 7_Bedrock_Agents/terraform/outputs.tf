output "agent_id" {
  description = "Bedrock Agent ID — set as AGENT_ID in backend/.env"
  value       = awscc_bedrock_agent.main.agent_id
}

output "agent_alias_id" {
  description = "Bedrock Agent alias ID — set as AGENT_ALIAS_ID in backend/.env"
  value       = awscc_bedrock_agent_alias.live.agent_alias_id
}

output "knowledge_base_id" {
  description = "Bedrock Knowledge Base ID"
  value       = awscc_bedrock_knowledge_base.main.knowledge_base_id
}

output "lambda_arn" {
  description = "Claims action group Lambda ARN"
  value       = aws_lambda_function.claims.arn
}

output "docs_bucket" {
  description = "S3 bucket containing KB source documents"
  value       = aws_s3_bucket.docs.id
}

output "vector_bucket" {
  description = "S3 vector bucket name"
  value       = aws_s3vectors_vector_bucket.kb.vector_bucket_name
}

output "claims_table" {
  description = "DynamoDB claims table name"
  value       = aws_dynamodb_table.claims.name
}

output "policies_table" {
  description = "DynamoDB policies table name"
  value       = aws_dynamodb_table.policies.name
}
