#!/bin/bash

# Get base image tag from rhel-base Dockerfile
BASE_IMAGE_TAG=$(grep 'IMAGE_TAG=' ../rhel-base/Dockerfile-redhat | cut -d'=' -f2)

# Default values
BASE_IMAGE_NAME="rhel-base"
NIFI_COMPONENTS_BASE_DIR="/mnt/hgfs/MOIA/nifi"

# NiFi version configurations
declare -A NIFI_VERSIONS=(
    ["v1"]="1.28.1"
    ["v2"]="2.0.0"
)

declare -A NIFI_URLS=(
    ["v1"]="https://dlcdn.apache.org/nifi/1.28.1/nifi-1.28.1-bin.zip"
    ["v2"]="https://dlcdn.apache.org/nifi/2.0.0/nifi-2.0.0-bin.zip"
)

# Check if version argument is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <v1|v2>"
    echo "Example: $0 v1"
    exit 1
fi

VERSION_KEY=$1
NIFI_VERSION=${NIFI_VERSIONS[$VERSION_KEY]}
NIFI_BINARY_URL=${NIFI_URLS[$VERSION_KEY]}

if [ -z "$NIFI_VERSION" ]; then
    echo "Invalid version key. Use 'v1' or 'v2'"
    exit 1
fi

# Build the Docker image
docker build \
    --build-arg BASE_IMAGE_NAME="${BASE_IMAGE_NAME}" \
    --build-arg BASE_IMAGE_TAG="${BASE_IMAGE_TAG}" \
    --build-arg NIFI_VERSION="${NIFI_VERSION}" \
    --build-arg NIFI_BINARY_URL="${NIFI_BINARY_URL}" \
    --build-arg NIFI_COMPONENTS_BASE_DIR="${NIFI_COMPONENTS_BASE_DIR}" \
    -t "nifi:${NIFI_VERSION}" \
    -f Dockerfile-nifi .

echo "Build completed: nifi:${NIFI_VERSION}" 