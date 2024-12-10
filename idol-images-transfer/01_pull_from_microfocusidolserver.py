import os
import argparse
import requests
import pathlib
import datetime
import signal
import sys
import subprocess
from dotenv import load_dotenv
import tempfile

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

def check_docker_context():
    """Get information about current Docker context and whether it's remote."""
    try:
        # Get current context name
        result = subprocess.run(['docker', 'context', 'show'], capture_output=True, text=True)
        current_context = result.stdout.strip()
        
        # Get context details
        inspect_result = subprocess.run(['docker', 'context', 'inspect', current_context], capture_output=True, text=True)
        
        return {
            'name': current_context,
            'details': inspect_result.stdout.strip(),
            'is_remote': 'ssh://' in inspect_result.stdout or 'tcp://' in inspect_result.stdout
        }
    except Exception as e:
        print(f"Warning: Could not get Docker context information: {str(e)}")
        return {'name': 'unknown', 'details': '', 'is_remote': False}

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
        if not check_docker_available()[0]:
            return False

        # Get context information
        context = check_docker_context()
        print(f"\nUsing Docker context: {context['name']}")
        
        # Check if already logged in
        check_cmd = "docker info | grep Username"
        check_result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
        if username in check_result.stdout:
            print(f"Already logged in as {username}")
            return True
            
        if context['is_remote']:
            print("Detected remote Docker context")
            # For remote contexts, try different login approaches
            
            # First, try without password-stdin
            print("Attempting login method 1...")
            cmd1 = f'docker login -u {username} --password "{password}" docker.io'
            process1 = subprocess.run(cmd1, shell=True, capture_output=True, text=True)
            
            if process1.returncode == 0 or "Login Succeeded" in process1.stdout:
                print("Successfully authenticated to Docker Hub")
                return True
                
            # If that fails, try with password-stdin
            print("Attempting login method 2...")
            cmd2 = f'echo "{password}" | docker login -u {username} --password-stdin docker.io'
            process2 = subprocess.run(cmd2, shell=True, capture_output=True, text=True)
            
            if process2.returncode == 0 or "Login Succeeded" in process2.stdout:
                print("Successfully authenticated to Docker Hub")
                return True
                
            # If both fail, try one more time with Python's base64 handling
            print("Attempting login method 3...")
            import base64
            import tempfile
            
            try:
                # Create a temporary file for the base64-decoded password
                with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp:
                    temp.write(password)
                    temp.flush()
                    temp_path = temp.name
                
                # Use the temporary file for login
                cmd3 = f'docker login -u {username} --password-stdin docker.io < "{temp_path}"'
                process3 = subprocess.run(cmd3, shell=True, capture_output=True, text=True)
                
                if process3.returncode == 0 or "Login Succeeded" in process3.stdout:
                    print("Successfully authenticated to Docker Hub")
                    return True
            finally:
                # Clean up the temporary file
                try:
                    os.unlink(temp_path)
                except Exception:
                    pass
            
            # If all methods fail, print the error from the last attempt
            error = process3.stderr.strip()
            if "unauthorized: incorrect username or password" in error:
                print("\nError: Invalid credentials")
                print(f"Username being used: {username}")
                print("Please verify your credentials in .env file")
                print("Note: The password is hidden for security")
            else:
                print(f"Docker login failed: {error}")
            return False
        else:
            # For local context, use the standard password-stdin method
            cmd = ['docker', 'login', '--username', username, '--password-stdin', 'docker.io']
            process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate(input=password.encode())
            
            if process.returncode == 0 or "Login Succeeded" in stdout.decode():
                print("Successfully authenticated to Docker Hub")
                return True
            else:
                print(f"Docker login failed: {stderr.decode().strip()}")
                return False
                
    except Exception as e:
        print(f"Error during Docker login: {str(e)}")
        return False

def check_existing_auth():
    """Check if there's an existing Docker authentication."""
    try:
        result = subprocess.run(['docker', 'info'], capture_output=True, text=True)
        return 'Username:' in result.stdout
    except Exception:
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
        
        # Add context information
        context = check_docker_context()
        print(f"  - Context: {context['name']}")
        print(f"  - Remote: {'Yes' if context['is_remote'] else 'No'}")
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

def pull_images(packages, versions, dry_run=True, use_existing_auth=False):
    """Pull Docker images for given packages and versions."""
    global interrupted
    
    # Check if Docker is available first
    is_available, error_msg = check_docker_available()
    if not is_available:
        print(f"\nCannot proceed: {error_msg}")
        return False
    
    # Handle authentication
    if use_existing_auth:
        if not check_existing_auth():
            print("\nNo existing Docker authentication found.")
            print("Please login manually first or run without --use-existing-auth")
            return False
        print("Using existing Docker authentication")
    else:
        # Check authentication and perform login
        print("Authenticating to Docker Hub...")
        if not docker_login():
            print("\nAuthentication failed. Please ensure:")
            print("1. Docker is properly installed and running")
            print("2. Your credentials in .env file are correct")
            print("3. Your internet connectivity to Docker Hub")
            print("\nAlternatively, you can:")
            print("1. Login manually on the Docker host")
            print("2. Run this script with --use-existing-auth")
            return False

    success = True
    failed_pulls = []
    
    for package in packages:
        if interrupted:
            print("\nOperation cancelled by user")
            break
            
        for version in versions:
            if interrupted:
                print("\nOperation cancelled by user")
                break
                
            registry = "docker.io/microfocusidolserver"
            image = f"{registry}/{package}:{version}"
            if dry_run:
                print(f"[DRY RUN] Would pull from {registry}: {package}:{version}")
            else:
                print(f"\nPulling from {registry}: {package}:{version}")
                try:
                    result = subprocess.run(['docker', 'pull', image], 
                                         capture_output=True, 
                                         text=True,
                                         check=True)
                    print("Successfully pulled image")
                except subprocess.CalledProcessError as e:
                    error_msg = e.stderr.strip() if e.stderr else str(e)
                    print(f"Failed to pull image: {error_msg}")
                    failed_pulls.append(package)
                    success = False
                except KeyboardInterrupt:
                    print("\nOperation cancelled by user")
                    return False
    
    if not success:
        print("\nThe following packages failed to pull:")
        for pkg in failed_pulls:
            print(f"  - {pkg}")
        print("\nPlease check:")
        print("1. Your Docker Hub account has access to these repositories")
        print("2. The package names and versions are correct")
        print("3. Your internet connection is stable")
    
    return success

def main():
    parser = argparse.ArgumentParser(description='Pull MicroFocus IDOL Docker images')
    parser.add_argument('--packages-file', help='Path to file containing package names')
    parser.add_argument('--versions-file', help='Path to file containing versions')
    parser.add_argument('--no-dry-run', action='store_true', help='Actually pull images instead of dry run')
    parser.add_argument('--use-existing-auth', action='store_true', help='Use existing Docker authentication instead of logging in')
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
    success = pull_images(packages, versions, dry_run=not args.no_dry_run, use_existing_auth=args.use_existing_auth)
    if not success:
        print("Some images failed to pull")
        exit(1)

if __name__ == "__main__":
    main()
