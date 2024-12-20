#!/usr/bin/env python3

'''
NiFi Image Retag Script

This script retags local NiFi Docker images with target registry tags.
It provides both dry-run and execute modes, with an option to remove old tags.

Environment Variables Required:
    TARGET_REPO:  Target repository URL (e.g., 'registry.example.com/org')
    IMAGE_NAMES:  Comma-separated list of image names to retag (default: 'nifi')
    IMAGE_TAGS:   Comma-separated list of tags to retag (default: '*')

Example Usage:
    # Dry run mode
    python 02_retag_nifi_images.py

    # Execute mode and remove old tags
    python 02_retag_nifi_images.py --execute --remove-old
'''

import docker
import os
import argparse
import sys
import pathlib
import datetime
import fnmatch
from dotenv import load_dotenv

# Create logs directory if it doesn't exist
pathlib.Path('./logs').mkdir(exist_ok=True)

# Add this near the start of your script, before accessing any env vars
load_dotenv()

def get_log_file_path():
    """Generate a log file path with current timestamp."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"./logs/nifi_retag_log_{timestamp}.log"

def parse_arguments():
    parser = argparse.ArgumentParser(description='Retag Docker images with target registry tags')
    parser.add_argument('--execute', action='store_true',
                       help='Execute the retagging (default is dry-run mode)')
    parser.add_argument('--remove-old', action='store_true',
                       help='Remove old image tags after retagging')
    return parser.parse_args()

def parse_list_value(value, default):
    """Parse comma-separated string into list, handling empty or None values."""
    if not value:
        return default
    return [item.strip() for item in value.split(',') if item.strip()]

def get_config():
    # Add debug prints
    print(f"Current working directory: {os.getcwd()}")
    print(f".env file exists: {os.path.exists('.env')}")
    
    # Read and print .env file contents directly
    try:
        with open('.env', 'r') as env_file:
            print("Contents of .env file:")
            print(env_file.read())
    except Exception as e:
        print(f"Error reading .env file: {e}")
    
    load_dotenv(verbose=True)  # Add verbose flag to see what dotenv is doing
    
    target_repo = os.getenv('TARGET_REPO')
    print(f"TARGET_REPO value: {target_repo}")  # Debug print
    
    # Parse image names and tags
    image_names = parse_list_value(os.getenv('IMAGE_NAMES'), ['nifi'])
    image_tags = parse_list_value(os.getenv('IMAGE_TAGS'), ['*'])
    
    return {
        'target_repo': target_repo,
        'image_names': image_names,
        'image_tags': image_tags
    }

def print_configuration(config, execute, remove_old):
    """Print the current configuration settings."""
    print("\nConfiguration:")
    print("-" * 50)
    print(f"Mode: {'EXECUTE' if execute else 'DRY RUN'}")
    print(f"Remove old tags: {'Yes' if remove_old else 'No'}")
    print(f"\nTarget Repository: {config['target_repo']}")
    print("\nImages to process:")
    print(f"  Names: {', '.join(config['image_names'])}")
    print(f"  Tags: {', '.join(config['image_tags'])}")
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

def should_process_image(image_name, image_tag, config):
    """Check if the image name and tag match the configured patterns."""
    # Check if image name matches any of the configured names
    name_matches = any(
        fnmatch.fnmatch(image_name.lower(), pattern.lower())
        for pattern in config['image_names']
    )
    if not name_matches:
        return False
    
    # Check if tag matches any of the configured patterns
    tag_matches = any(
        fnmatch.fnmatch(image_tag.lower(), pattern.lower())
        for pattern in config['image_tags']
    )
    return tag_matches

def retag_images(target_repo, config, execute=False, remove_old=False):
    client = check_docker_running()
    try:
        images = client.images.list()
        found_images = False
        
        print("\nProcessing images:")
        print("-" * 50)
        
        for image in images:
            for tag in image.tags:
                # Skip images without tags
                if not tag:
                    continue
                    
                # Parse image name and tag
                image_parts = tag.split(':')
                full_name = image_parts[0]
                image_name = full_name.split('/')[-1]  # Get just the image name without repo
                tag_name = image_parts[1] if len(image_parts) > 1 else 'latest'
                
                # Check if this image/tag combination should be processed
                if not should_process_image(image_name, tag_name, config):
                    continue
                
                # Skip if the image is already in the target repository
                if target_repo in tag:
                    continue
                
                found_images = True
                # Define the new image name
                new_image = f"{target_repo}/{image_name}:{tag_name}"
                
                print(f"{'[DRY-RUN] ' if not execute else ''}Retagging {tag} to {new_image}")
                
                if execute:
                    try:
                        # Tag the image
                        image.tag(new_image)
                        print(f"Successfully retagged to: {new_image}")
                        
                        if remove_old:
                            print(f"Removing old tag: {tag}")
                            client.images.remove(tag)
                            
                    except docker.errors.APIError as e:
                        print(f"Error processing {tag}: {str(e)}")
        
        if not found_images:
            print("No matching images found locally")
            
    except docker.errors.APIError as e:
        print(f"Docker API error: {str(e)}")
        sys.exit(1)

def main():
    args = parse_arguments()
    config = get_config()
    
    if not config['target_repo']:
        print("Error: TARGET_REPO environment variable is not set")
        return
    
    # Print configuration summary
    print_configuration(config, args.execute, args.remove_old)
    
    retag_images(
        config['target_repo'],
        config,
        execute=args.execute,
        remove_old=args.remove_old
    )

if __name__ == "__main__":
    main() 