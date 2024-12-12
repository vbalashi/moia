#!/usr/bin/env python3

'''
NiFi Image Push Script

This script pushes NiFi Docker images to a target registry with progress tracking.
It supports pushing specific tags and provides both dry-run and execute modes.

Environment Variables Required:
    TARGET_REPO:   Target repository URL (e.g., 'registry.example.com/org')
    REGISTRY_URL:  Registry URL (optional, extracted from TARGET_REPO if not provided)
    GITLAB_TOKEN:  GitLab registry authentication token
    IMAGE_NAMES:   Comma-separated list of image names to push (default: 'nifi')
    IMAGE_TAGS:    Comma-separated list of tags to push (default: '*')
                   Can be overridden with --tags CLI argument

Example Usage:
    # Dry run mode
    python push_nifi_images.py

    # Execute mode with specific tags
    python push_nifi_images.py --execute --tags "1.28.1-nar,2.0.0-nar"
'''

import docker
import os
// ... existing code ... 