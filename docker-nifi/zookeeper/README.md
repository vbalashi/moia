# Apache Zookeeper Configuration

This directory contains Docker configurations for Apache Zookeeper, a centralized service for maintaining configuration information, naming, providing distributed synchronization, and providing group services.

## Overview

The setup includes:
- Standard Zookeeper cluster configuration
- Remote Zookeeper cluster configuration

Both configurations are based on RHEL with JDK 11 and Apache Zookeeper 3.8.4.

## Files

- `Dockerfile-zookeeper` - Standard Zookeeper configuration
- `Dockerfile-zookeeper-remote` - Remote Zookeeper configuration
- Configuration templates and startup scripts

## Usage

Build images: `./build_zookeeper.sh`
