"""
Script to explore GitLab container registry and list available packages and their tags.

This script connects to a GitLab instance, explores its container registry,
and lists available packages and their tags. By default, it explores the
content-services/idol repository, but this can be overridden.

Environment Variables Required (.env):
    GITLAB_URL: Base URL of the GitLab instance (e.g., https://gitlab.example.com)
    GITLAB_TOKEN: Personal access token for GitLab authentication

Example Usage:
    python 00_explore_gitlab.py                     # List all packages and tags
    python 00_explore_gitlab.py --tag 24.4          # Show detailed info for specific tag
    python 00_explore_gitlab.py --repository group/project/repo  # Explore different repository
    python 00_explore_gitlab.py -h                  # Show help message

Output:
    - Lists all available packages and their tags
    - With --tag, shows detailed information in column format
    - Logs are saved to ./logs directory with timestamp
"""

import requests
from dotenv import load_dotenv
import os
import logging
from datetime import datetime
import pathlib
import urllib.parse
import argparse
from typing import Optional, List, Tuple
from dataclasses import dataclass

@dataclass
class GitLabConfig:
    """Configuration for GitLab API access"""
    url: str
    headers: dict
    timeout: int = 10

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

def init_gitlab_config() -> Optional[GitLabConfig]:
    """Initialize GitLab configuration from environment variables"""
    # Load environment variables
    load_dotenv()
    
    # Get configuration from environment variables
    gitlab_url = os.getenv('GITLAB_URL')
    personal_access_token = os.getenv('GITLAB_TOKEN')
    
    if not gitlab_url or not personal_access_token:
        logger.error("Missing required environment variables GITLAB_URL or GITLAB_TOKEN")
        return None
    
    return GitLabConfig(
        url=gitlab_url,
        headers={"PRIVATE-TOKEN": personal_access_token},
        timeout=10
    )

def build_group_list(config: GitLabConfig) -> List[Tuple[int, str]]:
    """Build list of GitLab groups"""
    group_list = []
    try:
        logger.info("Attempting to retrieve GitLab groups")
        api_endpoint_groups = f"{config.url}/api/v4/groups/"
        response = requests.get(api_endpoint_groups, headers=config.headers, timeout=config.timeout)
        
        if response.status_code == 200:
            groups = response.json()
            logger.info(f"Successfully retrieved {len(groups)} groups")
            for group in groups:
                group_list.append((group['id'], group['name']))
                logger.info(f"Registry ID: {group['id']}, Name: {group['name']}")
        else:
            logger.error(f"Failed to retrieve registries: {response.status_code}, {response.text}")
            
    except requests.exceptions.Timeout:
        logger.error(f"Connection timed out after {config.timeout} seconds")
    except requests.exceptions.ConnectionError:
        logger.error("Failed to connect to the GitLab server")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
    
    return group_list

def list_repositories(config: GitLabConfig, api_endpoint_repositories: str):
    """List repositories from a given endpoint"""
    logger.info(f"Attempting to list repositories from: {api_endpoint_repositories}")
    response = requests.get(api_endpoint_repositories, headers=config.headers)

    if response.status_code == 200:
        repositories = response.json()
        logger.info(f"Successfully retrieved {len(repositories)} repositories")
        for repository in repositories:
            logger.info(f"  Registry ID: {repository['id']}, Name: {repository['name']}")
    else:
        logger.error(f"Failed to retrieve registries: {response.status_code}, {response.text}")

def format_columns(data: List[Tuple], headers: List[str]):
    """Format data in aligned columns"""
    # Calculate column widths
    widths = [len(header) for header in headers]
    for row in data:
        for i, item in enumerate(row):
            widths[i] = max(widths[i], len(str(item)))
    
    # Create format string
    format_str = "  ".join(f"{{:<{width}}}" for width in widths)
    
    # Print headers
    print(format_str.format(*headers))
    print("  ".join("-" * width for width in widths))
    
    # Print data
    for row in data:
        print(format_str.format(*row))

def explore_container_registry(config: GitLabConfig, repository_path: str, filter_tag: Optional[str] = None):
    """
    Explore packages and tags in a container registry repository
    Args:
        config: GitLab configuration
        repository_path: Full path to the repository (e.g., 'group/project/image')
        filter_tag: Optional tag to filter results
    """
    encoded_repo_path = urllib.parse.quote(repository_path, safe='')
    api_endpoint_registry = f"{config.url}/api/v4/projects/{encoded_repo_path}/registry/repositories"
    
    try:
        response = requests.get(api_endpoint_registry, headers=config.headers, timeout=config.timeout)
        
        if response.status_code == 200:
            repositories = response.json()
            
            if filter_tag:
                # Detailed view with specific tag
                detailed_data = []
                for repo in repositories:
                    tags_url = f"{config.url}/api/v4/projects/{encoded_repo_path}/registry/repositories/{repo['id']}/tags"
                    tags_response = requests.get(tags_url, headers=config.headers, timeout=config.timeout)
                    
                    if tags_response.status_code == 200:
                        tags = tags_response.json()
                        for tag in tags:
                            try:
                                if tag['name'] == filter_tag:
                                    package_name = repo['path'].split('/')[-1]
                                    # Get creation time from tag details
                                    tag_detail_url = f"{config.url}/api/v4/projects/{encoded_repo_path}/registry/repositories/{repo['id']}/tags/{tag['name']}"
                                    tag_detail_response = requests.get(tag_detail_url, headers=config.headers, timeout=config.timeout)
                                    
                                    if tag_detail_response.status_code == 200:
                                        tag_detail = tag_detail_response.json()
                                        created_at = datetime.fromisoformat(tag_detail['created_at'].replace('Z', '+00:00'))
                                        formatted_date = created_at.strftime('%Y-%m-%d %H:%M:%S')
                                        detailed_data.append((package_name, tag['name'], formatted_date))
                                    else:
                                        logger.warning(f"Could not get details for tag {tag['name']}: {tag_detail_response.status_code}")
                                        detailed_data.append((package_name, tag['name'], "N/A"))
                            except KeyError as e:
                                logger.error(f"Unexpected tag data structure. Missing field: {e}")
                                logger.debug(f"Tag data: {tag}")
                            except Exception as e:
                                logger.error(f"Error processing tag: {e}")
                                logger.debug(f"Tag data: {tag}")
                
                if detailed_data:
                    headers = ["Image Name", "Tag", "Created At"]
                    format_columns(detailed_data, headers)
                else:
                    logger.info(f"No images found with tag: {filter_tag}")
            else:
                # Original summary view
                package_info = []
                max_name_length = 0
                
                for repo in repositories:
                    tags_url = f"{config.url}/api/v4/projects/{encoded_repo_path}/registry/repositories/{repo['id']}/tags"
                    tags_response = requests.get(tags_url, headers=config.headers, timeout=config.timeout)
                    
                    if tags_response.status_code == 200:
                        tags = tags_response.json()
                        tag_names = sorted([tag['name'] for tag in tags], reverse=True)
                        package_name = repo['path'].split('/')[-1]
                        max_name_length = max(max_name_length, len(package_name))
                        package_info.append((package_name, tag_names))
                
                format_string = "{:<" + str(max_name_length) + "s}: {}"
                for package_name, tags in sorted(package_info):
                    print(format_string.format(package_name, tags))
        else:
            logger.error(f"Failed to access registry: {response.status_code}, {response.text}")
            
    except requests.exceptions.Timeout:
        logger.error(f"Connection timed out after {config.timeout} seconds")
    except requests.exceptions.ConnectionError:
        logger.error("Failed to connect to the GitLab server")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Explore GitLab container registry and list available packages and their tags.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--tag",
        help="Filter results to show detailed information for a specific tag",
        type=str
    )
    parser.add_argument(
        "--repository",
        help="GitLab repository path to explore (e.g., 'group/project/repo')",
        type=str,
        default="advanced-search/content-services/idol"
    )
    args = parser.parse_args()

    logger.info("Starting GitLab Explorer")
    
    # Initialize GitLab configuration
    config = init_gitlab_config()
    if config:
        logger.info(f"Exploring repository: {args.repository}")
        explore_container_registry(config, args.repository, args.tag)
    else:
        logger.error("Failed to initialize GitLab configuration")
    
    logger.info("GitLab Explorer completed")