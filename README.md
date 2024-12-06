# IDOL Server Docker Image Management

This project contains a collection of Python scripts for managing Docker images related to Micro Focus IDOL Server. It helps automate the process of pulling, retagging, and pushing Docker images between different registries.

## Features

- Pull images from Micro Focus IDOL Server repository
- Check and analyze Docker image sizes
- Retag images for different environments
- Push images to target registries
- GitLab integration for repository management

## Prerequisites

- Python 3.x
- Docker installed and configured
- Access to relevant Docker registries
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

4. Copy `.env.example` to `.env` and configure your environment variables

## Scripts

- `00_explore_gitlab.py`: GitLab repository exploration and management
- `00_idolserver_check_images_sizes.py`: Analyze Docker image sizes
- `01_pull_from_microfocusidolserver.py`: Pull images from Micro Focus repository
- `02_retag_idolserver_images.py`: Retag Docker images
- `03_push_images_to_docdirect.py`: Push images to target registry

## Usage

Each script can be run independently based on your needs. For example:

```bash
python 01_pull_from_microfocusidolserver.py
```

Check individual script files for specific usage instructions and required parameters.

## Logs

The project generates log files for Docker push operations in the format `docker_push_log_YYYYMMDD_HHMMSS.log` 