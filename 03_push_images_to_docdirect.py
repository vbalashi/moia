import docker
import datetime
import time
import sys
import os
import argparse
import pathlib
from dotenv import load_dotenv

# Create logs directory if it doesn't exist
pathlib.Path('./logs').mkdir(exist_ok=True)

def check_docker_running():
    """
    Check if Docker daemon is running and accessible.
    Raises an exception with helpful message if Docker is not available.
    """
    try:
        client = docker.from_env()
        client.ping()
        return client
    except docker.errors.DockerException as e:
        print("Error: Unable to connect to Docker daemon. Please check that:")
        print("1. Docker Desktop is installed")
        print("2. Docker Desktop is running")
        print("3. You have permission to access Docker")
        print("\nDetailed error:", str(e))
        sys.exit(1)

def initialize_docker_client():
    """Initialize and return the Docker client."""
    return check_docker_running()

def get_log_file_path():
    """Generate a log file path with current timestamp."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"./logs/docker_push_log_{timestamp}.log"

def read_file_lines(file_path):
    """Read lines from a file, stripping whitespace and ignoring empty lines."""
    try:
        with open(file_path, 'r') as f:
            return [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"Error reading file {file_path}: {str(e)}")
        return None

def push_image(client, tag, log_file, dry_run=True):
    """
    Push a single Docker image to the repository and log the results.
    
    Args:
        client: Docker client instance
        tag: Image tag to push
        log_file: File object for logging
        dry_run: If True, only simulate the push operation
    """
    print(f"Image: {tag}")
    start_time = time.time()
    
    if dry_run:
        result = "DRY RUN - Push simulated"
        sys.stdout.write(f"\rDRY RUN - Would push image: {tag}\n")
        elapsed_time = 0
    else:
        try:
            response = client.images.push(tag, stream=True, decode=True)
            total_bytes = 0
            last_update = start_time
            result = "Started push"

            for chunk in response:
                if 'status' in chunk:
                    if chunk['status'] == 'Pushed':
                        result = "Pushed successfully"
                    elif chunk['status'] == 'Layer already exists':
                        result = "Layer already exists"
                if 'progressDetail' in chunk and 'total' in chunk['progressDetail']:
                    total_bytes = chunk['progressDetail']['total']

                current_time = time.time()
                elapsed_time = current_time - start_time
                if current_time - last_update >= 1:
                    sys.stdout.write(f"\rElapsed time: {elapsed_time:.2f} seconds, Status: {chunk.get('status', 'N/A')}")
                    sys.stdout.flush()
                    last_update = current_time

            if not total_bytes:
                result = "Image already exists in remote repository"
        except docker.errors.APIError as e:
            result = f"Push failed: {e.explanation}"
        
        end_time = time.time()
        elapsed_time = end_time - start_time
    
    log_entry = f"\n{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}, {tag}, {result}, Elapsed time: {elapsed_time:.2f} seconds\n"
    sys.stdout.write(log_entry)
    sys.stdout.flush()
    log_file.write(log_entry)

def get_image_tags(repository, packages, versions):
    """Generate full image tags for given packages and versions."""
    tags = []
    for package in packages:
        for version in versions:
            tags.append(f"{repository}/{package}:{version}")
    return tags

def process_images(client, repository, packages, versions, log_file_path, dry_run=True):
    """
    Process and push all matching Docker images.
    
    Args:
        client: Docker client instance
        repository: Target repository
        packages: List of package names
        versions: List of versions
        log_file_path: Path to the log file
        dry_run: If True, only simulate the push operation
    """
    images = client.images.list()
    matching_images = []
    target_tags = get_image_tags(repository, packages, versions)
    
    with open(log_file_path, 'w') as log_file:
        for image in images:
            for tag in image.tags:
                if any(target_tag in tag for target_tag in target_tags):
                    matching_images.append(tag)
                    push_image(client, tag, log_file, dry_run)
    
    if not matching_images:
        print(f"No images found matching repository prefix: {repository}/")
        print("Expected images:")
        for tag in target_tags:
            print(f"  - {tag}")

def parse_arguments():
    """Parse and return command line arguments."""
    parser = argparse.ArgumentParser(
        description='Push Docker images to DocDirect registry',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Dry run (default) - show what would be pushed
    python %(prog)s

    # Actually push the images
    python %(prog)s --no-dry-run

    # Use custom package and version files
    python %(prog)s --packages-file my_packages.txt --versions-file my_versions.txt
        """
    )
    
    parser.add_argument(
        '--no-dry-run',
        action='store_true',
        help='Actually push the images (default: dry run only)'
    )
    
    parser.add_argument(
        '--repository',
        help='Override the repository from .env file'
    )

    parser.add_argument(
        '--packages-file',
        help='Path to file containing package names'
    )

    parser.add_argument(
        '--versions-file',
        help='Path to file containing versions'
    )
    
    return parser.parse_args()

def main():
    """Main function to orchestrate the Docker image push process."""
    try:
        args = parse_arguments()
        
        # Load environment variables
        load_dotenv()
        repository = args.repository or os.getenv('NEW_REPO')
        if not repository:
            raise ValueError("Repository not specified. Either set NEW_REPO in .env file or use --repository")

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

        # Initialize Docker client
        client = initialize_docker_client()
        
        # Get log file path
        log_file_path = get_log_file_path()
        
        # Print configuration
        print("Configuration:")
        print(f"Repository: {repository}")
        print(f"Packages ({len(packages)}):")
        for pkg in packages:
            print(f"  - {pkg}")
        print(f"Versions ({len(versions)}):")
        for ver in versions:
            print(f"  - {ver}")
        print(f"Mode: {'PUSH' if args.no_dry_run else 'DRY RUN'}")
        print(f"Log file: {log_file_path}")
        print("-" * 50)
        
        # Process and push images
        process_images(client, repository, packages, versions, log_file_path, not args.no_dry_run)

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
