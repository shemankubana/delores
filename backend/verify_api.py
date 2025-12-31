import requests
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("FRESHDESK_API_KEY")
if not api_key:
    print("❌ Error: FRESHDESK_API_KEY not found in .env")
    exit(1)

# List of potential domains to try
potential_domains = [
    "https://irembo.freshdesk.com",
    "https://iremboagent.freshdesk.com/en/support/home",
    "https://osc.freshdesk.com",
    "https://iremboplus.freshdesk.com"
]

print(f"🔑 Testing API Key: {api_key[:5]}...{api_key[-3:]}")

for domain in potential_domains:
    url = f"{domain}/api/v2/tickets" # Tickets endpoint is usually a good connectivity check
    print(f"\nTesting: {domain}")
    try:
        response = requests.get(url, auth=(api_key, "X"), timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✅ SUCCESS! This is your correct API Domain.")
            print(f"   Please update your scraper to use: {domain}")
        elif response.status_code == 401:
            print(f"   ❌ Authentication Failed (Key invalid for this domain)")
        elif response.status_code == 404:
            print(f"   ❌ Endpoint Not Found (This might not be an API domain)")
        else:
            print(f"   ⚠️ Unexpected: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Connection Error: {e}")
