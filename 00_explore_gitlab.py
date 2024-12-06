import requests
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Get configuration from environment variables
gitlab_url = os.getenv('GITLAB_URL')
personal_access_token = os.getenv('GITLAB_TOKEN')
group_list = []

# Define the API endpoint
api_endpoint_groups = f"{gitlab_url}/api/v4/groups/"
# Note: group_id is not defined yet, so commenting out this line
# api_endpoint_repositories = f"{gitlab_url}/api/v4/groups/{group_id}/registry/repositories"

# Set up headers
headers = {
    "PRIVATE-TOKEN": personal_access_token
}

def build_group_list():
    # Make the request
    response = requests.get(api_endpoint_groups, headers=headers)
    print(response)

    # Check if the request was successful
    if response.status_code == 200:
        groups = response.json()
        for group in groups:
            group_list.append((group['id'], group['name']))  # Fixed tuple syntax
            print(f"Registry ID: {group['id']}, Name: {group['name']}")
    else:
        print(f"Failed to retrieve registries: {response.status_code}, {response.text}")

def list_repositories(api_endpoint_repositories):
    # Make the request
    response = requests.get(api_endpoint_repositories, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        repositories = response.json()
        for repository in repositories:
            print(f"  Registry ID: {repository['id']}, Name: {repository['name']}")
    else:
        print(f"Failed to retrieve registries: {response.status_code}, {response.text}")

if __name__ == "__main__":
    build_group_list()