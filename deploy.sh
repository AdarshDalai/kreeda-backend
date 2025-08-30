#!/bin/bash
# Kreeda Backend Deployment Script
# Deploys to AWS using only Always Free tier services

set -e

echo "🏏 Deploying Kreeda Backend to AWS Always Free Services..."

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

# Get AWS account ID and region
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=$(aws configure get region)
AWS_REGION=${AWS_REGION:-us-east-1}

echo "📍 Deploying to region: $AWS_REGION"
echo "🆔 Account ID: $AWS_ACCOUNT_ID"

# Create S3 bucket for SAM deployment (if it doesn't exist)
BUCKET_NAME="kreeda-deployment-${AWS_ACCOUNT_ID}"
if ! aws s3 ls "s3://${BUCKET_NAME}" 2>&1 > /dev/null; then
    echo "📦 Creating S3 bucket for deployment..."
    aws s3 mb "s3://${BUCKET_NAME}" --region "$AWS_REGION"
else
    echo "📦 Using existing S3 bucket: ${BUCKET_NAME}"
fi

# Build the application
echo "🔨 Building application..."
sam build --template sam.yaml

# Deploy to AWS
echo "🚀 Deploying to AWS..."
sam deploy \
    --template sam.yaml \
    --stack-name kreeda-backend \
    --s3-bucket "${BUCKET_NAME}" \
    --capabilities CAPABILITY_IAM \
    --parameter-overrides \
        GoogleClientId="${GOOGLE_CLIENT_ID:-placeholder}" \
        GoogleClientSecret="${GOOGLE_CLIENT_SECRET:-placeholder}" \
        AppleClientId="${APPLE_CLIENT_ID:-placeholder}" \
        AppleTeamId="${APPLE_TEAM_ID:-placeholder}" \
        AppleKeyId="${APPLE_KEY_ID:-placeholder}" \
        ApplePrivateKey="${APPLE_PRIVATE_KEY:-placeholder}" \
    --region "$AWS_REGION"

# Get outputs
echo "📋 Getting deployment outputs..."
API_URL=$(aws cloudformation describe-stacks \
    --stack-name kreeda-backend \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
    --output text \
    --region "$AWS_REGION")

CLOUDFRONT_URL=$(aws cloudformation describe-stacks \
    --stack-name kreeda-backend \
    --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontUrl`].OutputValue' \
    --output text \
    --region "$AWS_REGION")

USER_POOL_ID=$(aws cloudformation describe-stacks \
    --stack-name kreeda-backend \
    --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
    --output text \
    --region "$AWS_REGION")

echo ""
echo "✅ Deployment completed successfully!"
echo ""
echo "🌐 API Gateway URL: $API_URL"
echo "🌐 CloudFront URL: $CLOUDFRONT_URL"
echo "🔐 Cognito User Pool ID: $USER_POOL_ID"
echo ""
echo "📚 API Documentation: ${API_URL}docs"
echo "💓 Health Check: ${API_URL}health"
echo ""
echo "⚠️  Remember to:"
echo "   1. Update OAuth client IDs in Cognito console"
echo "   2. Configure Route 53 for custom domain (optional)"
echo "   3. Set up SSL certificate in Certificate Manager"
echo ""
echo "🎉 Kreeda Backend is now live on AWS Always Free tier!"
