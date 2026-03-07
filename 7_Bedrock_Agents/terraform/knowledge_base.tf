# ---------------------------------------------------------------------------
# S3 docs bucket — stores the KB source documents
# ---------------------------------------------------------------------------

resource "aws_s3_bucket" "docs" {
  bucket        = "${var.prefix}-docs-${local.account_id}"
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "docs" {
  bucket                  = aws_s3_bucket.docs.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Upload all KB documents from assets/ (excluding agent_instruction.md)
resource "aws_s3_object" "kb_docs" {
  for_each = local.kb_doc_files

  bucket = aws_s3_bucket.docs.id
  key    = each.key
  source = each.value
  etag   = filemd5(each.value)

  content_type = "text/markdown"
}

# ---------------------------------------------------------------------------
# S3 vector bucket + index — stores the vector embeddings
# ---------------------------------------------------------------------------

resource "aws_s3vectors_vector_bucket" "kb" {
  vector_bucket_name = "${var.prefix}-vectors-${local.account_id}"
}

resource "aws_s3vectors_index" "kb" {
  vector_bucket_name = aws_s3vectors_vector_bucket.kb.vector_bucket_name
  index_name         = "${var.prefix}-index"
  data_type          = "float32"
  dimension          = var.embedding_dimensions
  distance_metric    = "cosine"

  metadata_configuration {
    non_filterable_metadata_keys = ["AMAZON_BEDROCK_TEXT"]
  }
}

# ---------------------------------------------------------------------------
# IAM propagation delay — Bedrock must be able to assume the KB role before
# creating the KB. New IAM roles can take 5–15s to propagate; wait so the
# first terraform apply succeeds without a second run.
# ---------------------------------------------------------------------------

resource "null_resource" "kb_iam_propagate" {
  triggers = {
    role_arn = aws_iam_role.kb.arn
  }

  provisioner "local-exec" {
    command = "echo 'Waiting for IAM role propagation...' && sleep 20"
  }

  depends_on = [aws_iam_role_policy.kb_policy]
}

# ---------------------------------------------------------------------------
# Bedrock Knowledge Base (awscc — supports S3_VECTORS)
# ---------------------------------------------------------------------------

resource "awscc_bedrock_knowledge_base" "main" {
  name        = "${var.prefix}-kb"
  description = "AI Agent Insure product and coverage knowledge base"
  role_arn    = aws_iam_role.kb.arn

  storage_configuration = {
    type = "S3_VECTORS"
    s3_vectors_configuration = {
      index_name        = aws_s3vectors_index.kb.index_name
      vector_bucket_arn = aws_s3vectors_vector_bucket.kb.vector_bucket_arn
    }
  }

  knowledge_base_configuration = {
    type = "VECTOR"
    vector_knowledge_base_configuration = {
      embedding_model_arn = "arn:aws:bedrock:${local.region}::foundation-model/${var.embedding_model}"
      embedding_model_configuration = {
        bedrock_embedding_model_configuration = {
          dimensions          = var.embedding_dimensions
          embedding_data_type = "FLOAT32"
        }
      }
    }
  }

  depends_on = [
    null_resource.kb_iam_propagate,
    aws_iam_role_policy.kb_policy,
    aws_s3vectors_index.kb,
  ]
}

# ---------------------------------------------------------------------------
# Data source — points the KB at the docs S3 bucket
# ---------------------------------------------------------------------------

resource "awscc_bedrock_data_source" "docs" {
  name              = "${var.prefix}-docs"
  description       = "AI Agent Insure product documents"
  knowledge_base_id = awscc_bedrock_knowledge_base.main.knowledge_base_id

  data_source_configuration = {
    type = "S3"
    s3_configuration = {
      bucket_arn = aws_s3_bucket.docs.arn
    }
  }

  vector_ingestion_configuration = {
    chunking_configuration = {
      chunking_strategy = "FIXED_SIZE"
      fixed_size_chunking_configuration = {
        max_tokens         = 512
        overlap_percentage = 20
      }
    }
  }

  depends_on = [
    awscc_bedrock_knowledge_base.main,
    aws_s3_object.kb_docs,
  ]
}

# ---------------------------------------------------------------------------
# KB sync — trigger an ingestion job after the data source is created.
#
# Terraform has no native resource for StartIngestionJob, so we use a
# null_resource with a local-exec provisioner. The trigger on the data
# source ID means this re-runs if the data source is ever recreated.
# ---------------------------------------------------------------------------

resource "null_resource" "kb_sync" {
  triggers = {
    data_source_id    = awscc_bedrock_data_source.docs.data_source_id
    knowledge_base_id = awscc_bedrock_knowledge_base.main.knowledge_base_id
  }

  provisioner "local-exec" {
    command = <<-EOT
      set -e
      echo "Starting KB ingestion sync..."
      if ! command -v aws >/dev/null 2>&1; then
        echo "  SKIP: aws CLI not found. Run KB sync manually (see README)."
        exit 0
      fi
      if ! aws bedrock-agent help >/dev/null 2>&1; then
        echo "  SKIP: aws CLI has no 'bedrock-agent'. Update AWS CLI v2 or run sync manually (see README)."
        exit 0
      fi
      JOB=$(aws bedrock-agent start-ingestion-job \
        --knowledge-base-id ${awscc_bedrock_knowledge_base.main.knowledge_base_id} \
        --data-source-id ${awscc_bedrock_data_source.docs.data_source_id} \
        --region ${var.aws_region} \
        --query 'ingestionJob.ingestionJobId' \
        --output text 2>/dev/null) || { echo "  SKIP: start-ingestion-job failed. Run sync manually (see README)."; exit 0; }
      if [ -z "$JOB" ]; then
        echo "  SKIP: No ingestion job ID. Run sync manually (see README)."
        exit 0
      fi
      echo "  Ingestion job started: $JOB"
      echo "  Waiting for sync to complete..."
      for i in $(seq 1 30); do
        STATUS=$(aws bedrock-agent get-ingestion-job \
          --knowledge-base-id ${awscc_bedrock_knowledge_base.main.knowledge_base_id} \
          --data-source-id ${awscc_bedrock_data_source.docs.data_source_id} \
          --ingestion-job-id "$JOB" \
          --region ${var.aws_region} \
          --query 'ingestionJob.status' \
          --output text 2>/dev/null) || STATUS=""
        echo "    Status: $STATUS"
        if [ "$STATUS" = "COMPLETE" ]; then
          echo "  Sync complete."
          exit 0
        fi
        if [ "$STATUS" = "FAILED" ]; then
          echo "  ERROR: Sync job failed."
          exit 1
        fi
        sleep 10
      done
      echo "  ERROR: Sync timed out after 300s."
      exit 1
    EOT
  }

  depends_on = [awscc_bedrock_data_source.docs]
}
