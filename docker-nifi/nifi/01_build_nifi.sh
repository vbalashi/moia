#!/bin/bash

# Default values and configurations
LOCAL_COMPONENTS_DIR="./nifi-components"
NAR_EXTENSIONS_DIR="extensions-24.4"  # Default NAR extensions directory
USE_NAR=true  # Default to using NAR files
BASE_IMAGE_NAME="rhel-base"

# NiFi version configurations
declare -A NIFI_VERSIONS=(
    ["v1"]="1.28.1"
    ["v2"]="2.0.0"
)

declare -A NIFI_URLS=(
    ["v1"]="https://dlcdn.apache.org/nifi/1.28.1/nifi-1.28.1-bin.zip"
    ["v2"]="https://dlcdn.apache.org/nifi/2.0.0/nifi-2.0.0-bin.zip"
)

# Help function
print_help() {
    echo "Usage: $0 <version> [options]"
    echo
    echo "Versions:"
    echo "  v1    Build NiFi version 1.28.1"
    echo "  v2    Build NiFi version 2.0.0"
    echo
    echo "Options:"
    echo "  -h, --help       Show this help message"
    echo "  --no-nar         Build without NAR files"
    echo "  --nar-dir=DIR    Specify custom NAR extensions directory (default: extensions-24.4)"
    echo
    echo "Examples:"
    echo "  $0 v1                     # Build NiFi 1.28.1 with default NAR files"
    echo "  $0 v1 --no-nar            # Build NiFi 1.28.1 without NAR files"
    echo "  $0 v1 --nar-dir=custom    # Build NiFi 1.28.1 with custom NAR directory"
}

# Show help if no arguments or -h/--help
if [ $# -eq 0 ] || [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    print_help
    exit 0
fi

# Get base image tag from Docker images
BASE_IMAGE_TAG=$(docker images "${BASE_IMAGE_NAME}" --format "{{.Tag}}" | sort -V | tail -n1)
if [ -z "$BASE_IMAGE_TAG" ]; then
    echo "Error: No ${BASE_IMAGE_NAME} images found. Please build the base image first."
    exit 1
fi

# Parse arguments
VERSION_KEY=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        v1|v2)
            VERSION_KEY="$1"
            shift
            ;;
        --no-nar)
            USE_NAR=false
            NAR_EXTENSIONS_DIR="extensions-empty"
            shift
            ;;
        --nar-dir=*)
            NAR_EXTENSIONS_DIR="${1#*=}"
            shift
            ;;
        -h|--help)
            print_help
            exit 0
            ;;
        *)
            echo "Error: Unknown option $1"
            print_help
            exit 1
            ;;
    esac
done

# Check if version was provided
if [ -z "$VERSION_KEY" ]; then
    echo "Error: Version not specified (v1 or v2)"
    print_help
    exit 1
fi

NIFI_VERSION=${NIFI_VERSIONS[$VERSION_KEY]}
NIFI_BINARY_URL=${NIFI_URLS[$VERSION_KEY]}

if [ -z "$NIFI_VERSION" ]; then
    echo "Invalid version key. Use 'v1' or 'v2'"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if local components directory exists and has required subdirectories
if [ ! -d "${LOCAL_COMPONENTS_DIR}" ]; then
    echo "Error: Local components directory ${LOCAL_COMPONENTS_DIR} does not exist"
    exit 1
fi

# Check for required subdirectories
required_dirs=("sh" "conf" "extensions" "libs")
for dir in "${required_dirs[@]}"; do
    if [ ! -d "${LOCAL_COMPONENTS_DIR}/${dir}" ]; then
        echo "Error: Required directory '${dir}' not found in ${LOCAL_COMPONENTS_DIR}"
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
    echo "Docker Buildx is not installed. Please follow these steps to install it:"
    echo
    echo "For detailed Docker installation instructions, visit: https://docs.docker.com/engine/install/"
    echo
    echo "To install Docker Buildx plugin:"
    echo "1. Install required packages:"
    echo "   sudo apt-get update"
    echo "   sudo apt-get install ca-certificates curl gnupg"
    echo
    echo "2. Add Docker's official GPG key:"
    echo "   sudo install -m 0755 -d /etc/apt/keyrings"
    echo "   curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg"
    echo "   sudo chmod a+r /etc/apt/keyrings/docker.gpg"
    echo
    echo "3. Set up the Docker repository:"
    echo "   echo \\"
    echo "   \"deb [arch=\$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \\"
    echo "   \$(. /etc/os-release && echo \"\$VERSION_CODENAME\") stable\" | \\"
    echo "   sudo tee /etc/apt/sources.list.d/docker.list > /dev/null"
    echo
    echo "4. Update package lists and install Docker Buildx:"
    echo "   sudo apt-get update"
    echo "   sudo apt-get install -y docker-buildx-plugin"
    echo
    exit 1
fi

# Check if installation was successful
if ! docker buildx version &> /dev/null; then
    echo "Docker Buildx is not available. Please install it following the instructions above."
    USE_BUILDX=false
else
    USE_BUILDX=true
    # Ensure we have a builder instance
    if ! docker buildx ls | grep -q "default"; then
        docker buildx create --name builder --use
    fi
fi

# Determine the tag suffix based on NAR usage
TAG_SUFFIX=$([ "$USE_NAR" = true ] && echo "-nar" || echo "-no-nar")

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
        --build-arg NAR_EXTENSIONS_DIR="${NAR_EXTENSIONS_DIR}" \
        -t "nifi:${NIFI_VERSION}${TAG_SUFFIX}" \
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
        --build-arg NAR_EXTENSIONS_DIR="${NAR_EXTENSIONS_DIR}" \
        -t "nifi:${NIFI_VERSION}${TAG_SUFFIX}" \
        -f Dockerfile-nifi \
        .
fi

echo "Build completed: nifi:${NIFI_VERSION}${TAG_SUFFIX}"
echo "Note: Build artifacts are preserved in ${LOCAL_COMPONENTS_DIR}"