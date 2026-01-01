import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Fetch one of the "solutions" links found in the previous step
url = "https://iremboagent.freshdesk.com/en/support/solutions/47000525597"
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

print(f"Fetching {url}...")
resp = requests.get(url, headers=headers)
print(f"Status: {resp.status_code}")
print(f"Final URL: {resp.url}")

soup = BeautifulSoup(resp.content, 'html.parser')
print(f"Page Title: {soup.title.string if soup.title else 'No Title'}")

print("\n--- Links found in this page ---")
count = 0
for a in soup.find_all('a', href=True):
    href = a['href']
    # Print links that look like they might be folders or articles
    if "/solutions/" in href or "/articles/" in href:
        print(f"Link: {href}")
        count += 1

print(f"\nTotal relevant links found: {count}")
