
import requests
from bs4 import BeautifulSoup

def debug_links():
    url = "https://support.irembo.gov.rw/support/solutions"
    print(f"Fetching {url}...")
    
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
    try:
        resp = requests.get(url, headers=headers)
        print(f"Status Code: {resp.status_code}")
        
        soup = BeautifulSoup(resp.content, 'html.parser')
        
        print("\n--- All Links Found ---")
        links = soup.find_all('a', href=True)
        for a in links:
            href = a['href']
            text = a.get_text(strip=True)
            print(f"Text: {text[:30]}... | Href: {href}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_links()
