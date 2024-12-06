import docker

# Initialize the Docker client
client = docker.from_env()

# Define the old and new repositories
old_repo = "microfocusidolserver"
new_repo = "registry.gitlab.docdirekt.rijkscloud.nl/advanced-search/content-services/idol"

# Get a list of images from the old repository
images = client.images.list()

# Loop through each image and retag it
for image in images:
    for tag in image.tags:
        if tag.startswith(f"{old_repo}/"):
            # Extract package name and tag from the image name
            package_name = tag.split('/')[1].split(':')[0]
            tag_name = tag.split(':')[1]
            
            # Define the new image name
            new_image = f"{new_repo}/{package_name}:{tag_name}"
            
            # Retag the image
            print(f"Retagging {tag} to {new_image}")
            image.tag(new_image)

            # Optionally remove the old image tag
            # client.images.remove(tag)
