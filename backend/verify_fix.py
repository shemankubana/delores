import sys
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Add current directory to path so we can import backend
sys.path.append(os.getcwd())

try:
    from backend.scraper import crawl_freshdesk_portal
except ImportError as e:
    print(f"Import failed: {e}")
    # Try adjusting path if running from root
    sys.path.append(os.path.join(os.getcwd(), 'backend'))
    from scraper import crawl_freshdesk_portal

url = "https://iremboagent.freshdesk.com/en/support/home"
print(f"Crawling {url}...")
articles = crawl_freshdesk_portal(url)
print(f"Found {len(articles)} articles.")

if len(articles) > 0:
    print("✅ SUCCESS: Articles found!")
    for a in list(articles)[:5]:
        print(f" - {a}")
else:
    print("❌ FAILURE: No articles found.")
