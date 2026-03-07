terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.84"
    }
    awscc = {
      source  = "hashicorp/awscc"
      version = ">= 1.27"
    }
    archive = {
      source  = "hashicorp/archive"
      version = ">= 2.4"
    }
    null = {
      source  = "hashicorp/null"
      version = ">= 3.2"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# awscc uses the same credentials as aws but needs its own provider block
provider "awscc" {
  region = var.aws_region
}

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id
  region     = data.aws_region.current.id

  # Expiry dates for demo policies (days from now)
  expiry_180 = formatdate("YYYY-MM-DD", timeadd(timestamp(), "${180 * 24}h"))
  expiry_90  = formatdate("YYYY-MM-DD", timeadd(timestamp(), "${90 * 24}h"))
  expiry_270 = formatdate("YYYY-MM-DD", timeadd(timestamp(), "${270 * 24}h"))

  # KB doc files — shared with 4_Bedrock_RAG_KB, no duplication
  kb_doc_files = {
    for f in fileset("${path.module}/../../4_Bedrock_RAG_KB/assets", "*.md") :
    f => "${path.module}/../../4_Bedrock_RAG_KB/assets/${f}"
  }

  agent_instruction = file("${path.module}/../assets/agent_instruction.md")
  openapi_schema    = file("${path.module}/../action_groups/openapi_schema.json")
}
