# Docker NiFi Project

This repository contains Docker configurations and management scripts for NiFi, Zookeeper, and RHEL base images.

## Project Structure

### NiFi (`/nifi`)
- Build scripts for NiFi 1.x (1.28.1) and 2.x (2.0.0) Docker images
- `01_build_nifi.sh`: Builds NiFi images with/without NAR support
- `02_retag_nifi_images.py`: Retags images for target registry
- Supports custom NAR files and extensions

### RHEL Base (`/rhel-base`)
- Base RHEL UBI8 image configuration with OpenJDK 21
- `00_check_rhel_version.sh`: Checks for RHEL UBI updates
- `01_build_rhel.sh`: Builds base RHEL image

### Zookeeper (`/zookeeper`)
- Apache Zookeeper 3.8.4 configurations
- Standard and remote cluster setups
- Build script for Zookeeper images
- Based on RHEL with JDK 11