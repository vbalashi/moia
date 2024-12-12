# RHEL Base Image for NiFi

This directory contains the build configuration for a Red Hat Enterprise Linux (RHEL) based Docker image that serves as a base for NiFi deployment.

## Scripts

### `00_check_rhel_version.sh`
Checks if there's a newer version of RHEL UBI available in the registry.
```bash
./00_check_rhel_version.sh
```
This script:
- Extracts the current UBI version from `Dockerfile-redhat`
- Queries the Red Hat registry for available versions
- Compares current and latest versions
- Logs the results to `logs/rhel_version_check_<timestamp>.log`
- Reports if an update is available

### `01_build_rhel.sh`
Builds the Docker image using the RHEL UBI version specified in the Dockerfile.
```bash
./01_build_rhel.sh
```
This script:
- Extracts the version tag from `Dockerfile-redhat`
- Builds the Docker image with the appropriate tag
- Names the image as `rhel-base:<ubi-version>`

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