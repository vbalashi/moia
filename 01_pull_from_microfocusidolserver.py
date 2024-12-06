import os

# List of packages
packages = [
    'content',
    'category',
    'community',
    'find',
    'dah',
    'omnigroupserver',
    'agentstore',
    'categorisation-agentstore',
    'controller',
    'coordinator',
    'dataadmin',
    'dih',
    'eductionserver',
    'qms',
    'qms-agentstore',
    'siteadmin',
    'statsserver',
    'view'
]

# List of versions
versions = [
    '23.4',
    '24.1',
    '24.2'
]

# Iterate over all packages and versions
for package in packages:
    for version in versions:
        # Construct the Docker image name
        image = f"microfocusidolserver/{package}:{version}"
        # Pull the Docker image
        command = f"docker pull {image}"
        print(f"Executing: {command}")
        os.system(command)
