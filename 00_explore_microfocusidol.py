import requests
import json
import os
from dotenv import load_dotenv
import argparse

# Load environment variables from .env file
load_dotenv()

# Get credentials from environment variables
username = os.getenv('DOCKER_HUB_USERNAME')
password = os.getenv('DOCKER_HUB_PASSWORD')

def get_all_packages():
    try:
        # First, get a JWT token
        login_response = requests.post(
            'https://hub.docker.com/v2/users/login/',
            json={
                'username': username,
                'password': password
            }
        )
        
        if login_response.status_code != 200:
            print(f"Login failed: {login_response.status_code}")
            print(f"Login response: {login_response.text}")
            return []
            
        token = login_response.json().get('token')
        if not token:
            print("No token received after login")
            return []
            
        # Use the token to get repositories
        url = "https://hub.docker.com/v2/namespaces/microfocusidolserver/repositories/?page_size=100"
        
        response = requests.get(
            url,
            headers={
                'Authorization': f'JWT {token}',
                'Content-Type': 'application/json'
            }
        )
        
        if response.status_code != 200:
            print(f"Error response: {response.text}")
            return []
            
        data = response.json()
        packages = [repo['name'] for repo in data.get('results', [])]
        
        # Handle pagination if there are more results
        while data.get('next'):
            response = requests.get(
                data['next'], 
                headers={'Authorization': f'JWT {token}'}
            )
            if response.status_code == 200:
                data = response.json()
                packages.extend([repo['name'] for repo in data.get('results', [])])
            else:
                print(f"Failed to get next page: {response.status_code}")
                break
        
        return sorted(packages)
        
    except Exception as e:
        print(f"Error fetching packages: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return []

def list_tags(package):
    try:
        # First, get a JWT token
        login_response = requests.post(
            'https://hub.docker.com/v2/users/login/',
            json={
                'username': username,
                'password': password
            }
        )
        
        if login_response.status_code != 200:
            return []
            
        token = login_response.json().get('token')
        if not token:
            return []

        url = f"https://hub.docker.com/v2/repositories/microfocusidolserver/{package}/tags/?page_size=100"
        response = requests.get(
            url,
            headers={
                'Authorization': f'JWT {token}',
                'Content-Type': 'application/json'
            }
        )
        
        if response.status_code != 200:
            return []
            
        data = response.json()
        tags = [tag['name'] for tag in data.get('results', [])]
        
        # Handle pagination if there are more results
        while data.get('next'):
            response = requests.get(
                data['next'],
                headers={'Authorization': f'JWT {token}'}
            )
            if response.status_code == 200:
                data = response.json()
                tags.extend([tag['name'] for tag in data.get('results', [])])
            else:
                break
                
        return sorted(tags)
        
    except Exception:
        return []

def read_packages_from_file(file_path):
    try:
        with open(file_path, 'r') as f:
            return [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"Error reading file {file_path}: {str(e)}")
        return None

def main():
    parser = argparse.ArgumentParser(
        description='Explore MicroFocus IDOL Docker Hub packages and their tags',
        formatter_class=argparse.RawTextHelpFormatter
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '--packages', 
        nargs='*', 
        help='List of packages to show tags for\nExample: --packages content category'
    )
    group.add_argument(
        '--packages-file', 
        help='Path to file containing package names (one per line)\nExample: --packages-file packages.txt'
    )

    try:
        args = parser.parse_args()
    except SystemExit:
        parser.print_help()
        return

    all_packages = get_all_packages()

    if not args.packages and not args.packages_file:
        # Just print all packages
        for package in all_packages:
            print(package)
        return

    # Get packages to process
    packages_to_process = []
    if args.packages_file:
        file_packages = read_packages_from_file(args.packages_file)
        if file_packages is None:
            return
        packages_to_process.extend(file_packages)
    
    if args.packages:
        packages_to_process.extend(args.packages)

    if not packages_to_process:
        print("No packages specified")
        return

    # Process each package
    for package in packages_to_process:
        if package not in all_packages:
            print(f"Warning: Package '{package}' not found")
            continue
        
        tags = list_tags(package)
        print(f"\n{package}: {tags}")

if __name__ == "__main__":
    main() 