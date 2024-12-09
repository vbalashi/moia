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
    script_name = os.path.splitext(os.path.basename(__file__))[0]
    return f"./logs/{script_name}_{timestamp}.log"

def read_file_lines(file_path):
    """Read lines from a file, stripping whitespace and ignoring empty lines."""
    try:
        with open(file_path, 'r') as f:
            return [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"Error reading file {file_path}: {str(e)}")
        return None

def docker_login(registry, token):
    """
    Attempt to login to Docker registry using GitLab token.
    Returns True if successful, False otherwise.
    """
    try:
        client = docker.from_env()
        auth_config = {
            'username': 'oauth2',
            'password': token
        }
        result = client.login(
            registry=registry,
            **auth_config
        )
        if result and 'Status' in result and 'succeeded' in result['Status'].lower():
            print(f"Successfully logged in to {registry}")
            return True
        return False
    except Exception as e:
        print(f"Login failed: {str(e)}")
        return False

def push_image(client, tag, log_file, dry_run=True, token=None):
    """
    Push a single Docker image to the repository and log the results.
    
    Args:
        client: Docker client instance
        tag: Image tag to push
        log_file: File object for logging
        dry_run: If True, only simulate the push operation
        token: GitLab token for authentication
    """
    print(f"\nImage: {tag}")
    start_time = time.time()
    
    if dry_run:
        result = "DRY RUN - Push simulated"
        print(f"DRY RUN - Would push image: {tag}")
        elapsed_time = 0
    else:
        try:
            # First check if the image exists locally
            try:
                image = client.images.get(tag)
                print(f"Found local image: {tag} (ID: {image.short_id})")
            except docker.errors.ImageNotFound:
                result = f"Image not found locally: {tag}"
                elapsed_time = time.time() - start_time
                log_entry = f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}, {tag}, {result}, Elapsed time: {elapsed_time:.2f} seconds"
                print(f"\n{log_entry}")
                log_file.write(f"{log_entry}\n")
                return

            # Try to inspect the image to get more details
            try:
                image_details = client.api.inspect_image(tag)
                print(f"Image size: {image_details['Size'] / 1024 / 1024:.2f} MB")
            except Exception as e:
                print(f"Warning: Could not get image details: {e}")

            response = client.images.push(tag, stream=True, decode=True)
            total_layers = 0
            pushed_layers = 0
            last_update = start_time
            result = "Started push"
            error_details = []
            needs_auth = False
            last_status = ""

            for chunk in response:
                if 'error' in chunk:
                    error = chunk['error'].lower()
                    error_details.append(chunk['error'])
                    if 'authentication required' in error or 'not authenticated' in error:
                        needs_auth = True
                    continue

                if 'status' in chunk:
                    status = chunk['status']
                    if 'id' in chunk:
                        layer_id = chunk['id']
                        if status == 'Pushing':
                            total_layers += 1
                            current_status = f"Pushing layer {layer_id}"
                        elif status == 'Layer already exists':
                            pushed_layers += 1
                            current_status = f"Layer exists {layer_id}"
                        elif status == 'Pushed':
                            pushed_layers += 1
                            current_status = f"Pushed layer {layer_id}"
                        else:
                            current_status = f"{status} {layer_id}"
                    else:
                        current_status = status
                    
                    current_time = time.time()
                    elapsed_time = current_time - start_time
                    if current_time - last_update >= 1:
                        progress = f"[{pushed_layers}/{total_layers}]" if total_layers > 0 else ""
                        status_line = f"\rElapsed time: {elapsed_time:.2f} seconds, Status: {current_status} {progress}"
                        # Clear the previous line if it was longer
                        if len(last_status) > len(status_line):
                            print('\r' + ' ' * len(last_status), end='\r')
                        print(status_line, end='', flush=True)
                        last_status = status_line
                        last_update = current_time

            # Clear the progress line
            if last_status:
                print('\r' + ' ' * len(last_status), end='\r')

            if needs_auth and token:
                print("\nAuthentication required, attempting to login...")
                registry = tag.split('/')[0]
                if docker_login(registry, token):
                    print("Login successful, retrying push...")
                    return push_image(client, tag, log_file, dry_run, token)
                else:
                    result = "Push failed: Authentication failed"
            elif error_details:
                result = f"Push failed: {'; '.join(error_details)}"
            elif pushed_layers > 0:
                result = f"Pushed successfully ({pushed_layers} layers)"
            else:
                result = "Push failed - no layers were pushed (check authentication and permissions)"

        except docker.errors.APIError as e:
            if "denied" in str(e).lower():
                if token:
                    print("\nAccess denied, attempting to login...")
                    registry = tag.split('/')[0]
                    if docker_login(registry, token):
                        print("Login successful, retrying push...")
                        return push_image(client, tag, log_file, dry_run, token)
                result = f"Push failed: Access denied - check authentication credentials"
            else:
                result = f"Push failed: {str(e)}"
        except Exception as e:
            result = f"Unexpected error: {str(e)}"
        
        end_time = time.time()
        elapsed_time = end_time - start_time
    
    log_entry = f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}, {tag}, {result}, Elapsed time: {elapsed_time:.2f} seconds"
    print(f"\n{log_entry}")
    log_file.write(f"{log_entry}\n")

def get_image_tags(repository, packages, versions):
    """Generate full image tags for given packages and versions."""
    tags = []
    for package in packages:
        for version in versions:
            tags.append(f"{repository}/{package}:{version}")
    return tags

def process_images(client, repository, packages, versions, log_file_path, dry_run=True, token=None):
    """
    Process and push all matching Docker images.
    
    Args:
        client: Docker client instance
        repository: Target repository
        packages: List of package names
        versions: List of versions
        log_file_path: Path to the log file
        dry_run: If True, only simulate the push operation
        token: GitLab token for authentication
    """
    images = client.images.list()
    matching_images = []
    target_tags = get_image_tags(repository, packages, versions)
    
    with open(log_file_path, 'w') as log_file:
        for image in images:
            for tag in image.tags:
                if any(target_tag in tag for target_tag in target_tags):
                    matching_images.append(tag)
                    push_image(client, tag, log_file, dry_run, token)
    
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
        gitlab_url = os.getenv('GITLAB_URL')
        gitlab_token = os.getenv('GITLAB_TOKEN')
        repository = args.repository or os.getenv('NEW_REPO')

        if not repository and gitlab_url:
            # Try to construct repository from GITLAB_URL if NEW_REPO is not set
            repository = f"{gitlab_url}/advanced-search/content-services/idol"

        if not repository:
            raise ValueError("Repository not specified. Either set NEW_REPO in .env file, use --repository, or set GITLAB_URL")

        if not gitlab_token:
            print("Warning: GITLAB_TOKEN not set in .env file")
            print("You may need to login manually if authentication is required")

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
        print(f"GitLab URL: {gitlab_url}")
        print(f"Repository: {repository}")
        print(f"Token: {'set' if gitlab_token else 'not set'}")
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
        process_images(client, repository, packages, versions, log_file_path, not args.no_dry_run, gitlab_token)

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
