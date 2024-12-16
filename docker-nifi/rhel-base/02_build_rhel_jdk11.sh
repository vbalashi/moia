#!/bin/bash

# Script: 02_build_rhel_jdk11.sh
# Description: Builds a Docker image based on RHEL UBI base image using
#              the version specified in Dockerfile-redhat-jdk11.
#
# Output:
#   - Builds Docker image tagged as rhel-base-jdk11:<version>
#   - Prints build completion message with the full image name

TARGET_IMAGE_NAME="rhel-base-jdk11"
# Extract the IMAGE_TAG from Dockerfile
TARGET_IMAGE_TAG=$(grep 'IMAGE_TAG=' Dockerfile-redhat-jdk11 | cut -d'=' -f2)

docker build -t "${TARGET_IMAGE_NAME}:${TARGET_IMAGE_TAG}" -f Dockerfile-redhat-jdk11 .

echo "Build completed: ${TARGET_IMAGE_NAME}:${TARGET_IMAGE_TAG}" 