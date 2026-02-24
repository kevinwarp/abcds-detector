#!/bin/bash
###########################################################################
#
#  Deploy ABCDs Detector to Google Cloud Run
#
#  Prerequisites:
#    - gcloud CLI installed and authenticated
#    - Docker installed (or use --source flag for Cloud Build)
#    - GCP project with Cloud Run API enabled
#
#  Usage:
#    chmod +x deploy.sh
#    ./deploy.sh
#
#  Environment variables (set before running or update defaults below):
#    GCP_PROJECT_ID    - Your GCP project ID
#    GCP_REGION        - Deployment region (default: us-central1)
#    SERVICE_NAME      - Cloud Run service name (default: abcds-detector)
#
###########################################################################

set -euo pipefail

# Configuration - update these or set as environment variables
GCP_PROJECT_ID="${GCP_PROJECT_ID:?ERROR: Set GCP_PROJECT_ID environment variable}"
GCP_REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="${SERVICE_NAME:-abcds-detector}"
IMAGE_NAME="gcr.io/${GCP_PROJECT_ID}/${SERVICE_NAME}"

echo "=== ABCDs Detector - Cloud Run Deployment ==="
echo "Project:  ${GCP_PROJECT_ID}"
echo "Region:   ${GCP_REGION}"
echo "Service:  ${SERVICE_NAME}"
echo ""

# Set the active project
gcloud config set project "${GCP_PROJECT_ID}"

# Enable required APIs
echo "Enabling required GCP APIs..."
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    videointelligence.googleapis.com \
    aiplatform.googleapis.com \
    storage.googleapis.com \
    kgsearch.googleapis.com

# Build and deploy using Cloud Build (no local Docker needed)
echo ""
echo "Building and deploying to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
    --source . \
    --region "${GCP_REGION}" \
    --platform managed \
    --allow-unauthenticated \
    --memory 2Gi \
    --timeout 600 \
    --set-env-vars "\
PROJECT_ID=${GCP_PROJECT_ID},\
BUCKET_NAME=${BUCKET_NAME:-},\
KNOWLEDGE_GRAPH_API_KEY=${KNOWLEDGE_GRAPH_API_KEY:-},\
BRAND_NAME=${BRAND_NAME:-Google},\
BRAND_VARIATIONS=${BRAND_VARIATIONS:-google},\
BRANDED_PRODUCTS=${BRANDED_PRODUCTS:-},\
BRANDED_PRODUCTS_CATEGORIES=${BRANDED_PRODUCTS_CATEGORIES:-},\
BRANDED_CALL_TO_ACTIONS=${BRANDED_CALL_TO_ACTIONS:-},\
USE_LLMS=${USE_LLMS:-true},\
USE_ANNOTATIONS=${USE_ANNOTATIONS:-true}"

# Get the service URL
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" \
    --region "${GCP_REGION}" \
    --format "value(status.url)")

echo ""
echo "=== Deployment Complete ==="
echo "Service URL: ${SERVICE_URL}"
echo ""
echo "Test with:"
echo "  curl ${SERVICE_URL}/"
echo "  curl -X POST ${SERVICE_URL}/assess"
