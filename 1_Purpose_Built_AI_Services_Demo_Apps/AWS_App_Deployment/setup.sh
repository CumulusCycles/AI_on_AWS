#!/bin/bash

# Setup script to create all files and folders required for the AWS App Deployment project
# This script creates the directory structure and empty files as specified in the .md guides

set -e  # Exit on error

echo "Creating project structure..."

# ============================================================================
# FRONTEND STRUCTURE
# ============================================================================
echo "Creating frontend structure..."

# Frontend root directory
mkdir -p frontend/src/components
mkdir -p frontend/src/lib

# Frontend configuration files
touch frontend/tailwind.config.js
touch frontend/postcss.config.js
touch frontend/.env.example
touch frontend/.env.local
touch frontend/.gitignore

# Frontend source files
touch frontend/src/types.ts
touch frontend/src/lib/validation.ts
touch frontend/src/lib/api.ts
touch frontend/src/components/SingleFileUpload.tsx
touch frontend/src/components/ClaimForm.tsx

# ============================================================================
# PREPROCESSING LAMBDA STRUCTURE
# ============================================================================
echo "Creating preprocessing Lambda structure..."

# Preprocessing Lambda directories
mkdir -p lambda/preprocessing/services

# Preprocessing Lambda files
touch lambda/preprocessing/requirements.txt
touch lambda/preprocessing/.env.local.example
touch lambda/preprocessing/.env.local
touch lambda/preprocessing/config.py
touch lambda/preprocessing/index.py
touch lambda/preprocessing/run_local.py
touch lambda/preprocessing/.gitignore

# Preprocessing Lambda services
touch lambda/preprocessing/services/__init__.py
touch lambda/preprocessing/services/comprehend.py
touch lambda/preprocessing/services/rekognition.py
touch lambda/preprocessing/services/lambda_invoker.py

# ============================================================================
# AGGREGATE LAMBDA STRUCTURE
# ============================================================================
echo "Creating aggregate Lambda structure..."

# Aggregate Lambda directories
mkdir -p lambda/aggregate/services
mkdir -p lambda/aggregate/middleware
mkdir -p lambda/aggregate/routes
mkdir -p lambda/aggregate/handlers

# Aggregate Lambda configuration files
# touch lambda/aggregate/package.json
touch lambda/aggregate/tsconfig.json
touch lambda/aggregate/.env.local.example
touch lambda/aggregate/.env.local
touch lambda/aggregate/.gitignore

# Aggregate Lambda source files
touch lambda/aggregate/types.ts
touch lambda/aggregate/config.ts
touch lambda/aggregate/swagger.ts
touch lambda/aggregate/index.ts
touch lambda/aggregate/run_local.ts

# Aggregate Lambda services
touch lambda/aggregate/services/__init__.ts
touch lambda/aggregate/services/s3.ts
touch lambda/aggregate/services/dynamodb.ts
touch lambda/aggregate/services/aggregator.ts

# Aggregate Lambda middleware
touch lambda/aggregate/middleware/logging.ts
touch lambda/aggregate/middleware/cors.ts

# Aggregate Lambda routes
touch lambda/aggregate/routes/health.ts
touch lambda/aggregate/routes/aggregate.ts

# Aggregate Lambda handlers
touch lambda/aggregate/handlers/lambda.ts

# ============================================================================
# CDK STRUCTURE
# ============================================================================
echo "Creating CDK structure..."

mkdir -p cdk

# # CDK directories
# mkdir -p cdk/cdk/constructs
# mkdir -p cdk/cdk/lambda_bundling

# # CDK configuration files
# touch cdk/app.py
# touch cdk/cdk.json
# touch cdk/requirements.txt
# touch cdk/setup.py

# # CDK stack files
# touch cdk/cdk/__init__.py
# touch cdk/cdk/cdk_stack.py

# # CDK constructs
# touch cdk/cdk/constructs/__init__.py
# touch cdk/cdk/constructs/storage.py
# touch cdk/cdk/constructs/database.py
# touch cdk/cdk/constructs/compute.py
# touch cdk/cdk/constructs/api.py
# touch cdk/cdk/constructs/frontend.py

# # CDK Lambda bundling
# touch cdk/cdk/lambda_bundling/python_bundler.py
# touch cdk/cdk/lambda_bundling/nodejs_bundler.py

echo ""
echo "✅ Project structure created successfully!"
echo ""
echo "Created:"
echo "  - Frontend structure (components, lib, config files)"
echo "  - Preprocessing Lambda structure (services, config files)"
echo "  - Aggregate Lambda structure (services, middleware, routes, handlers)"
# echo "  - CDK structure (constructs, bundling helpers)"
echo "  - CDK dir"
echo ""
echo "Note: All files are empty. Follow the .md guides in docs/ to populate them."
