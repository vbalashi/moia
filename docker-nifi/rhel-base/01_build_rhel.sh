#!/bin/bash

# Script: 01_build_rhel.sh
# Description: Builds a Docker image based on RHEL UBI base image using
#              the version specified in Dockerfile-redhat.
#
# Output:
#   - Builds Docker image tagged as rhel-base:<version>
#   - Prints build completion message with the full image name

TARGET_IMAGE_NAME="rhel-base"
# Extract the IMAGE_TAG from Dockerfile
TARGET_IMAGE_TAG=$(grep 'IMAGE_TAG=' Dockerfile-redhat | cut -d'=' -f2)

docker build -t "${TARGET_IMAGE_NAME}:${TARGET_IMAGE_TAG}" -f Dockerfile-redhat .

echo "Build completed: ${TARGET_IMAGE_NAME}:${TARGET_IMAGE_TAG}" 