import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get credentials from environment variables
username = os.getenv('DOCKER_HUB_USERNAME')
password = os.getenv('DOCKER_HUB_PASSWORD')
login_url = os.getenv('DOCKER_HUB_LOGIN_URL')

# Login payload
payload = {
    'username': username,
    'password': password
}

# Headers for the login request
headers = {
    'Content-Type': 'application/json'
}

# Perform the login request
response = requests.post(login_url, headers=headers, data=json.dumps(payload))

def void():
    return

# Check if login was successful
if response.status_code == 200:
    # Extract the token from the response
    token = response.json().get('token')
    if token:
        void()
    else:
        print('Failed to retrieve token')
else:
    print(f'Login failed with status code: {response.status_code}')


# List of packages
packages = [
    'content',
    # 'category',
    # 'community',
    # 'find',
    # 'dah',
    # 'omnigroupserver',
    # 'agentstore',
    # 'categorisation-agentstore',
    # 'controller',
    # 'coordinator',
    # 'dataadmin',
    # 'dih',
    # 'eductionserver',
    # 'qms',
    # 'qms-agentstore',
    # 'siteadmin',
    # 'statsserver',
    # 'view'
]

# List of versions
versions = [
    '23.4',
    '24.1',
    '24.2'
]

# Function to get image size
def get_image_size(package, version):
    url = f"https://hub.docker.com/v2/repositories/microfocusidolserver/{package}/tags/{version}/"
    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to get tag data for {package}:{version}")
        return None
    
    tag_data = response.json()
    if 'images' not in tag_data or len(tag_data['images']) == 0:
        print(f"No images found for {package}:{version}")
        return None

    digest = tag_data['images'][0]['digest']
    manifest_url = f"https://hub.docker.com/v2/repositories/microfocusidolserver/{package}/manifests/{digest}"
    manifest_headers = {
        'Accept': 'application/vnd.docker.distribution.manifest.v2+json',
        'Authorization': f'Bearer {token}'
    }
    manifest_response = requests.get(manifest_url, headers=manifest_headers)
    if manifest_response.status_code != 200:
        print(f"Failed to get manifest for {package}:{version}")
        return None
    
    manifest_data = manifest_response.json()
    size = sum(layer['size'] for layer in manifest_data['layers'])
    return size

# Iterate over all packages and versions
total_size = 0
for package in packages:
    for version in versions:
        print(f"Checking size for {package}:{version}")
        size = get_image_size(package, version)
        if size:
            print(f"Size of {package}:{version} is {size / (1024**2):.2f} MB")
            total_size += size

print(f"Total size required: {total_size / (1024**3):.2f} GB")
