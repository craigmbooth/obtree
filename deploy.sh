#!/bin/bash

# Deploy script for OBTree to Google Cloud Run
# This script builds the Docker image and deploys it to Cloud Run

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  OBTree Deployment Script${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if we're in the right directory
if [ ! -f "Dockerfile" ]; then
    echo -e "${RED}Error: Dockerfile not found. Please run this script from the project root.${NC}"
    exit 1
fi

# Check if terraform outputs exist
if [ ! -d "terraform" ]; then
    echo -e "${RED}Error: terraform directory not found.${NC}"
    exit 1
fi

cd terraform

# Get configuration from Terraform outputs
echo -e "${YELLOW}Reading Terraform configuration...${NC}"
PROJECT_ID=$(terraform output -raw project_id 2>/dev/null || echo "")
REGION=$(terraform output -raw region 2>/dev/null || echo "us-central1")
SERVICE_NAME=$(terraform output -raw service_name 2>/dev/null || echo "obtree")
ARTIFACT_REGISTRY=$(terraform output -raw artifact_registry_repository 2>/dev/null || echo "")

# If Terraform outputs fail, try reading from tfvars
if [ -z "$PROJECT_ID" ] && [ -f "terraform.tfvars" ]; then
    echo -e "${YELLOW}Reading from terraform.tfvars...${NC}"
    PROJECT_ID=$(grep '^project_id' terraform.tfvars | cut -d'"' -f2)
    REGION=$(grep '^region' terraform.tfvars | cut -d'"' -f2 || echo "us-central1")
    SERVICE_NAME=$(grep '^service_name' terraform.tfvars | cut -d'"' -f2 || echo "obtree")
fi

if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}Error: Could not determine PROJECT_ID from Terraform.${NC}"
    echo -e "${YELLOW}Please ensure Terraform has been applied successfully.${NC}"
    exit 1
fi

# Construct artifact registry URL if not available from outputs
if [ -z "$ARTIFACT_REGISTRY" ]; then
    ARTIFACT_REGISTRY="${REGION}-docker.pkg.dev/${PROJECT_ID}/${SERVICE_NAME}"
fi

IMAGE_NAME="${ARTIFACT_REGISTRY}/${SERVICE_NAME}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
FULL_IMAGE="${IMAGE_NAME}:${IMAGE_TAG}"

cd ..

echo ""
echo -e "${GREEN}Deployment Configuration:${NC}"
echo -e "  Project ID:      ${YELLOW}${PROJECT_ID}${NC}"
echo -e "  Region:          ${YELLOW}${REGION}${NC}"
echo -e "  Service:         ${YELLOW}${SERVICE_NAME}${NC}"
echo -e "  Image:           ${YELLOW}${FULL_IMAGE}${NC}"
echo ""

# Confirm deployment
read -p "Do you want to proceed with deployment? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Deployment cancelled.${NC}"
    exit 0
fi

echo ""
echo -e "${GREEN}Step 1: Building and pushing Docker image...${NC}"
echo -e "${YELLOW}This may take several minutes...${NC}"
echo ""

# Build and push using Cloud Build
gcloud builds submit \
    --project="${PROJECT_ID}" \
    --tag="${FULL_IMAGE}" \
    --timeout=10m

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Docker build failed.${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}Step 2: Deploying to Cloud Run...${NC}"
echo ""

# Deploy to Cloud Run
gcloud run services update "${SERVICE_NAME}" \
    --project="${PROJECT_ID}" \
    --region="${REGION}" \
    --image="${FULL_IMAGE}" \
    --quiet

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Cloud Run deployment failed.${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Deployment Successful! 🎉${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Get the service URL
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" \
    --project="${PROJECT_ID}" \
    --region="${REGION}" \
    --format='value(status.url)' 2>/dev/null)

if [ -n "$SERVICE_URL" ]; then
    echo -e "${GREEN}Your application is live at:${NC}"
    echo -e "${YELLOW}${SERVICE_URL}${NC}"
    echo ""
fi

echo -e "${GREEN}Image deployed:${NC} ${FULL_IMAGE}"
echo ""
echo -e "${YELLOW}Note: Database migrations are run automatically on container startup.${NC}"
echo ""
