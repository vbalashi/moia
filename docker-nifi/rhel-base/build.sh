#!/bin/bash

TARGET_IMAGE_NAME="rhel-base"
# Extract the IMAGE_TAG from Dockerfile
TARGET_IMAGE_TAG=$(grep 'IMAGE_TAG=' Dockerfile-redhat | cut -d'=' -f2)

docker build -t "${TARGET_IMAGE_NAME}:${TARGET_IMAGE_TAG}" -f Dockerfile-redhat .

echo "Build completed: ${TARGET_IMAGE_NAME}:${TARGET_IMAGE_TAG}" 