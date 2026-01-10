# CDK Deployment Guide

This guide will help you deploy the CDK stack to AWS, test the deployed application, and clean up resources when done.

## Overview

We'll cover:
- CDK bootstrapping (first time only)
- Building the frontend for deployment
- Synthesizing and reviewing the stack
- Deploying to AWS
- Updating frontend API URL
- Testing the deployed application
- Viewing resources in AWS Console
- Cleaning up (destroying the stack)

## Prerequisites

- Completed `6_SETUP_CDK.md`
- Completed `7_BUILD_CDK_STACK.md`
- AWS CLI configured with credentials
- Docker running (required for Lambda bundling)
- Python virtual environment activated

## Step-by-Step Deployment

**Important:** All commands assume you start from the project root directory (`AWS_App_Deployment/`). Navigate there first if needed:
```bash
cd /path/to/AWS_App_Deployment
```

Commands will navigate into `cdk` or `frontend` subdirectories as needed. Make sure you're in the correct directory for each command (as noted in each step).

### Step 1: Build Frontend for Deployment (First Build)

**Important:** Build the frontend first because `cdk bootstrap` (Step 2) will validate the stack, which requires the `frontend/dist` directory to exist.

**Note:** Start from the project root directory (`AWS_App_Deployment/`).

Build the frontend for the first time:

```bash
cd frontend
rm -rf dist
npm run build
```

This creates the `dist` folder that CDK will deploy to S3.

**Note:** This first build will use `http://localhost:8000` as the API URL (the default in `api.ts`). This is fine for the initial deployment. After we get the API Gateway URL from the deployment, we'll rebuild the frontend with the correct URL in Step 6.

### Step 2: Bootstrap CDK (First Time Only)

**⚠️ Important: Docker must be running!** 

Before proceeding, ensure Docker Desktop (or Docker daemon) is running. CDK uses Docker to bundle Lambda functions, and `cdk bootstrap` will validate the stack by running `cdk synth` internally, which requires Docker.

**Why Docker is needed:** AWS Lambda runs on Linux. When CDK bundles your Lambda functions, it needs to install Python/Node.js dependencies in a Linux environment to ensure binary compatibility. Docker containers provide this Linux build environment. Without Docker running, CDK cannot create Lambda deployment packages with correctly compiled native dependencies.

**Verify Docker is running:**
```bash
docker ps
```

If this command fails or shows an error, start Docker Desktop and wait for it to fully initialize before continuing.

If this is your first time using CDK in this AWS account/region, bootstrap it:

**Note:** You should be in the `cdk` directory (where `app.py` and `cdk.json` are located). If you're in the project root or `frontend` directory, navigate to `cdk` first.

From project root:
```bash
cd cdk
cdk bootstrap aws://ACCOUNT-ID/REGION
```

Replace `ACCOUNT-ID` with your AWS account ID and `REGION` with your region (e.g., `us-east-1`).

Or let CDK detect it automatically:

```bash
cdk bootstrap
```

**Note:** 
- Bootstrapping only needs to be done once per AWS account/region combination. It creates an S3 bucket and IAM roles that CDK uses for deployments.
- `cdk bootstrap` validates the stack by running `cdk synth` internally, which is why the frontend must be built first.
- Docker must be running for `cdk bootstrap` to succeed (it bundles Lambda functions during validation).

### Step 3: Synthesize CDK Stack (Dry Run)

**⚠️ Reminder: Docker must be running!**

`cdk synth` bundles Lambda functions using Docker. Ensure Docker is running before proceeding.

Test that your CDK stack synthesizes correctly:

**Note:** Make sure you're in the `cdk` directory (where `app.py` and `cdk.json` are located).

From project root:
```bash
cd cdk
cdk synth
```

Or if already in the `cdk` directory:
```bash
cdk synth
```

This generates CloudFormation templates without deploying. Review any warnings or errors.

**What to look for:**
- No syntax errors
- All Lambda functions have correct paths
- All environment variables are set
- IAM roles have correct permissions

**Note:** Make sure you're in the `cdk` directory (where `app.py` and `cdk.json` are located) when running CDK commands.

### Step 4: Review Stack Diff

See what changes will be made:

**Note:** Make sure you're in the `cdk` directory (where `app.py` and `cdk.json` are located).

```bash
cdk diff
```

This shows the differences between your current stack (if deployed) and the new stack definition.

**Note:** 
- If this is your first deployment, `cdk diff` will show all resources that will be created.
- Review the output carefully to ensure it matches your expectations.

### Step 5: Deploy the Stack

Deploy the stack to AWS:

**Note:** Make sure you're in the `cdk` directory (where `app.py` and `cdk.json` are located).

```bash
cdk deploy
```

CDK will prompt you to confirm the IAM changes. Review them and type `y` to proceed.

This will:
1. Build and bundle Lambda functions (requires Docker)
2. Create S3 buckets
3. Create DynamoDB table
4. Create Lambda functions
5. Create API Gateway
6. Deploy frontend to S3
7. Set up IAM roles and policies

**Note:** The first deployment may take 10-15 minutes. Subsequent deployments are faster.

**Important:** After deployment, CDK will output several values including the API Gateway URL. **Save this URL** - you'll need it in the next step.

**⚠️ CRITICAL STEP:** If you see errors like `POST https://your_api_gateway_url/process-claim net::ERR_NAME_NOT_RESOLVED` in your browser console after opening the deployed frontend, this means the frontend was built without the API Gateway URL. You MUST complete Step 6 below to fix this.

### Step 6: Update Frontend API URL and Redeploy

**📝 Note:** This step demonstrates a manual rebuild-and-redeploy approach for demo purposes. In real-world production scenarios, a better approach would be to use a runtime configuration file (e.g., `config.json`) stored in S3 that the frontend fetches at runtime. This eliminates the need to rebuild and redeploy the frontend when the API Gateway URL changes. The CDK stack would automatically write the API Gateway URL to this config file during deployment, and the frontend would read it dynamically. This approach is more maintainable, avoids unnecessary rebuilds, and is commonly used in production environments.

**⚠️ REQUIRED:** After your first deployment, you MUST rebuild the frontend with the API Gateway URL from Step 5 output and redeploy. The initial frontend build uses a placeholder or localhost URL, which won't work with the deployed API Gateway.

After deployment, CDK outputs the API Gateway URL. You need to rebuild the frontend with this URL and redeploy the stack.

**Important:** You must rebuild the frontend AND redeploy the CDK stack so the updated frontend files are uploaded to S3.

**Option 1: Update .env.production and rebuild**

1. Create or update `frontend/.env.production`:

```bash
# Replace YOUR_API_GATEWAY_URL with the actual URL from CDK output
VITE_API_URL=https://YOUR_API_GATEWAY_URL
```

2. Rebuild the frontend:

**Note:** Make sure you're in the `frontend` directory.

From project root:
```bash
cd frontend
rm -rf dist
npm run build
```

3. Redeploy the CDK stack (this uploads the new frontend build to S3):

**Note:** Make sure you're in the `cdk` directory.

From project root:
```bash
cd cdk
cdk deploy
```

**Option 2: Set environment variable during build**

1. Rebuild the frontend with the API Gateway URL:

**Note:** Make sure you're in the `frontend` directory.

From project root:
```bash
cd frontend
rm -rf dist
VITE_API_URL=https://YOUR_API_GATEWAY_URL npm run build
```

2. Redeploy the CDK stack:

**Note:** Make sure you're in the `cdk` directory.

From project root:
```bash
cd cdk
cdk deploy
```

**Note:** The API Gateway URL will look something like:
```
https://yphjx9dod4.execute-api.us-east-1.amazonaws.com
```

**Important:** 
- Copy the entire URL from the CDK output (it will be displayed as `ClaimProcessorStack.ApiGatewayUrl = https://...`)
- Make sure to remove any trailing slash (`/`) if present
- The URL should end with `.amazonaws.com` or `.amazonaws.com/` (but remove the trailing slash when setting it)

**Why redeploy?** The CDK stack includes a `BucketDeployment` that uploads the frontend `dist` folder to S3. After rebuilding the frontend with the correct API URL, you must redeploy so CDK uploads the updated files.

### Step 7: Test Deployed Application

**⚠️ IMPORTANT:** Make sure you completed Step 6 (rebuild frontend with API Gateway URL and redeploy) before testing, or the frontend will not be able to communicate with the API Gateway.

1. **Get the frontend URL** from CDK outputs or AWS Console:
   - Look for the `FrontendWebsiteUrl` output
   - Or find it in S3 Console: `demo-claim-app-frontend` bucket → Properties → Static website hosting

2. **Open the frontend** in your browser

3. **Check browser console** (F12 or Cmd+Option+I):
   - Open the Console tab
   - If you see errors about `your_api_gateway_url` or `ERR_NAME_NOT_RESOLVED`, you need to complete Step 6 first
   - After fixing, the API calls should show the correct API Gateway URL

4. **Submit a test claim**:
   - Fill in the claim description
   - Upload an accident photo
   - Click "Submit Claim"

5. **Verify the flow**:
   - Request goes to API Gateway (check browser Network tab - should show your API Gateway URL)
   - Preprocessing Lambda processes the claim (calls Comprehend and Rekognition)
   - Aggregate Lambda stores data in S3 and DynamoDB
   - Results are returned to frontend
   - JSON response appears in the right panel

6. **Check CloudWatch logs** if there are any errors:
   - CloudWatch → Log groups → Look for Lambda function logs
   - If you don't see any logs, it means the request isn't reaching Lambda (likely a frontend URL issue)

### Step 8: View Resources in AWS Console

Verify all resources were created correctly:

**S3 Buckets:**
- `demo-claim-app-frontend` - Frontend static website
- `demo-claim-app-images` - Uploaded claim images

**DynamoDB:**
- `demo-claim-app-claims` - Claim metadata table

**Lambda Functions:**
- `demo-claim-app-preprocessing` - Preprocessing Lambda
- `demo-claim-app-aggregate` - Aggregate Lambda

**API Gateway:**
- HTTP API: `demo-claim-app-api`
- Route: `POST /process-claim`

**CloudWatch:**
- Check logs for both Lambda functions
- Look for any errors or warnings

### Step 9: Clean Up (Destroy Stack)

When you're done testing, destroy the stack to avoid ongoing costs:

**Note:** Make sure you're in the `cdk` directory (where `app.py` and `cdk.json` are located).

```bash
cdk destroy
```

CDK will prompt you to confirm. Type `y` to proceed.

This will:
- Delete all resources created by the stack
- Empty and delete S3 buckets (if `auto_delete_objects=True`)
- Delete DynamoDB table
- Delete Lambda functions
- Delete API Gateway
- Delete IAM roles and policies

**⚠️ Warning:** This permanently deletes all data. Make sure you're done testing.

**Note:** Bootstrapping resources (S3 bucket, IAM roles) are not deleted by `cdk destroy`. They remain for future CDK deployments in this account/region.

## Quick Fix: Frontend API URL Error

**If you already deployed and are seeing `ERR_NAME_NOT_RESOLVED` or `your_api_gateway_url` in browser console:**

1. **Get your API Gateway URL** from the last CDK deployment output (look for `ClaimProcessorStack.ApiGatewayUrl`)
   - Example: `https://yphjx9dod4.execute-api.us-east-1.amazonaws.com`
   
2. **Rebuild frontend with the correct URL** (from project root):
   ```bash
   cd frontend
   rm -rf dist
   VITE_API_URL=https://YOUR_ACTUAL_API_GATEWAY_URL npm run build
   ```
   Replace `YOUR_ACTUAL_API_GATEWAY_URL` with your actual URL (no trailing slash)

3. **Redeploy CDK stack** (from project root):
   ```bash
   cd ../cdk
   cdk deploy
   ```

4. **Wait for deployment to complete**, then refresh your browser and test again

See Step 6 below for more details and alternative methods.

## Troubleshooting

### Lambda Bundling Issues

If Lambda bundling fails:
- **Docker not running**: Ensure Docker Desktop (or Docker daemon) is running. Docker is required because Lambda functions run on Linux, and CDK needs a Linux environment to compile native dependencies (like NumPy, pandas) for the correct platform. Verify with `docker ps`.
- **Docker not accessible**: Verify with `docker ps`. If it fails, start Docker Desktop and wait for it to fully initialize.
- **Missing dependencies**: Check that all dependencies are listed in `requirements.txt` or `package.json`
- **Path issues**: Verify file paths in `cdk_stack.py` are correct relative to project root

### Python Lambda Import Error: "No module named 'services'"

**Error:** If you see `Runtime.ImportModuleError: Unable to import module 'index': No module named 'services'` in CloudWatch logs when the Preprocessing Lambda runs:

**Problem:** The Python Lambda bundler in `cdk/cdk/lambda_bundling/python_bundler.py` is not correctly packaging subdirectories like `services/`. 

**Root Cause:** Line 35 in `python_bundler.py` uses:
```bash
cp -r /asset-input/*.py /asset-output/ 2>/dev/null || true
```
This only copies root-level `.py` files and does not include the `services/` subdirectory or other directories.

**Fix:** Update line 35 in `cdk/cdk/lambda_bundling/python_bundler.py` to copy the entire directory structure:

**Change this:**
```bash
cp -r /asset-input/*.py /asset-output/ 2>/dev/null || true &&
```

**To this:**
```bash
cp -r /asset-input/* /asset-output/ 2>/dev/null || true &&
find /asset-output -type f -name '*.py' -path '*/__pycache__/*' -delete 2>/dev/null || true &&
```

Or, to be more selective and only copy Python files and directories:
```bash
cp -r /asset-input/*.py /asset-output/ 2>/dev/null || true &&
cp -r /asset-input/services /asset-output/ 2>/dev/null || true &&
cp -r /asset-input/config.py /asset-output/ 2>/dev/null || true &&
```

**After making the fix:**
1. Save the file
2. Redeploy the CDK stack: `cdk deploy`
3. Test the Lambda function again

**Note:** The bundler should copy all necessary Python files and subdirectories (like `services/`) to `/asset-output` so they're available at runtime in the Lambda environment.

### Frontend Not Loading

- **S3 website hosting**: Check that website hosting is enabled in S3 bucket properties
- **Index.html exists**: Verify `index.html` exists in the bucket root
- **Bucket policy**: If using S3 website hosting directly, you may need to configure bucket policy for public read access
- **CORS**: Check browser console for CORS errors

**Note:** For production, consider using CloudFront in front of S3 for better performance and HTTPS. This is not included in this guide.

### API Gateway CORS Issues

- **CORS configuration**: Verify CORS is configured in API Gateway (should be set in `cdk_stack.py`)
- **Frontend URL**: Check that frontend is using the correct API Gateway URL
- **Browser console**: Review browser console for specific CORS error messages
- **Preflight requests**: Ensure OPTIONS method is allowed in CORS configuration

### Lambda Timeout

- **Increase timeout**: Update `timeout=Duration.seconds(30)` in `cdk_stack.py` if needed
- **CloudWatch logs**: Check CloudWatch logs for Lambda functions to identify bottlenecks
- **IAM permissions**: Verify Lambda has proper IAM permissions for all AWS services it uses

### Deployment Fails

- **IAM permissions**: Ensure your AWS credentials have permissions to create all resources
- **Resource limits**: Check if you've hit any AWS service limits (e.g., Lambda function count)
- **Region availability**: Verify all services are available in your chosen region
- **CDK version**: Ensure CDK CLI and library versions are compatible

### Frontend API URL Not Working

**Common Error:** If you see `POST https://your_api_gateway_url/process-claim net::ERR_NAME_NOT_RESOLVED` or `Failed to fetch` errors in the browser console:

1. **This means the frontend wasn't built with the API Gateway URL** - Complete Step 6 above to rebuild and redeploy
2. **Get the API Gateway URL** from the CDK deployment output (look for `ApiGatewayUrl = https://...`)
3. **Rebuild the frontend** with the correct URL:
   ```bash
   cd frontend
   rm -rf dist
   VITE_API_URL=https://YOUR_ACTUAL_API_GATEWAY_URL npm run build
   ```
   Replace `YOUR_ACTUAL_API_GATEWAY_URL` with the actual URL from CDK output (e.g., `https://yphjx9dod4.execute-api.us-east-1.amazonaws.com`)
4. **Redeploy the CDK stack** to upload the updated frontend:
   ```bash
   cd ../cdk
   cdk deploy
   ```
5. **Wait for deployment to complete** and refresh your browser
6. **Verify in browser console** - the API calls should now go to the correct URL

**Other troubleshooting:**
- **Environment variable**: Verify `VITE_API_URL` is set correctly in `.env.production`
- **Rebuild required**: After updating `.env.production`, you must rebuild: `rm -rf dist && npm run build`
- **Redeploy required**: After rebuilding, redeploy: `cdk deploy`
- **URL format**: Ensure the API Gateway URL doesn't have a trailing slash (remove trailing `/` if present)
- **Browser cache**: Clear your browser cache or do a hard refresh (Cmd+Shift+R on Mac, Ctrl+Shift+R on Windows)

## Next Steps

After successful deployment:

1. **Monitor CloudWatch logs** for errors and performance issues
2. **Set up CloudWatch alarms** for Lambda errors (optional)
3. **Consider CloudFront** for frontend (better performance, HTTPS, custom domain)
4. **Set up custom domain** for API Gateway (optional)
5. **Implement error handling** and retry logic
6. **Add input validation** and rate limiting
7. **Set up CI/CD pipeline** for automated deployments (optional)
8. **Configure monitoring and alerting** (optional)

## Cost Optimization Tips

To keep AWS costs low:

- **Lambda memory**: Already set to minimal (256 MB)
- **DynamoDB**: Using on-demand billing (pay per request)
- **S3**: Only pay for storage and requests
- **API Gateway**: Pay per API call
- **CloudWatch logs**: Consider setting retention policies to reduce log storage costs
- **Destroy stack**: Always destroy the stack when not in use to avoid ongoing costs

**Estimated costs for this demo app (light usage):**
- Lambda: ~$0.20 per million requests
- DynamoDB: ~$1.25 per million requests
- S3: ~$0.023 per GB storage + $0.005 per 1,000 requests
- API Gateway: ~$1.00 per million requests

Total for light testing: **< $1-2 per month** (assuming minimal usage)

