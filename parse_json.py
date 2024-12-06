import json
import pandas as pd

# Load JSON data
with open('repo_tags.json', 'r') as file:
    data = json.load(file)

# Normalize JSON data to tabular format
df = pd.json_normalize(data)

# Save to Excel
df.to_excel('docker_repo_tags.xlsx', index=False)

print("Data saved to docker_repo_tags.xlsx")

