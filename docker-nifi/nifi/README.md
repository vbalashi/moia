# NiFi Docker Image

This directory contains the build configuration for Apache NiFi Docker images based on RHEL.

## Supported Versions

- NiFi 1.x (currently 1.28.1)
- NiFi 2.x (currently 2.0.0)

## Building the Image

Use the `build.sh` script to build either NiFi v1 or v2:

```bash
# Build NiFi v1
./build.sh v1

# Build NiFi v2
./build.sh v2
```

## Configuration

The build process uses the following key parameters:

- Base image: Uses the RHEL base image from `../rhel-base`
- Components directory: `/mnt/hgfs/MOIA/nifi` (configurable in build.sh)
- Default ports: 8080, 8443, 10000, 8000

## Directory Structure

The following directories should exist in your NIFI_COMPONENTS_BASE_DIR:
```
/mnt/hgfs/MOIA/nifi/
├── conf/     # NiFi configuration files
├── lib/      # Additional libraries
└── drivers/  # Database drivers and other dependencies
```

## Image Tags

Images are tagged with their full version number:
- `nifi:1.28.1`
- `nifi:2.0.0` 