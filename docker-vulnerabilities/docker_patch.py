#!/usr/bin/env python3

import docker
import logging
import os
import sys
import argparse
import tarfile
import tempfile
import signal
from datetime import datetime
from pathlib import Path

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Patch Docker images with RPM files.')
    parser.add_argument('--images-file', default='images.txt',
                      help='File containing list of images to patch (default: images.txt)')
    parser.add_argument('--rpms-file', default='rpms.txt',
                      help='File containing list of RPM files to install (default: rpms.txt)')
    parser.add_argument('--no-dry-run', action='store_true',
                      help='Execute actual changes (default: dry-run mode)')
    return parser.parse_args()

def setup_logging():
    """Configure logging to both file and console."""
    log_dir = Path('./logs')
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f'docker_patch_{timestamp}.log'
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def load_config(file_path):
    """Load configuration from file, skipping empty lines and comments."""
    try:
        with open(file_path, 'r') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except Exception as e:
        raise Exception(f"Failed to load config file {file_path}: {str(e)}")

def create_tar_archive(files):
    """Create a temporary tar archive containing the specified files."""
    temp_dir = tempfile.mkdtemp()
    archive_path = os.path.join(temp_dir, 'files.tar')
    
    with tarfile.open(archive_path, 'w') as tar:
        for file_path in files:
            tar.add(file_path, arcname=os.path.basename(file_path))
    
    return archive_path

def cleanup_containers(client, logger):
    """Clean up any leftover containers from previous runs."""
    try:
        containers = client.containers.list(all=True, filters={'name': 'patch_temp_*'})
        if containers:
            logger.info(f"Found {len(containers)} leftover containers from previous runs")
            for container in containers:
                try:
                    container.stop()
                    container.remove()
                    logger.info(f"Cleaned up container: {container.short_id}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup container {container.short_id}: {str(e)}")
    except Exception as e:
        logger.error(f"Error during container cleanup: {str(e)}")

def patch_docker_image(client, image_spec, rpm_files, logger, dry_run=True):
    """Patch a single Docker image with specified RPM files."""
    container = None
    try:
        image_name, tag = image_spec.split(':')
        new_tag = f"{tag}_fix"
        logger.info(f"Processing image: {image_spec}")

        if dry_run:
            logger.info("[DRY-RUN] Would pull image if not present")
            logger.info("[DRY-RUN] Would create temporary container")
            for rpm_file in rpm_files:
                rpm_path = Path(rpm_file)
                if not rpm_path.exists():
                    raise FileNotFoundError(f"RPM file not found: {rpm_file}")
                logger.info(f"[DRY-RUN] Would copy and install: {rpm_path.name}")
            logger.info(f"[DRY-RUN] Would create new image: {image_name}:{new_tag}")
            return True

        # Pull the image if not present
        try:
            client.images.get(image_spec)
        except docker.errors.ImageNotFound:
            logger.info(f"Pulling image: {image_spec}")
            client.images.pull(image_name, tag)

        # Create and start temporary container with unique name
        container_name = f"patch_temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.getpid()}"
        container = client.containers.create(
            image_spec,
            user='root',  # Ensure we run as root for RPM installation
            name=container_name
        )
        logger.info(f"Created temporary container: {container.short_id}")

        try:
            # Verify all RPM files exist
            for rpm_file in rpm_files:
                rpm_path = Path(rpm_file)
                if not rpm_path.exists():
                    raise FileNotFoundError(f"RPM file not found: {rpm_file}")

            # Create tar archive of RPM files
            logger.info("Creating temporary archive of RPM files")
            archive_path = create_tar_archive(rpm_files)

            # Copy archive to container
            logger.info("Copying RPM files to container")
            with open(archive_path, 'rb') as f:
                container.put_archive('/tmp', f.read())

            # Start container
            container.start()

            # Install RPMs
            for rpm_file in rpm_files:
                rpm_name = os.path.basename(rpm_file)
                logger.info(f"Installing {rpm_name}")
                exit_code, output = container.exec_run(f"rpm -Uvh /tmp/{rpm_name}")
                if exit_code != 0:
                    raise Exception(f"Failed to install {rpm_name}: {output.decode()}")

            # Clean up RPMs
            container.exec_run("rm -f /tmp/*.rpm")
            
            # Commit changes to new image
            new_image_name = f"{image_name}:{new_tag}"
            container.commit(repository=image_name, tag=new_tag)
            logger.info(f"Created new image: {new_image_name}")

            return True

        finally:
            # Cleanup
            try:
                if container:
                    container.stop()
                    container.remove()
                    logger.info(f"Removed temporary container: {container.short_id}")
            except Exception as e:
                logger.warning(f"Failed to cleanup container: {str(e)}")

            # Clean up temporary tar file
            try:
                if 'archive_path' in locals():
                    os.unlink(archive_path)
                    os.rmdir(os.path.dirname(archive_path))
            except Exception as e:
                logger.warning(f"Failed to cleanup temporary files: {str(e)}")

    except Exception as e:
        logger.error(f"Failed to patch {image_spec}: {str(e)}")
        return False

def main():
    args = parse_args()
    logger = setup_logging()
    client = docker.from_env()
    
    def signal_handler(signum, frame):
        logger.info("\nReceived interrupt signal. Cleaning up...")
        cleanup_containers(client, logger)
        sys.exit(1)

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Clean up any leftover containers from previous runs
        cleanup_containers(client, logger)

        # Load configurations
        images_list = load_config(args.images_file)
        rpm_list = load_config(args.rpms_file)
        
        logger.info(f"Found {len(images_list)} images to process")
        logger.info(f"Found {len(rpm_list)} RPM files to install")
        logger.info(f"Running in {'LIVE' if args.no_dry_run else 'DRY-RUN'} mode")

        # Process each image
        success_count = 0
        for image_spec in images_list:
            if patch_docker_image(client, image_spec, rpm_list, logger, dry_run=not args.no_dry_run):
                success_count += 1

        # Summary
        mode = 'LIVE' if args.no_dry_run else 'DRY-RUN'
        logger.info(f"[{mode}] Patching completed. Successfully processed {success_count}/{len(images_list)} images")

    except Exception as e:
        logger.error(f"Script execution failed: {str(e)}")
        sys.exit(1)
    finally:
        cleanup_containers(client, logger)

if __name__ == "__main__":
    main() 