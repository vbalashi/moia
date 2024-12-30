"""
Script to retag Docker images from one repository to another.

This script retags Docker images from a source repository to a target repository.
It supports dry-run mode and can optionally remove old tags after retagging.
The script is designed to work with local Docker images that have already been
pulled from the source repository.

Environment Variables Required (.env):
    OLD_REPO: Source repository path (e.g., microfocusidolserver)
    NEW_REPO: Target repository path (e.g., your-registry/idolserver)

Features:
    - Dry-run mode to preview changes
    - Option to remove old tags after retagging
    - Support for specific tag transformation
    - Package name pattern matching
    - Detailed logging with timestamps
    - Docker daemon health check

Example Usage:
    # Preview retagging (dry-run):
    python 02_retag_idolserver_images.py
    
    # Execute retagging:
    python 02_retag_idolserver_images.py --execute
    
    # Execute retagging and remove old tags:
    python 02_retag_idolserver_images.py --execute --remove-old

    # Execute specific tag transformation:
    python 02_retag_idolserver_images.py --execute --source-tag 24.4_fix --target-tag 24.4

    # Retag only specific packages (supports wildcards):
    python 02_retag_idolserver_images.py --execute --package *disco*
"""

import docker
import os
import argparse
import sys
import pathlib
import datetime
from dotenv import load_dotenv

# Create logs directory if it doesn't exist
pathlib.Path('./logs').mkdir(exist_ok=True)

def get_log_file_path():
    """Generate a log file path with current timestamp."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"./logs/docker_retag_log_{timestamp}.log"

def parse_arguments():
    parser = argparse.ArgumentParser(description='Retag Docker images from one repository to another')
    parser.add_argument('--execute', action='store_true',
                       help='Execute the retagging (default is dry-run mode)')
    parser.add_argument('--remove-old', action='store_true',
                       help='Remove old image tags after retagging')
    parser.add_argument('--source-tag',
                       help='Specific source tag to retag (e.g., 24.4_fix)')
    parser.add_argument('--target-tag',
                       help='Target tag to use (e.g., 24.4)')
    parser.add_argument('--package',
                       help='Package name pattern to match (e.g., *disco*)')
    return parser.parse_args()

def get_config():
    load_dotenv()
    return {
        'old_repo': os.getenv('OLD_REPO'),
        'new_repo': os.getenv('NEW_REPO')
    }

def print_configuration(config, execute, remove_old, source_tag=None, target_tag=None, package_pattern=None):
    """Print the current configuration settings."""
    print("\nConfiguration:")
    print("-" * 50)
    print(f"Mode: {'EXECUTE' if execute else 'DRY RUN'}")
    print(f"Remove old tags: {'Yes' if remove_old else 'No'}")
    if source_tag and target_tag:
        print(f"\nTag Transformation:")
        print(f"  Source tag: {source_tag}")
        print(f"  Target tag: {target_tag}")
    if package_pattern:
        print(f"Package filter: {package_pattern}")
    print(f"\nRepositories:")
    print(f"  Source: {config['old_repo']}")
    print(f"  Target: {config['new_repo']}")
    print("-" * 50)
    print()

def check_docker_running():
    try:
        client = docker.from_env()
        client.ping()
        return client
    except docker.errors.DockerException as e:
        print("Error: Docker is not running or not accessible.")
        print("Please make sure Docker Desktop is running and try again.")
        print("\nDetailed error:", str(e))
        sys.exit(1)

def matches_pattern(package_name, pattern):
    """Check if package name matches the given pattern."""
    from fnmatch import fnmatch
    return pattern is None or fnmatch(package_name.lower(), pattern.lower())

def retag_images(old_repo, new_repo, execute=False, remove_old=False, source_tag=None, target_tag=None, package_pattern=None):
    client = check_docker_running()
    try:
        images = client.images.list()
        found_images = False
        
        print("\nProcessing images:")
        print("-" * 50)
        
        for image in images:
            for tag in image.tags:
                if tag.startswith(f"{old_repo}/"):
                    # Extract package name and current tag from the image name
                    package_name = tag.split('/')[1].split(':')[0]
                    current_tag = tag.split(':')[1]
                    
                    # Skip if we're looking for a specific tag and this isn't it
                    if source_tag and current_tag != source_tag:
                        continue
                        
                    # Skip if package doesn't match the pattern
                    if not matches_pattern(package_name, package_pattern):
                        continue
                        
                    found_images = True
                    # Use target_tag if specified, otherwise keep the current tag
                    final_tag = target_tag if target_tag else current_tag
                    
                    # Define the new image name
                    new_image = f"{new_repo}/{package_name}:{final_tag}"
                    
                    print(f"{'[DRY-RUN] ' if not execute else ''}Retagging {tag} to {new_image}")
                    
                    if execute:
                        try:
                            image.tag(new_image)
                            if remove_old:
                                print(f"Removing old tag: {tag}")
                                client.images.remove(tag)
                        except docker.errors.APIError as e:
                            print(f"Error retagging {tag}: {str(e)}")
        
        if not found_images:
            if source_tag:
                print(f"No images found from repository '{old_repo}' with tag '{source_tag}'")
            else:
                print(f"No images found from repository '{old_repo}'")
            if package_pattern:
                print(f"Package filter: {package_pattern}")
            
    except docker.errors.APIError as e:
        print(f"Docker API error: {str(e)}")
        sys.exit(1)

def main():
    args = parse_arguments()
    config = get_config()
    
    if not config['old_repo'] or not config['new_repo']:
        print("Error: OLD_REPO and NEW_REPO must be set in .env file")
        return
    
    # Validate tag arguments
    if bool(args.source_tag) != bool(args.target_tag):
        print("Error: Both --source-tag and --target-tag must be provided together")
        return
    
    # Print configuration summary
    print_configuration(config, args.execute, args.remove_old, args.source_tag, args.target_tag, args.package)
    
    retag_images(
        config['old_repo'],
        config['new_repo'],
        execute=args.execute,
        remove_old=args.remove_old,
        source_tag=args.source_tag,
        target_tag=args.target_tag,
        package_pattern=args.package
    )

if __name__ == "__main__":
    main()
