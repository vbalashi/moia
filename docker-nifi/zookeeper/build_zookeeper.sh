#!/bin/bash

# Script: build_zookeeper.sh
# Description: Builds Docker images for both Zookeeper and Zookeeper-remote
#              using the Zookeeper version as the tag.

# Extract the ZOOKEEPER_VERSION from Dockerfile
ZOOKEEPER_VERSION=$(grep 'ARG ZOOKEEPER_VERSION=' Dockerfile-zookeeper | cut -d'=' -f2)

# Regular Zookeeper
ZOOKEEPER_IMAGE_NAME="zookeeper"
echo "Building ${ZOOKEEPER_IMAGE_NAME}:${ZOOKEEPER_VERSION}"
docker build -t "${ZOOKEEPER_IMAGE_NAME}:${ZOOKEEPER_VERSION}" -f Dockerfile-zookeeper .

# Remote Zookeeper
ZOOKEEPER_REMOTE_IMAGE_NAME="zookeeper-remote"
echo "Building ${ZOOKEEPER_REMOTE_IMAGE_NAME}:${ZOOKEEPER_VERSION}"
docker build -t "${ZOOKEEPER_REMOTE_IMAGE_NAME}:${ZOOKEEPER_VERSION}" -f Dockerfile-zookeeper-remote .

echo "Build completed:"
echo "- ${ZOOKEEPER_IMAGE_NAME}:${ZOOKEEPER_VERSION}"
echo "- ${ZOOKEEPER_REMOTE_IMAGE_NAME}:${ZOOKEEPER_VERSION}" 