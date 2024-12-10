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
    return parser.parse_args()

def get_config():
    load_dotenv()
    return {
        'old_repo': os.getenv('OLD_REPO'),
        'new_repo': os.getenv('NEW_REPO')
    }

def print_configuration(config, execute, remove_old):
    """Print the current configuration settings."""
    print("\nConfiguration:")
    print("-" * 50)
    print(f"Mode: {'EXECUTE' if execute else 'DRY RUN'}")
    print(f"Remove old tags: {'Yes' if remove_old else 'No'}")
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

def retag_images(old_repo, new_repo, execute=False, remove_old=False):
    client = check_docker_running()
    try:
        images = client.images.list()
        found_images = False
        
        print("\nProcessing images:")
        print("-" * 50)
        
        for image in images:
            for tag in image.tags:
                if tag.startswith(f"{old_repo}/"):
                    found_images = True
                    # Extract package name and tag from the image name
                    package_name = tag.split('/')[1].split(':')[0]
                    tag_name = tag.split(':')[1]
                    
                    # Define the new image name
                    new_image = f"{new_repo}/{package_name}:{tag_name}"
                    
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
            print(f"No images found from repository '{old_repo}'")
            
    except docker.errors.APIError as e:
        print(f"Docker API error: {str(e)}")
        sys.exit(1)

def main():
    args = parse_arguments()
    config = get_config()
    
    if not config['old_repo'] or not config['new_repo']:
        print("Error: OLD_REPO and NEW_REPO must be set in .env file")
        return
    
    # Print configuration summary
    print_configuration(config, args.execute, args.remove_old)
    
    retag_images(
        config['old_repo'],
        config['new_repo'],
        execute=args.execute,
        remove_old=args.remove_old
    )

if __name__ == "__main__":
    main()
