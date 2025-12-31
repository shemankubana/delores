import requests
from bs4 import BeautifulSoup

url = "https://iremboagent.freshdesk.com/en/support/solutions"
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

print(f"Fetching {url}...")
resp = requests.get(url, headers=headers)
print(f"Status: {resp.status_code}")
print(f"Final URL: {resp.url}")

soup = BeautifulSoup(resp.content, 'html.parser')

print("\n--- Links Found ---")
count = 0
for a in soup.find_all('a', href=True):
    href = a['href']
    if "/folders/" in href or "/categories/" in href:
        print(f"Found relevant link: {href}")
        count += 1

print(f"\nTotal relevant links: {count}")

if count == 0:
    print("\n--- HTML PREVIEW (First 2000 chars) ---")
    print(soup.prettify()[:2000])
