#!/bin/bash

# Get base image tag from rhel-base Dockerfile
if [ ! -f "../rhel-base/Dockerfile-redhat" ]; then
    echo "Error: rhel-base Dockerfile not found at ../rhel-base/Dockerfile-redhat"
    exit 1
fi

BASE_IMAGE_TAG=$(grep 'IMAGE_TAG=' ../rhel-base/Dockerfile-redhat | cut -d'=' -f2)
if [ -z "$BASE_IMAGE_TAG" ]; then
    echo "Error: Could not extract BASE_IMAGE_TAG from Dockerfile-redhat"
    exit 1
fi

# Default values
BASE_IMAGE_NAME="rhel-base"
NIFI_COMPONENTS_BASE_DIR="/mnt/hgfs/MOIA/nifi"
LOCAL_COMPONENTS_DIR="./nifi-components"

# NiFi version configurations
declare -A NIFI_VERSIONS=(
    ["v1"]="1.28.1"
    ["v2"]="2.0.0"
)

declare -A NIFI_URLS=(
    ["v1"]="https://dlcdn.apache.org/nifi/1.28.1/nifi-1.28.1-bin.zip"
    ["v2"]="https://dlcdn.apache.org/nifi/2.0.0/nifi-2.0.0-bin.zip"
)

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if source directory exists and has required subdirectories
if [ ! -d "${NIFI_COMPONENTS_BASE_DIR}" ]; then
    echo "Error: Source directory ${NIFI_COMPONENTS_BASE_DIR} does not exist"
    exit 1
fi

# Check for required subdirectories
required_dirs=("sh" "conf" "extensions" "libs")
for dir in "${required_dirs[@]}"; do
    if [ ! -d "${NIFI_COMPONENTS_BASE_DIR}/${dir}" ]; then
        echo "Error: Required directory '${dir}' not found in ${NIFI_COMPONENTS_BASE_DIR}"
        exit 1
    fi
done

# Check if Dockerfile-nifi exists
if [ ! -f "Dockerfile-nifi" ]; then
    echo "Error: Dockerfile-nifi not found in current directory"
    exit 1
fi

# Install Docker Buildx plugin if not present
echo "Checking Docker Buildx..."
if ! docker buildx version &> /dev/null; then
    echo "Installing Docker Buildx plugin..."
    sudo apt-get update && sudo apt-get install -y docker-buildx-plugin
fi

# Check if installation was successful
if ! docker buildx version &> /dev/null; then
    echo "Failed to install Docker Buildx. Falling back to regular docker build."
    USE_BUILDX=false
else
    USE_BUILDX=true
    # Ensure we have a builder instance
    if ! docker buildx ls | grep -q "default"; then
        docker buildx create --name builder --use
    fi
fi

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

# Remove existing directory if it exists
rm -rf "${LOCAL_COMPONENTS_DIR}"

# Create local components directory and copy files
echo "Copying NiFi components..."
mkdir -p "${LOCAL_COMPONENTS_DIR}"
cp -r "${NIFI_COMPONENTS_BASE_DIR}"/* "${LOCAL_COMPONENTS_DIR}/"

# Verify the copy was successful
if [ ! -d "${LOCAL_COMPONENTS_DIR}/sh" ]; then
    echo "Error: Failed to copy required components. Check permissions and paths."
    exit 1
fi

# Build the Docker image
if [ "$USE_BUILDX" = true ]; then
    echo "Building with Docker Buildx..."
    docker buildx build \
        --platform linux/amd64 \
        --build-arg BASE_IMAGE_NAME="${BASE_IMAGE_NAME}" \
        --build-arg BASE_IMAGE_TAG="${BASE_IMAGE_TAG}" \
        --build-arg NIFI_VERSION="${NIFI_VERSION}" \
        --build-arg NIFI_BINARY_URL="${NIFI_BINARY_URL}" \
        --build-arg NIFI_COMPONENTS_BASE_DIR="${LOCAL_COMPONENTS_DIR}" \
        -t "nifi:${NIFI_VERSION}" \
        --load \
        -f Dockerfile-nifi \
        .
else
    echo "Building with regular Docker..."
    docker build \
        --build-arg BASE_IMAGE_NAME="${BASE_IMAGE_NAME}" \
        --build-arg BASE_IMAGE_TAG="${BASE_IMAGE_TAG}" \
        --build-arg NIFI_VERSION="${NIFI_VERSION}" \
        --build-arg NIFI_BINARY_URL="${NIFI_BINARY_URL}" \
        --build-arg NIFI_COMPONENTS_BASE_DIR="${LOCAL_COMPONENTS_DIR}" \
        -t "nifi:${NIFI_VERSION}" \
        -f Dockerfile-nifi \
        .
fi

echo "Build completed: nifi:${NIFI_VERSION}"
echo "Note: Build artifacts are preserved in ${LOCAL_COMPONENTS_DIR}"