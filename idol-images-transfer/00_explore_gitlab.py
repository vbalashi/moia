"""
Script to explore GitLab container registry and list available packages and their tags.

This script connects to a GitLab instance, explores its container registry,
and lists available packages and their tags. It's particularly focused on
exploring the content-services/idol repository.

Environment Variables Required (.env):
    GITLAB_URL: Base URL of the GitLab instance (e.g., https://gitlab.example.com)
    GITLAB_TOKEN: Personal access token for GitLab authentication

Example Usage:
    python 00_explore_gitlab.py

Output:
    - Lists all available packages and their tags
    - Logs are saved to ./logs directory with timestamp
"""

import requests
from dotenv import load_dotenv
import os
import logging
from datetime import datetime
import pathlib
import urllib.parse

# Create log directory if it doesn't exist
pathlib.Path('./logs').mkdir(exist_ok=True)

# Configure logging
log_filename = f"./logs/00_explore_gitlab_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get configuration from environment variables
gitlab_url = os.getenv('GITLAB_URL')
personal_access_token = os.getenv('GITLAB_TOKEN')
group_list = []

# Define the API endpoint
api_endpoint_groups = f"{gitlab_url}/api/v4/groups/"

# Set up headers and request configuration
headers = {
    "PRIVATE-TOKEN": personal_access_token
}
timeout_seconds = 10  # Add timeout configuration

def build_group_list():
    try:
        logger.info("Attempting to retrieve GitLab groups")
        # Make the request with timeout
        response = requests.get(api_endpoint_groups, headers=headers, timeout=timeout_seconds)
        
        # Check if the request was successful
        if response.status_code == 200:
            groups = response.json()
            logger.info(f"Successfully retrieved {len(groups)} groups")
            for group in groups:
                group_list.append((group['id'], group['name']))
                logger.info(f"Registry ID: {group['id']}, Name: {group['name']}")
        else:
            logger.error(f"Failed to retrieve registries: {response.status_code}, {response.text}")
            
    except requests.exceptions.Timeout:
        logger.error(f"Connection timed out after {timeout_seconds} seconds. Please check your network connection and GitLab URL.")
    except requests.exceptions.ConnectionError:
        logger.error("Failed to connect to the GitLab server. Please verify the GitLab URL and your network connection.")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")

def list_repositories(api_endpoint_repositories):
    logger.info(f"Attempting to list repositories from: {api_endpoint_repositories}")
    # Make the request
    response = requests.get(api_endpoint_repositories, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        repositories = response.json()
        logger.info(f"Successfully retrieved {len(repositories)} repositories")
        for repository in repositories:
            logger.info(f"  Registry ID: {repository['id']}, Name: {repository['name']}")
    else:
        logger.error(f"Failed to retrieve registries: {response.status_code}, {response.text}")

def explore_container_registry(repository_path):
    """
    Explore packages and tags in a container registry repository
    Args:
        repository_path: Full path to the repository (e.g., 'group/project/image')
    """
    encoded_repo_path = urllib.parse.quote(repository_path, safe='')
    api_endpoint_registry = f"{gitlab_url}/api/v4/projects/{encoded_repo_path}/registry/repositories"
    
    try:
        # Get repositories in the registry
        response = requests.get(api_endpoint_registry, headers=headers, timeout=timeout_seconds)
        
        if response.status_code == 200:
            repositories = response.json()
            package_info = []
            max_name_length = 0
            
            for repo in repositories:
                # Get tags for each repository
                tags_url = f"{gitlab_url}/api/v4/projects/{encoded_repo_path}/registry/repositories/{repo['id']}/tags"
                tags_response = requests.get(tags_url, headers=headers, timeout=timeout_seconds)
                
                if tags_response.status_code == 200:
                    tags = tags_response.json()
                    tag_names = sorted([tag['name'] for tag in tags], reverse=True)
                    package_name = repo['path'].split('/')[-1]
                    max_name_length = max(max_name_length, len(package_name))
                    package_info.append((package_name, tag_names))
                else:
                    logger.error(f"Failed to retrieve tags: {tags_response.status_code}, {tags_response.text}")
            
            # Print aligned output
            format_string = "{:<" + str(max_name_length) + "s}: {}"
            for package_name, tags in sorted(package_info):
                print(format_string.format(package_name, tags))
        else:
            logger.error(f"Failed to access registry: {response.status_code}, {response.text}")
            
    except requests.exceptions.Timeout:
        logger.error(f"Connection timed out after {timeout_seconds} seconds")
    except requests.exceptions.ConnectionError:
        logger.error("Failed to connect to the GitLab server")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    logger.info("Starting GitLab Explorer")
    repository_path = "advanced-search/content-services/idol"
    explore_container_registry(repository_path)
    logger.info("GitLab Explorer completed")