#!/usr/bin/env bash
# Build the React app and deploy to S3 static website.
# Requires: frontend/.env with VITE_API_URL, BUCKET, REGION (see .env.example).
# Run from repo root: ./frontend/deploy.sh   or from frontend: ./deploy.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ ! -f .env ]]; then
  echo "Missing .env. Copy .env.example to .env and set VITE_API_URL, BUCKET, REGION." >&2
  exit 1
fi

set -a
source .env
set +a

if [[ -z "$BUCKET" || -z "$REGION" ]]; then
  echo "Set BUCKET and REGION in .env." >&2
  exit 1
fi

echo "Building..."
npm run build

echo "Deploying to s3://$BUCKET (region $REGION)..."

# Create bucket if it doesn't exist
if ! aws s3api head-bucket --bucket "$BUCKET" 2>/dev/null; then
  echo "Creating bucket $BUCKET..."
  aws s3api create-bucket --bucket "$BUCKET" --region "$REGION"
fi

# Static website hosting (SPA: index + error → index.html)
aws s3 website "s3://$BUCKET" --index-document index.html --error-document index.html

# Allow public read for website
aws s3api put-public-access-block --bucket "$BUCKET" --public-access-block-configuration \
  BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false

aws s3api put-bucket-policy --bucket "$BUCKET" --policy '{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::'"$BUCKET"'/*"
    }
  ]
}'

# Upload build output
aws s3 sync dist/ "s3://$BUCKET/" --delete

# index.html: no-cache so updates are visible
aws s3 cp "s3://$BUCKET/index.html" "s3://$BUCKET/index.html" \
  --content-type "text/html" --cache-control "no-cache" --metadata-directive REPLACE

echo "Done. Website URL: http://$BUCKET.s3-website-$REGION.amazonaws.com"
