# IDOL Server Docker Image Management

This project contains a collection of Python scripts for managing Docker images related to Micro Focus IDOL Server. It helps automate the process of pulling, retagging, and pushing Docker images between different registries.

## Features

- Explore GitLab repositories and groups
- Pull images from Micro Focus IDOL Server repository
- Retag images for different environments
- Push images to target registries
- Dry-run support for all operations
- Detailed logging and operation summaries

## Prerequisites

- Python 3.x
- Docker Desktop installed and running
- Access to Docker Hub (for pulling IDOL images)
- Access to target GitLab registry
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
# Docker Hub credentials for pulling IDOL images
DOCKER_HUB_USERNAME=microfocusidolreadonly
DOCKER_HUB_PASSWORD=your_password_here

# GitLab configuration
GITLAB_URL=https://gitlab.example.com
GITLAB_TOKEN=your_gitlab_token_here

# Repository configuration
OLD_REPO=microfocusidolserver
NEW_REPO=registry.gitlab.example.com/your-project/idol
```

## Scripts

### 1. GitLab Explorer (`00_explore_gitlab.py`)
Explores GitLab groups and repositories, useful for verifying access and finding correct repository paths.

```bash
python 00_explore_gitlab.py
```

### 2. Pull Images (`01_pull_from_microfocusidolserver.py`)
Pulls IDOL Docker images from Micro Focus repository.

```bash
# Dry run - show what would be pulled
python 01_pull_from_microfocusidolserver.py

# Actually pull the images
python 01_pull_from_microfocusidolserver.py --no-dry-run

# Use custom package and version lists
python 01_pull_from_microfocusidolserver.py --packages-file packages.txt --versions-file versions.txt
```

Default packages include: content, category, community, find, dah, omnigroupserver, agentstore, etc.
Default version: 24.4

### 3. Retag Images (`02_retag_idolserver_images.py`)
Retags pulled images for your target registry.

```bash
# Dry run - show what would be retagged
python 02_retag_idolserver_images.py

# Execute retagging
python 02_retag_idolserver_images.py --execute

# Execute retagging and remove old tags
python 02_retag_idolserver_images.py --execute --remove-old
```

### 4. Push Images (`03_push_images_to_docdirect.py`)
Pushes retagged images to the target registry.

```bash
# Dry run - show what would be pushed
python 03_push_images_to_docdirect.py

# Actually push the images
python 03_push_images_to_docdirect.py --no-dry-run

# Use custom package and version lists
python 03_push_images_to_docdirect.py --packages-file packages.txt --versions-file versions.txt
```

## Typical Workflow

1. Verify GitLab access and repository paths:
```bash
python 00_explore_gitlab.py
```

2. Pull IDOL images (dry-run first):
```bash
python 01_pull_from_microfocusidolserver.py
python 01_pull_from_microfocusidolserver.py --no-dry-run
```

3. Retag images for your registry:
```bash
python 02_retag_idolserver_images.py --execute
```

4. Push to target registry (dry-run first):
```bash
python 03_push_images_to_docdirect.py
python 03_push_images_to_docdirect.py --no-dry-run
```

## Configuration Files

You can customize packages and versions using text files:

- `packages.txt`: One package name per line (e.g., content, find, etc.)
- `versions.txt`: One version number per line (e.g., 24.4)

## Logs

All logs are stored in the `./logs` directory:

- GitLab exploration: `./logs/00_explore_gitlab_YYYYMMDD_HHMMSS.log`
- Docker operations: `./logs/docker_push_log_YYYYMMDD_HHMMSS.log`
- Each script provides detailed configuration summaries and progress information during execution

## Project Structure

```
.
├── .env                 # Environment configuration
├── .venv/              # Python virtual environment
├── logs/               # All log files
├── requirements.txt    # Python dependencies
└── scripts
    ├── 00_explore_gitlab.py
    ├── 01_pull_from_microfocusidolserver.py
    ├── 02_retag_idolserver_images.py
    └── 03_push_images_to_docdirect.py
```