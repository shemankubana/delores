import requests
from bs4 import BeautifulSoup
import logging
import time
from langchain_core.documents import Document

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TARGETS = [
    "https://support.irembo.gov.rw",
    "https://osc.freshdesk.com",
    "https://iremboplus.freshdesk.com"
]

def get_soup(url):
    """Helper to get BeautifulSoup object with error handling and headers"""
    try:
        # User-Agent is important so Freshdesk doesn't block the script
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            return BeautifulSoup(resp.content, 'html.parser')
        else:
            logger.warning(f"      ⚠️ Failed to access {url} (Status: {resp.status_code})")
    except Exception as e:
        logger.error(f"      ⚠️ Connection error to {url}: {e}")
    return None

def crawl_freshdesk_portal(base_url):
    """
    Crawls Home -> Folders -> Articles
    """
    article_urls = set() # Use a set to avoid duplicates
    
    # 1. Start at the Solutions Home page
    solutions_url = f"{base_url}/support/solutions"
    logger.info(f"   🔍 Crawling structure: {solutions_url}")
    
    soup = get_soup(solutions_url)
    if not soup:
        logger.warning(f"      ❌ Could not access solutions page. Trying homepage...")
        soup = get_soup(base_url)
        if not soup: return []

    # 2. Find all Folder Links
    # Freshdesk folder links usually contain "/support/solutions/folders/"
    folder_links = []
    for a in soup.find_all('a', href=True):
        if "/support/solutions/folders/" in a['href']:
            full_link = a['href'] if a['href'].startswith('http') else f"{base_url}{a['href']}"
            folder_links.append(full_link)
    
    # Remove duplicates
    folder_links = list(set(folder_links))
    logger.info(f"      found {len(folder_links)} folders. Scanning articles...")

    # 3. Visit each Folder to find Articles
    for i, folder_url in enumerate(folder_links):
        f_soup = get_soup(folder_url)
        if not f_soup: continue
        
        # Find Article Links inside the folder
        # Freshdesk article links contain "/support/solutions/articles/"
        found_in_folder = 0
        for a in f_soup.find_all('a', href=True):
            if "/support/solutions/articles/" in a['href']:
                full_article = a['href'] if a['href'].startswith('http') else f"{base_url}{a['href']}"
                if full_article not in article_urls:
                    article_urls.add(full_article)
                    found_in_folder += 1
        
        logger.info(f"      [{i+1}/{len(folder_links)}] Found {found_in_folder} articles in folder.")
        # Be polite to the server
        time.sleep(0.5)
        
    logger.info(f"   ✅ Found {len(article_urls)} total unique articles on {base_url}")
    return list(article_urls)

def scrape_article_content(url):
    soup = get_soup(url)
    if not soup: return None
    
    try:
        title_tag = soup.find('h1')
        title = title_tag.get_text(strip=True) if title_tag else "No Title"
        
        # Try finding the body in common Freshdesk classes
        body = soup.find('div', class_='article-body') or \
               soup.find('div', class_='description-text') or \
               soup.find('div', class_='g-content') # Sometimes used in custom themes
               
        if body:
            # Remove scripts and styles
            for s in body(["script", "style"]): s.decompose()
            text = body.get_text(separator="\n", strip=True)
            return {
                "title": title,
                "content": text,
                "url": url
            }
    except Exception as e:
        logger.error(f"Error extracting content from {url}: {e}")
        pass
    return None

def scrape_portal(ignored_arg=None):
    """
    Scrapes all targets and returns a list of LangChain Documents.
    """
    all_documents = []
    
    for site in TARGETS:
        logger.info(f"\n🚀 Processing Site: {site}")
        
        # STEP 1: Crawl to find links
        urls = crawl_freshdesk_portal(site)
        
        # STEP 2: Scrape Content
        for i, url in enumerate(urls):
            # logger.info(f"   Processing {i+1}/{len(urls)}")
            data = scrape_article_content(url)
            
            if data and len(data["content"]) > 50:
                 doc = Document(
                     page_content=data["content"],
                     metadata={
                         "source": data["url"],
                         "title": data["title"],
                         "product": "Irembo"
                     }
                 )
                 all_documents.append(doc)
            
            # Be polite
            time.sleep(0.2)
    
    logger.info(f"🎉 Done! Scraped {len(all_documents)} documents.")
    return all_documents

if __name__ == "__main__":
    docs = scrape_portal()
    print(f"Scraped {len(docs)} documents.")
