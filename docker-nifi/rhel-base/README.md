# RHEL Base Image for NiFi

This directory contains the build configuration for a Red Hat Enterprise Linux (RHEL) based Docker image that serves as a base for NiFi deployment.

## Available Scripts

### `build.sh`
Builds the Docker image using the latest RHEL UBI version specified in the Dockerfile.
```bash
./build.sh
```
The script automatically extracts the version tag from `Dockerfile-redhat` to maintain version consistency.

### `check_rhel_version.sh`
Checks if there's a newer version of RHEL UBI available in the registry.
```bash
./check_rhel_version.sh
```
The script compares the current version in the Dockerfile with the latest available version from the Red Hat registry and logs the results.

## Base Image Details
- Base Image: `registry.access.redhat.com/ubi8/ubi`
- Java Version: OpenJDK 21
- Additional Packages: curl, fontconfig

## Build Output
The resulting image will be tagged as:
```
rhel-base:<ubi-version>
```
where `<ubi-version>` matches the UBI version specified in the Dockerfile. 