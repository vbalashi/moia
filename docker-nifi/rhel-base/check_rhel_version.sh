#!/bin/bash

# Create logs directory if it doesn't exist
mkdir -p logs

# Path to your Dockerfile (relative to where the script is)
DOCKERFILE="Dockerfile-redhat"
LOG_FILE="logs/rhel_version_check_$(date +%Y%m%d_%H%M%S).log"

# Extract current version from Dockerfile
CURRENT_VERSION=$(grep "IMAGE_TAG=" "$DOCKERFILE" | cut -d'=' -f2 | tr -d '"' | tr -d ' ')
REGISTRY_URL="https://registry.access.redhat.com/v2/ubi8/ubi/tags/list"

# Get latest version from registry and log the raw output
RAW_JSON=$(curl -s "$REGISTRY_URL")
echo "Raw JSON from registry: $RAW_JSON" > "$LOG_FILE"

LATEST_VERSION=$(echo "$RAW_JSON" | jq -r '.tags[]' | grep -E '^8\.[0-9]+\-[0-9]+\.[0-9]+$' | sort -V | tail -n1)

echo "RHEL UBI Image Version Check"
echo "=========================="
echo "Current version in Dockerfile: $CURRENT_VERSION"
echo "Latest available version:     $LATEST_VERSION"
echo "--------------------------"

if [ "$CURRENT_VERSION" != "$LATEST_VERSION" ]; then
    echo "STATUS: Update available!"
else
    echo "STATUS: Using latest version"
fi

echo "Log file created: $LOG_FILE"