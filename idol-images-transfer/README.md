# IDOL Server Docker Image Management

This project contains a collection of Python scripts for managing Docker images related to Micro Focus IDOL Server. It helps automate the process of pulling, retagging, and pushing Docker images between different registries.

## Features

- Explore GitLab repositories and groups
- Explore Docker Hub IDOL Server packages and tags
- Pull images from Micro Focus IDOL Server repository
- Retag images for different environments
- Push images to target registries (Docker Hub or custom registry)
- Dry-run support for all operations
- Detailed logging and operation summaries

## Prerequisites

- Python 3.x
- Docker Desktop installed and running
- Access to Docker Hub (for pulling IDOL images)
- Access to target registry (Docker Hub or custom)
- Required environment variables configured

## Installation

1. Clone this repository
2. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Copy `.env.example` to `.env` and configure your environment variables:

```env
# GitLab configuration (for 00_explore_gitlab.py)
GITLAB_URL=https://gitlab.example.com
GITLAB_TOKEN=your_gitlab_token_here

# Docker Hub credentials (used by multiple scripts)
DOCKER_HUB_USERNAME=your_dockerhub_username
DOCKER_HUB_PASSWORD=your_dockerhub_password

# Repository configuration (for retagging)
OLD_REPO=microfocusidolserver
NEW_REPO=your-registry/idol

# Custom registry configuration (optional, only if not using Docker Hub)
DOCKER_REGISTRY=your.registry.url  # e.g., registry.gitlab.example.com
DOCKER_USERNAME=your_registry_username  # if different from Docker Hub
DOCKER_PASSWORD=your_registry_password  # if different from Docker Hub
```

## Scripts

### 1. GitLab Explorer (`00_explore_gitlab.py`)
Explores GitLab groups and repositories to verify access and find correct repository paths.

**Required Environment Variables:**
- `GITLAB_URL`: Base URL of the GitLab instance
- `GITLAB_TOKEN`: Personal access token for GitLab authentication

```bash
python 00_explore_gitlab.py
```

### 2. Docker Hub Explorer (`00_explore_microfocusidol.py`)
Lists available packages and their tags from the Micro Focus IDOL Server Docker Hub repository.

**Required Environment Variables:**
- `DOCKER_HUB_USERNAME`: Docker Hub username
- `DOCKER_HUB_PASSWORD`: Docker Hub password

```bash
# List all packages
python 00_explore_microfocusidol.py

# Show tags for specific packages
python 00_explore_microfocusidol.py --packages content category

# Show tags for packages listed in a file
python 00_explore_microfocusidol.py --packages-file packages.txt
```

### 3. Pull Images (`01_pull_from_microfocusidolserver.py`)
Pulls IDOL Docker images from Micro Focus repository.

**Required Environment Variables:**
- `DOCKER_HUB_USERNAME`: Docker Hub username
- `DOCKER_HUB_PASSWORD`: Docker Hub password

```bash
# Dry run - show what would be pulled
python 01_pull_from_microfocusidolserver.py

# Actually pull the images
python 01_pull_from_microfocusidolserver.py --execute

# Use custom package and version lists
python 01_pull_from_microfocusidolserver.py --packages-file packages.txt --versions-file versions.txt
```

Default packages include: content, category, community, find, dah, omnigroupserver, agentstore, etc.
Default version: 24.4

### 4. Retag Images (`02_retag_idolserver_images.py`)
Retags pulled images for your target registry.

**Required Environment Variables:**
- `OLD_REPO`: Source repository path (e.g., microfocusidolserver)
- `NEW_REPO`: Target repository path (e.g., your-registry/idol)

```bash
# Dry run - show what would be retagged
python 02_retag_idolserver_images.py

# Execute retagging
python 02_retag_idolserver_images.py --execute

# Execute retagging and remove old tags
python 02_retag_idolserver_images.py --execute --remove-old
```

### 5. Push Images (`03_push_images_to_docdirect.py`)
Pushes retagged images to the target registry (Docker Hub or custom registry).

**Required Environment Variables:**
If pushing to Docker Hub:
- `DOCKER_HUB_USERNAME`: Docker Hub username
- `DOCKER_HUB_PASSWORD`: Docker Hub password

If pushing to a custom registry:
- `DOCKER_REGISTRY`: Target registry URL
- `DOCKER_USERNAME`: Registry username (if different from Docker Hub)
- `DOCKER_PASSWORD`: Registry password (if different from Docker Hub)

Common variables:
- `NEW_REPO`: Target repository path (same as used in retagging)

```bash
# Dry run - show what would be pushed
python 03_push_images_to_docdirect.py

# Actually push the images
python 03_push_images_to_docdirect.py --execute

# Push specific packages
python 03_push_images_to_docdirect.py --execute --packages content category
```

## Typical Workflow

1. Explore available packages and tags:
```bash
python 00_explore_microfocusidol.py
```

2. Pull IDOL images (dry-run first):
```bash
python 01_pull_from_microfocusidolserver.py
python 01_pull_from_microfocusidolserver.py --execute
```

3. Retag images for your registry:
```bash
python 02_retag_idolserver_images.py --execute
```

4. Push to target registry (dry-run first):
```bash
python 03_push_images_to_docdirect.py
python 03_push_images_to_docdirect.py --execute
```

## Configuration Files

You can customize packages and versions using text files:

- `packages.txt`: One package name per line (e.g., content, find, etc.)
- `versions.txt`: One version number per line (e.g., 24.4)

## Logs

All operations are logged in the `./logs` directory with timestamps:

- GitLab exploration: `./logs/00_explore_gitlab_YYYYMMDD_HHMMSS.log`
- Docker Hub exploration: `./logs/00_explore_microfocusidol_YYYYMMDD_HHMMSS.log`
- Docker pull operations: `./logs/docker_pull_log_YYYYMMDD_HHMMSS.log`
- Docker retag operations: `./logs/docker_retag_log_YYYYMMDD_HHMMSS.log`
- Docker push operations: `./logs/docker_push_log_YYYYMMDD_HHMMSS.log`

Each script provides detailed configuration summaries and progress information during execution.

## Project Structure

```
.
├── .env                                    # Environment configuration
├── .venv/                                  # Python virtual environment
├── logs/                                   # All log files
├── packages.txt                            # Optional: Custom package list
├── versions.txt                            # Optional: Custom version list
├── requirements.txt                        # Python dependencies
├── README.md                               # This file
├── 00_explore_gitlab.py                    # GitLab exploration script
├── 00_explore_microfocusidol.py           # Docker Hub exploration script
├── 01_pull_from_microfocusidolserver.py   # Image pull script
├── 02_retag_idolserver_images.py          # Image retag script
└── 03_push_images_to_docdirect.py         # Image push script
```