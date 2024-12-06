import docker
import datetime
import time
import sys

# Initialize the Docker client
client = docker.from_env()

# Define the new repository
new_repo = "registry.gitlab.docdirekt.rijkscloud.nl/advanced-search/content-services/idol"

# Get a list of images
images = client.images.list()

# Get the current timestamp
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

# Open a log file with the current timestamp in the name
log_file_path = f"docker_push_log_{timestamp}.log"
with open(log_file_path, 'w') as log_file:
    # Loop through each image and push it if it matches the new repository format
    for image in images:
        for tag in image.tags:
            if tag.startswith(f"{new_repo}/"):
                # Print image name
                print(f"Image: {tag}")

                # Record the start time
                start_time = time.time()

                try:
                    # Push the new image to the remote repository and stream the response
                    response = client.images.push(tag, stream=True, decode=True)
                    
                    # Initialize variables to track progress
                    total_bytes = 0
                    last_update = start_time

                    # Process the streamed response
                    for chunk in response:
                        if 'status' in chunk:
                            # If status is 'Pushed', the push is successful
                            if chunk['status'] == 'Pushed':
                                result = "Pushed successfully"
                            elif chunk['status'] == 'Layer already exists':
                                result = "Layer already exists"
                        if 'progressDetail' in chunk and 'total' in chunk['progressDetail']:
                            total_bytes = chunk['progressDetail']['total']

                        # Print the current status
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
                
                # Record the end time
                end_time = time.time()
                elapsed_time = end_time - start_time

                # Log the result with a timestamp
                log_entry = f"\n{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}, {tag}, {result}, Elapsed time: {elapsed_time:.2f} seconds\n"
                
                # Print to terminal and move to the next line
                sys.stdout.write(log_entry)
                sys.stdout.flush()
                
                # Write to log file
                log_file.write(log_entry)
