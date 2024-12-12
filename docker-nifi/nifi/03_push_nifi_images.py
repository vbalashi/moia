#!/usr/bin/env python3

import docker
import os
import argparse
import sys
import pathlib
import datetime
import fnmatch
from dotenv import load_dotenv
import json
from tqdm import tqdm
import time

# Create logs directory if it doesn't exist
pathlib.Path('./logs').mkdir(exist_ok=True)

def get_log_file_path():
    """Generate a log file path with current timestamp."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"./logs/nifi_push_log_{timestamp}.log"

def parse_arguments():
    parser = argparse.ArgumentParser(description='Push Docker images to target registry with progress tracking')
    parser.add_argument('--execute', action='store_true',
                       help='Execute the pushing (default is dry-run mode)')
    parser.add_argument('--tags', type=str,
                       help='Comma-separated list of tags to push (overrides IMAGE_TAGS env variable)')
    return parser.parse_args()

def parse_list_value(value, default):
    """Parse comma-separated string into list, handling empty or None values."""
    if not value:
        return default
    return [item.strip() for item in value.split(',') if item.strip()]

def get_config():
    load_dotenv()
    
    target_repo = os.getenv('TARGET_REPO')
    registry_url = os.getenv('REGISTRY_URL')
    gitlab_token = os.getenv('GITLAB_TOKEN')
    
    # Parse image names and tags
    image_names = parse_list_value(os.getenv('IMAGE_NAMES'), ['nifi'])
    
    args = parse_arguments()
    # Use CLI tags if provided, otherwise fall back to env variable
    if args.tags is not None:
        image_tags = parse_list_value(args.tags, ['*'])
    else:
        image_tags = parse_list_value(os.getenv('IMAGE_TAGS'), ['*'])
    
    # Extract registry URL from target repo if not explicitly provided
    if not registry_url and target_repo:
        registry_url = target_repo.split('/')[0]
    
    return {
        'target_repo': target_repo,
        'registry_url': registry_url,
        'gitlab_token': gitlab_token,
        'image_names': image_names,
        'image_tags': image_tags
    }

def print_configuration(config, execute):
    """Print the current configuration settings."""
    print("\nConfiguration:")
    print("-" * 50)
    print(f"Mode: {'EXECUTE' if execute else 'DRY RUN'}")
    print(f"\nRepositories:")
    print(f"  Target: {config['target_repo']}")
    print(f"  Registry: {config['registry_url']}")
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

def login_to_registry(client, config):
    """Login to GitLab registry using token."""
    try:
        if config['registry_url'] and config['gitlab_token']:
            print(f"Logging in to registry {config['registry_url']}...")
            client.login(
                username='oauth2',
                password=config['gitlab_token'],
                registry=config['registry_url']
            )
            print("Successfully logged in to registry")
        else:
            print("Warning: Registry URL or GitLab token not provided, skipping login")
    except docker.errors.APIError as e:
        print(f"Error logging in to registry: {str(e)}")
        sys.exit(1)

def should_process_image(image_name, image_tag, config):
    """Check if the image name and tag match the configured patterns."""
    name_matches = any(
        fnmatch.fnmatch(image_name.lower(), pattern.lower())
        for pattern in config['image_names']
    )
    if not name_matches:
        return False
    
    tag_matches = any(
        fnmatch.fnmatch(image_tag.lower(), pattern.lower())
        for pattern in config['image_tags']
    )
    return tag_matches

def get_image_size(image):
    """Get the size of the image in bytes."""
    try:
        inspection = image.attrs
        return inspection['Size']
    except:
        return None

def format_size(size_bytes):
    """Format size in bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def check_remote_image_exists(client, image_tag, config):
    """Check if image exists in remote repository with same digest."""
    try:
        # Pull remote image digest
        remote_image = client.images.get_registry_data(image_tag)
        remote_digest = remote_image.id
        
        # Get local image digest
        local_image = client.images.get(image_tag)
        local_digest = local_image.id
        
        return remote_digest == local_digest
    except docker.errors.NotFound:
        return False
    except docker.errors.APIError:
        print(f"Warning: Could not check remote image {image_tag}. Will proceed with push.")
        return False

def push_images(target_repo, config, execute=False):
    client = check_docker_running()
    try:
        images = client.images.list()
        found_images = False
        images_to_push = []
        
        print("\nScanning for images to push:")
        print("-" * 50)
        
        # First, collect all images that need to be pushed
        for image in images:
            for tag in image.tags:
                if not tag:
                    continue
                    
                image_parts = tag.split(':')
                full_name = image_parts[0]
                image_name = full_name.split('/')[-1]
                tag_name = image_parts[1] if len(image_parts) > 1 else 'latest'
                
                # Check if this is a target repo image that should be pushed
                if tag.startswith(target_repo) and should_process_image(image_name, tag_name, config):
                    # Add check for existing remote image
                    if check_remote_image_exists(client, tag, config):
                        print(f"Skipping {tag} - identical image already exists in remote repository")
                        continue
                        
                    found_images = True
                    size = get_image_size(image)
                    images_to_push.append({
                        'image': image,
                        'tag': tag,
                        'size': size
                    })
        
        if not found_images:
            print("No matching images found to push")
            return
            
        print(f"\nFound {len(images_to_push)} images to push:")
        total_size = sum(img['size'] for img in images_to_push if img['size'] is not None)
        print(f"Total size to push: {format_size(total_size)}\n")
        
        if not execute:
            print("[DRY-RUN] Would push the following images:")
            for img in images_to_push:
                print(f"  - {img['tag']} ({format_size(img['size']) if img['size'] else 'unknown size'})")
            return
        
        # Push images with progress tracking
        for img_data in images_to_push:
            print(f"\nPushing {img_data['tag']}...")
            if img_data['size']:
                print(f"Image size: {format_size(img_data['size'])}")
            
            try:
                # Initialize progress tracking
                layer_progress = {}
                current_status = None
                
                for line in client.images.push(img_data['tag'], stream=True, decode=True):
                    if 'status' in line:
                        status = line['status']
                        
                        if status.startswith('Pushing'):
                            if 'id' in line and 'progress' in line:
                                layer_id = line['id']
                                progress = line['progress']
                                
                                # Update progress for this layer
                                layer_progress[layer_id] = progress
                                
                                # Clear screen and show progress for all layers
                                print("\033[H\033[J")  # Clear screen
                                print(f"Pushing {img_data['tag']}:")
                                for lid, prog in layer_progress.items():
                                    print(f"Layer {lid}: {prog}")
                        elif status != current_status:
                            current_status = status
                            print(f"Status: {status}")
                
                print(f"Successfully pushed: {img_data['tag']}")
                
            except docker.errors.APIError as e:
                print(f"Error pushing {img_data['tag']}: {str(e)}")
                
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
    print_configuration(config, args.execute)
    
    # Setup Docker client and login
    client = check_docker_running()
    login_to_registry(client, config)
    
    push_images(
        config['target_repo'],
        config,
        execute=args.execute
    )

if __name__ == "__main__":
    main() 