# NiFi Docker Image

This directory contains the build configuration and management scripts for Apache NiFi Docker images based on RHEL.

## Supported Versions

- NiFi 1.x (currently 1.28.1)
- NiFi 2.x (currently 2.0.0)

## Scripts Overview

### 1. Build Script (`01_build_nifi.sh`)

Builds NiFi Docker images for different versions with optional NAR file support.

```bash
# Build NiFi v1 with default NAR files
./01_build_nifi.sh v1

# Build NiFi v2 without NAR files
./01_build_nifi.sh v2 --no-nar

# Build with custom NAR directory
./01_build_nifi.sh v1 --nar-dir=custom
```

Prerequisites:
- Docker with Buildx plugin installed
- Base RHEL image (`rhel-base`) must be available locally
- Required directory structure (see below)

### 2. Retag Script (`02_retag_nifi_images.py`)

Retags local NiFi images with target registry tags.

```bash
# Dry run mode
python 02_retag_nifi_images.py

# Execute mode and remove old tags
python 02_retag_nifi_images.py --execute --remove-old
```

Required Environment Variables:
- `TARGET_REPO`: Target repository URL (e.g., 'registry.example.com/org')
- `IMAGE_NAMES`: Comma-separated list of image names to retag (default: 'nifi')
- `IMAGE_TAGS`: Comma-separated list of tags to retag (default: '*')

### 3. Push Script (`push_nifi_images.py`)

Pushes NiFi Docker images to a target registry with progress tracking.

```bash
# Dry run mode
python push_nifi_images.py

# Execute mode with specific tags
python push_nifi_images.py --execute --tags "1.28.1-nar,2.0.0-nar"
```

Required Environment Variables:
- `TARGET_REPO`: Target repository URL (e.g., 'registry.example.com/org')
- `REGISTRY_URL`: Registry URL (optional, extracted from TARGET_REPO if not provided)
- `GITLAB_TOKEN`: GitLab registry authentication token
- `IMAGE_NAMES`: Comma-separated list of image names to push (default: 'nifi')
- `IMAGE_TAGS`: Comma-separated list of tags to push (default: '*')

## Directory Structure

The following directories should exist in your NIFI_COMPONENTS_BASE_DIR:
```
./nifi-components/
├── sh/         # Shell scripts
├── conf/       # NiFi configuration files
├── extensions/ # NAR files and extensions
└── libs/       # Additional libraries
```

## Image Tags

Images are tagged with their version number and NAR status:
- `nifi:1.28.1-nar`    # NiFi 1.28.1 with NAR files
- `nifi:1.28.1-no-nar` # NiFi 1.28.1 without NAR files
- `nifi:2.0.0-nar`     # NiFi 2.0.0 with NAR files
- `nifi:2.0.0-no-nar`  # NiFi 2.0.0 without NAR files

## Workflow Example

1. Build the image:
   ```bash
   ./01_build_nifi.sh v1
   ```

2. Retag for your registry:
   ```bash
   export TARGET_REPO="registry.example.com/org"
   python 02_retag_nifi_images.py --execute
   ```

3. Push to registry:
   ```bash
   export GITLAB_TOKEN="your-token"
   python push_nifi_images.py --execute
   ```