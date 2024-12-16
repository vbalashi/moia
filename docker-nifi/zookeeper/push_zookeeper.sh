#!/bin/bash

# Script: push_zookeeper.sh
# Description: Pushes Docker images for both Zookeeper and Zookeeper-remote
#              to the specified Docker registry.

# Extract the ZOOKEEPER_VERSION from Dockerfile
ZOOKEEPER_VERSION=$(grep 'ARG ZOOKEEPER_VERSION=' Dockerfile-zookeeper | cut -d'=' -f2)

# Define the registry URL
REGISTRY_URL="registry.gitlab.docdirekt.rijkscloud.nl/advanced-search/data-services/apache-nifi"

# Regular Zookeeper
ZOOKEEPER_IMAGE_NAME="zookeeper"
echo "Tagging and pushing ${ZOOKEEPER_IMAGE_NAME}:${ZOOKEEPER_VERSION}"
docker tag "${ZOOKEEPER_IMAGE_NAME}:${ZOOKEEPER_VERSION}" "${REGISTRY_URL}/${ZOOKEEPER_IMAGE_NAME}:${ZOOKEEPER_VERSION}"
docker push "${REGISTRY_URL}/${ZOOKEEPER_IMAGE_NAME}:${ZOOKEEPER_VERSION}"

# Remote Zookeeper
ZOOKEEPER_REMOTE_IMAGE_NAME="zookeeper-remote"
echo "Tagging and pushing ${ZOOKEEPER_REMOTE_IMAGE_NAME}:${ZOOKEEPER_VERSION}"
docker tag "${ZOOKEEPER_REMOTE_IMAGE_NAME}:${ZOOKEEPER_VERSION}" "${REGISTRY_URL}/${ZOOKEEPER_REMOTE_IMAGE_NAME}:${ZOOKEEPER_VERSION}"
docker push "${REGISTRY_URL}/${ZOOKEEPER_REMOTE_IMAGE_NAME}:${ZOOKEEPER_VERSION}"

echo "Push completed:"
echo "- ${REGISTRY_URL}/${ZOOKEEPER_IMAGE_NAME}:${ZOOKEEPER_VERSION}"
echo "- ${REGISTRY_URL}/${ZOOKEEPER_REMOTE_IMAGE_NAME}:${ZOOKEEPER_VERSION}" 