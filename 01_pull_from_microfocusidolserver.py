import os
import argparse
import requests
import pathlib
import datetime
import signal
import sys
import subprocess
from dotenv import load_dotenv

# Create logs directory if it doesn't exist
pathlib.Path('./logs').mkdir(exist_ok=True)

# Load environment variables from .env file
load_dotenv()

# Global flag for interrupt handling
interrupted = False

def signal_handler(signum, frame):
    """Handle interrupt signal."""
    global interrupted
    print("\nInterrupt received. Stopping after current operation...")
    interrupted = True

# Set up signal handler
signal.signal(signal.SIGINT, signal_handler)

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

def check_docker_auth():
    """Check if already authenticated to Docker Hub."""
    try:
        result = subprocess.run(['docker', 'info'], capture_output=True, text=True)
        return 'Username:' in result.stdout
    except Exception as e:
        print(f"Error checking Docker authentication: {str(e)}")
        return False

def check_docker_available():
    """Check if Docker is properly installed and running."""
    try:
        result = subprocess.run(['docker', 'version', '--format', '{{.Server.Version}}'], 
                              capture_output=True, text=True, check=True)
        return True, None
    except subprocess.CalledProcessError:
        return False, "Docker daemon is not running. Please start Docker Desktop or Docker service."
    except FileNotFoundError:
        return False, "Docker is not installed or not in PATH. Please install Docker first."
    except Exception as e:
        return False, f"Unexpected issue with Docker: {str(e)}"

def get_docker_info():
    """Get information about Docker daemon configuration."""
    try:
        # First check if Docker is available
        is_available, error_msg = check_docker_available()
        if not is_available:
            return None, error_msg

        # Try to get basic Docker info
        result = subprocess.run(['docker', 'info', '--format', '{{.Name}}'], 
                              capture_output=True, text=True, check=True)
        host = result.stdout.strip()
        
        # Get version info
        version_result = subprocess.run(['docker', 'version', '--format', '{{.Server.Version}}'], 
                                      capture_output=True, text=True, check=True)
        version = version_result.stdout.strip()
        
        # Get root directory
        root_dir_result = subprocess.run(['docker', 'info', '--format', '{{.DockerRootDir}}'], 
                                       capture_output=True, text=True, check=True)
        root_dir = root_dir_result.stdout.strip()
        
        return {
            'version': version,
            'root_dir': root_dir,
            'host': host
        }, None
    except subprocess.CalledProcessError as e:
        return None, "Could not get complete Docker daemon info"
    except Exception as e:
        return None, f"Could not get Docker daemon info: {str(e)}"

def docker_login():
    """Perform Docker login using credentials from .env."""
    username = os.getenv('DOCKER_HUB_USERNAME')
    password = os.getenv('DOCKER_HUB_PASSWORD')
    
    if not username or not password:
        print("Error: Docker Hub credentials not found in .env file")
        print("Please ensure DOCKER_HUB_USERNAME and DOCKER_HUB_PASSWORD are set in .env")
        return False
    
    try:
        # First check if Docker is available
        if not check_docker_available():
            return False

        # Check if docker-credential-helper is available
        if os.name == 'nt':  # Windows
            helper_check = subprocess.run(['where', 'docker-credential-desktop'], 
                                        capture_output=True, text=True)
            if helper_check.returncode != 0:
                print("Warning: Docker credential helper not found.")
                print("Please install Docker Desktop or configure appropriate credential helper.")
                print("Attempting login without credential storage...")
                
        cmd = ['docker', 'login', '--username', username, '--password-stdin']
        process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate(input=password.encode())
        
        if process.returncode == 0:
            print("Successfully authenticated to Docker Hub")
            return True
        else:
            error_msg = stderr.decode().strip()
            if "error storing credentials" in error_msg:
                print("Warning: Login successful but failed to store credentials")
                print("This is not critical - pulls will still work for this session")
                return True
            else:
                print(f"Docker login failed: {error_msg}")
                return False
    except Exception as e:
        print(f"Error during Docker login: {str(e)}")
        return False

def print_configuration(packages, versions, dry_run):
    """Print the current configuration settings."""
    print("\nConfiguration:")
    print("-" * 50)
    print(f"Mode: {'DRY RUN' if dry_run else 'PULL'}")
    print(f"Remote Registry: docker.io/microfocusidolserver")
    
    # Get Docker status
    docker_info, error_msg = get_docker_info()
    print("\nDocker Status:")
    if docker_info:
        print(f"  - Host: {docker_info['host']}")
        print(f"  - Version: {docker_info['version']}")
        print(f"  - Root Dir: {docker_info['root_dir']}")
    else:
        print(f"  Not Available - {error_msg}")
    
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
    global interrupted
    
    # Check if Docker is available first
    is_available, error_msg = check_docker_available()
    if not is_available:
        print(f"\nCannot proceed: {error_msg}")
        return False
    
    # Check authentication
    if not check_docker_auth():
        print("Not authenticated to Docker Hub. Attempting to login...")
        if not docker_login():
            print("\nAuthentication failed. Please ensure:")
            print("1. Docker is properly installed and running")
            print("2. Your credentials in .env file are correct")
            print("3. You have internet connectivity to Docker Hub")
            return False

    success = True
    for package in packages:
        if interrupted:
            print("Operation cancelled by user")
            return False
            
        for version in versions:
            if interrupted:
                print("Operation cancelled by user")
                return False
                
            registry = "docker.io/microfocusidolserver"
            image = f"{registry}/{package}:{version}"
            if dry_run:
                print(f"[DRY RUN] Would pull from {registry}: {package}:{version}")
            else:
                print(f"Pulling from {registry}: {package}:{version}")
                try:
                    result = subprocess.run(['docker', 'pull', image], check=True)
                    if result.returncode != 0:
                        print(f"Failed to pull {image}")
                        success = False
                except subprocess.CalledProcessError as e:
                    print(f"Failed to pull {image}: {str(e)}")
                    success = False
                except KeyboardInterrupt:
                    print("\nOperation cancelled by user")
                    return False
    
    if not success:
        print("\nSome images failed to pull")
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
