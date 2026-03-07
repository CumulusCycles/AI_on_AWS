variable "aws_region" {
  description = "AWS region to deploy all resources"
  type        = string
  default     = "us-east-1"
}

variable "prefix" {
  description = "Resource name prefix — change to avoid collisions if deploying multiple stacks"
  type        = string
  default     = "ai-agent-insure"
}

variable "foundation_model" {
  description = "Bedrock foundation model ID for the agent (use one that supports direct invocation, e.g. Claude 3 Haiku like 6_*)"
  type        = string
  default     = "anthropic.claude-3-haiku-20240307-v1:0"
}

variable "embedding_model" {
  description = "Bedrock embedding model ID for the knowledge base"
  type        = string
  default     = "amazon.titan-embed-text-v2:0"
}

variable "embedding_dimensions" {
  description = "Embedding vector dimensions — must match the embedding model (Titan V2 = 1024)"
  type        = number
  default     = 1024
}
