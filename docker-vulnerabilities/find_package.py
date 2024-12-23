import requests
from bs4 import BeautifulSoup
import re
from concurrent.futures import ThreadPoolExecutor
from packaging import version

REPOS = [
    "https://mirror.stream.centos.org/9-stream/BaseOS/x86_64/os/Packages/",
    "https://repo.almalinux.org/almalinux/9/BaseOS/x86_64/os/Packages/",
    "https://dl.rockylinux.org/pub/rocky/9/BaseOS/x86_64/os/Packages/"
]

def parse_rpm_version(rpm_name):
    """Extract version information from RPM name."""
    match = re.match(r'krb5-libs-([0-9\._-]+)\.el9.*\.rpm', rpm_name)
    if match:
        return match.group(1)
    return None

def scan_repo(repo_url):
    """Scan a single repository for krb5-libs packages."""
    try:
        print(f"Scanning {repo_url}...")
        response = requests.get(repo_url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        packages = []
        
        # Find all links that contain krb5-libs
        for link in soup.find_all('a'):
            href = link.get('href', '')
            if 'krb5-libs' in href and href.endswith('.rpm'):
                ver = parse_rpm_version(href)
                if ver:
                    packages.append({
                        'name': href,
                        'version': ver,
                        'url': repo_url + href if repo_url.endswith('/') else repo_url + '/' + href
                    })
        
        return packages
    except Exception as e:
        print(f"Error scanning {repo_url}: {str(e)}")
        return []

def main():
    print("Scanning repositories for krb5-libs packages...")
    all_packages = []
    
    # Use ThreadPoolExecutor to scan repos in parallel
    with ThreadPoolExecutor(max_workers=len(REPOS)) as executor:
        results = executor.map(scan_repo, REPOS)
        for packages in results:
            all_packages.extend(packages)
    
    if not all_packages:
        print("No packages found!")
        return
    
    # Sort packages by version
    all_packages.sort(key=lambda x: version.parse(x['version']), reverse=True)
    
    print("\nFound packages (sorted by version):")
    print("-" * 80)
    for pkg in all_packages:
        print(f"Version: {pkg['version']}")
        print(f"Name: {pkg['name']}")
        print(f"URL: {pkg['url']}")
        print("-" * 80)
    
    print("\nTo download and install the latest version:")
    latest = all_packages[0]
    print(f"curl -O {latest['url']}")
    print(f"rpm -Uvh {latest['name']}")

if __name__ == "__main__":
    main()