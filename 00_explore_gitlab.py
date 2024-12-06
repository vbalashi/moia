import requests
from dotenv import load_dotenv
import os
import logging
from datetime import datetime
import pathlib

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

if __name__ == "__main__":
    logger.info("Starting GitLab Explorer")
    build_group_list()
    logger.info("GitLab Explorer completed")