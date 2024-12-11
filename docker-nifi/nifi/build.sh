#!/bin/bash

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
    echo "  --no-copy        Use existing components directory without copying"
    echo "  --force-copy     Force copy components without asking"
    echo
    echo "Examples:"
    echo "  $0 v1                     # Build NiFi 1.28.1 with default NAR files"
    echo "  $0 v1 --no-nar            # Build NiFi 1.28.1 without NAR files"
    echo "  $0 v1 --nar-dir=custom    # Build NiFi 1.28.1 with custom NAR directory"
    echo "  $0 v1 --force-copy        # Build NiFi 1.28.1 and force copy components"
}

# Show help if no arguments or -h/--help
if [ $# -eq 0 ] || [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    print_help
    exit 0
fi

# Get base image tag from Docker images
BASE_IMAGE_NAME="rhel-base"
BASE_IMAGE_TAG=$(docker images "${BASE_IMAGE_NAME}" --format "{{.Tag}}" | sort -V | tail -n1)
if [ -z "$BASE_IMAGE_TAG" ]; then
    echo "Error: No ${BASE_IMAGE_NAME} images found. Please build the base image first."
    exit 1
fi

# Default values
NIFI_COMPONENTS_BASE_DIR="/mnt/hgfs/MOIA/nifi"
LOCAL_COMPONENTS_DIR="./nifi-components"
NAR_EXTENSIONS_DIR="extensions-24.4"  # Default NAR extensions directory
USE_NAR=true  # Default to using NAR files

# Default values for copy behavior
COPY_MODE="ask"  # Can be "ask", "no-copy", or "force-copy"

# Parse additional arguments
while [[ $# -gt 1 ]]; do
    case "$2" in
        --no-nar)
            USE_NAR=false
            NAR_EXTENSIONS_DIR="extensions-empty"
            shift
            ;;
        --nar-dir=*)
            NAR_EXTENSIONS_DIR="${2#*=}"
            shift
            ;;
        --no-copy)
            COPY_MODE="no-copy"
            shift
            ;;
        --force-copy)
            COPY_MODE="force-copy"
            shift
            ;;
    esac
done

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

# Check if local components directory exists
if [ -d "${LOCAL_COMPONENTS_DIR}" ]; then
    echo "Components directory ${LOCAL_COMPONENTS_DIR} exists"
    echo "Contents:"
    ls -la "${LOCAL_COMPONENTS_DIR}" | awk '{print $9}' | grep -v '^$' | sed 's/^/  /'
    echo

    case $COPY_MODE in
        "no-copy")
            echo "Proceeding with existing files (--no-copy specified)..."
            ;;
        "force-copy")
            echo "Copying new files (--force-copy specified)..."
            cp -r "${NIFI_COMPONENTS_BASE_DIR}"/* "${LOCAL_COMPONENTS_DIR}/"
            ;;
        "ask")
            echo "Select an option:"
            echo "1) Proceed without copying (use existing files)"
            echo "2) Copy new files (overwrite existing)"
            echo "3) Exit"
            read -p "Enter choice [1-3]: " choice
            
            case $choice in
                1)
                    echo "Proceeding with existing files..."
                    ;;
                2)
                    echo "Copying new files..."
                    cp -r "${NIFI_COMPONENTS_BASE_DIR}"/* "${LOCAL_COMPONENTS_DIR}/"
                    ;;
                3)
                    echo "Build cancelled by user"
                    exit 0
                    ;;
                *)
                    echo "Invalid choice. Exiting."
                    exit 1
                    ;;
            esac
            ;;
    esac
else
    # Create local components directory and copy files
    echo "Copying NiFi components..."
    mkdir -p "${LOCAL_COMPONENTS_DIR}"
    cp -r "${NIFI_COMPONENTS_BASE_DIR}"/* "${LOCAL_COMPONENTS_DIR}/"
fi

# If using NAR files, ensure the extensions directory exists
if [ "$USE_NAR" = true ]; then
    if [ ! -d "${NIFI_COMPONENTS_BASE_DIR}/${NAR_EXTENSIONS_DIR}" ]; then
        echo "Error: NAR extensions directory '${NAR_EXTENSIONS_DIR}' not found in ${NIFI_COMPONENTS_BASE_DIR}"
        exit 1
    fi
    # Replace the default extensions directory with the specified one
    rm -rf "${LOCAL_COMPONENTS_DIR}/extensions"
    cp -r "${NIFI_COMPONENTS_BASE_DIR}/${NAR_EXTENSIONS_DIR}" "${LOCAL_COMPONENTS_DIR}/extensions"
else
    # Create empty extensions directory
    rm -rf "${LOCAL_COMPONENTS_DIR}/extensions"
    mkdir -p "${LOCAL_COMPONENTS_DIR}/extensions"
fi

# Verify the copy was successful
if [ ! -d "${LOCAL_COMPONENTS_DIR}/sh" ]; then
    echo "Error: Failed to copy required components. Check permissions and paths."
    exit 1
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
        -t "nifi:${NIFI_VERSION}${TAG_SUFFIX}" \
        -f Dockerfile-nifi \
        .
fi

echo "Build completed: nifi:${NIFI_VERSION}${TAG_SUFFIX}"
echo "Note: Build artifacts are preserved in ${LOCAL_COMPONENTS_DIR}"