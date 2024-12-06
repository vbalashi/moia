import os
import argparse
import requests
import pathlib
import datetime
from dotenv import load_dotenv

# Create logs directory if it doesn't exist
pathlib.Path('./logs').mkdir(exist_ok=True)

# Load environment variables from .env file
load_dotenv()

def read_file_lines(file_path):
    """Read lines from a file, stripping whitespace and ignoring empty lines."""
    try:
        with open(file_path, 'r') as f:
            return [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"Error reading file {file_path}: {str(e)}")
        return None

def get_log_file_path():
    """Generate a log file path with current timestamp."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"./logs/docker_pull_log_{timestamp}.log"

def get_docker_auth_token():
    """Get Docker Hub authentication token."""
    username = os.getenv('DOCKER_HUB_USERNAME')
    password = os.getenv('DOCKER_HUB_PASSWORD')
    
    if not username or not password:
        print("Error: Docker Hub credentials not found in environment variables")
        return None
    
    try:
        response = requests.post(
            'https://hub.docker.com/v2/users/login/',
            json={'username': username, 'password': password}
        )
        
        if response.status_code != 200:
            print(f"Login failed: {response.status_code}")
            return None
            
        return response.json().get('token')
    except Exception as e:
        print(f"Error during authentication: {str(e)}")
        return None

def print_configuration(packages, versions, dry_run):
    """Print the current configuration settings."""
    print("\nConfiguration:")
    print("-" * 50)
    print(f"Mode: {'DRY RUN' if dry_run else 'PULL'}")
    print(f"\nPackages to pull ({len(packages)}):")
    for pkg in packages:
        print(f"  - {pkg}")
    print(f"\nVersions ({len(versions)}):")
    for ver in versions:
        print(f"  - {ver}")
    print(f"\nDocker Hub User: {os.getenv('DOCKER_HUB_USERNAME')}")
    print("-" * 50)
    print()

def pull_images(packages, versions, dry_run=True):
    """Pull Docker images for given packages and versions."""
    token = get_docker_auth_token()
    if not token:
        return False

    success = True
    for package in packages:
        for version in versions:
            image = f"microfocusidolserver/{package}:{version}"
            if dry_run:
                print(f"[DRY RUN] Would pull: {image}")
            else:
                print(f"Pulling: {image}")
                command = f"docker pull {image}"
                result = os.system(command)
                if result != 0:
                    print(f"Failed to pull {image}")
                    success = False
    
    return success

def main():
    parser = argparse.ArgumentParser(description='Pull MicroFocus IDOL Docker images')
    parser.add_argument('--packages-file', help='Path to file containing package names')
    parser.add_argument('--versions-file', help='Path to file containing versions')
    parser.add_argument('--no-dry-run', action='store_true', help='Actually pull images instead of dry run')
    args = parser.parse_args()

    # Default packages and versions if files not provided
    default_packages = [
        'content', 'category', 'community', 'find', 'dah', 'omnigroupserver',
        'agentstore', 'categorisation-agentstore', 'controller', 'coordinator',
        'dataadmin', 'dih', 'eductionserver', 'qms', 'qms-agentstore',
        'siteadmin', 'statsserver', 'view'
    ]
    default_versions = ['24.4']

    # Read packages from file if provided
    if args.packages_file:
        packages = read_file_lines(args.packages_file)
        if packages is None:
            return
    else:
        packages = default_packages

    # Read versions from file if provided
    if args.versions_file:
        versions = read_file_lines(args.versions_file)
        if versions is None:
            return
    else:
        versions = default_versions

    # Print configuration summary
    print_configuration(packages, versions, not args.no_dry_run)

    # Pull images
    success = pull_images(packages, versions, dry_run=not args.no_dry_run)
    if not success:
        print("Some images failed to pull")
        exit(1)

if __name__ == "__main__":
    main()
