import requests
import logging
import time
from io import BytesIO
from PIL import Image
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from langchain_core.documents import Document

# Import our new Local Model Manager
from .local_model import local_models

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TARGETS = [
    "https://iremboagent.freshdesk.com",
    "https://osc.freshdesk.com",
    "https://iremboplus.freshdesk.com"
]

def get_soup(url):
    """Fetches a URL with a browser-like User-Agent."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
        resp = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        
        # Check for authentication redirects
        if "login" in resp.url.lower() or resp.status_code == 403:
            logger.warning(f"      ⚠️ Authentication required or forbidden: {url}")
            return None, None
            
        if resp.status_code == 200:
            return BeautifulSoup(resp.content, 'html.parser'), resp.url
        logger.warning(f"      ⚠️ Status {resp.status_code} for {url}")
    except Exception as e:
        logger.error(f"      ⚠️ Connection error: {e}")
    return None, None

def process_images_in_html(soup, base_url):
    """
    Finds <img> tags, downloads them, generates captions using BLIP, 
    and appends the description to the text.
    """
    captions = []
    images = soup.find_all('img')
    
    if images:
        logger.info(f"      Found {len(images)} images to process...")
        
    for img in images:
        src = img.get('src')
        if not src: continue
        
        full_img_url = urljoin(base_url, src)
        try:
            # Download image bytes
            logger.info(f"      Processing Image: {full_img_url}...")
            # Use headers to avoid 403 blocks on images
            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'} 
            img_resp = requests.get(full_img_url, headers=headers, timeout=5)
            
            if img_resp.status_code == 200:
                image = Image.open(BytesIO(img_resp.content)).convert('RGB')
                
                # Generate Caption using Local BLIP Model
                caption = local_models.caption_image(image)
                captions.append(f"[Image Description: {caption}]")
                logger.info(f"         ✅ Captioned: {caption}")
            else:
                logger.warning(f"         ❌ Failed to download image (Status {img_resp.status_code})")
                
        except Exception as e:
            logger.error(f"         ❌ Image processing error: {e}")
            
    return "\n".join(captions)

def scrape_article_html(url):
    """
    Enhanced article scraper with multiple selector strategies and better debugging.
    """
    logger.info(f"   📄 Scraping Article: {url}")
    soup, real_url = get_soup(url)
    if not soup: 
        logger.warning(f"      ❌ Failed to fetch HTML for {url}")
        return None
        
    try:
        # Extract Title
        title = "No Title"
        title_elem = soup.find('h1') or soup.find('h2', class_='article-title')
        if title_elem:
            title = title_elem.get_text(strip=True)
        
        # Strategy 1: Try multiple Freshdesk-specific selectors
        body = None
        selectors = [
            # Freshdesk common selectors
            {'class_': 'article-body'},
            {'class_': 'fr-view'},  # Froala editor
            {'class_': 'article-content'},
            {'class_': 'solution-article-content'},
            {'id': 'article-content'},
            {'id': 'article-body'},
            {'itemprop': 'articleBody'},
            
            # Generic content selectors
            {'class_': 'description-text'},
            {'class_': 'g-content'},
            {'class_': 'fw-article-content'},
            {'class_': 'content-body'},
        ]
        
        for s in selectors:
            body = soup.find('div', **s) or soup.find('section', **s)
            if body and body.get_text(strip=True): 
                logger.info(f"      ✅ Found body with selector: {s}")
                break
        
        # Strategy 2: Try article tag
        if not body or not body.get_text(strip=True):
            body = soup.find('article')
            if body and body.get_text(strip=True):
                logger.info(f"      ✅ Found body with <article> tag")
        
        # Strategy 3: Find main content area
        if not body or not body.get_text(strip=True):
            body = soup.find('main')
            if body and body.get_text(strip=True):
                logger.info(f"      ✅ Found body with <main> tag")
        
        # Strategy 4: Debug - print available divs and try the most promising one
        if not body or not body.get_text(strip=True):
            logger.warning(f"      ⚠️ No content body found with standard selectors")
            logger.info(f"      🔍 Analyzing page structure...")
            
            # Get all divs with classes and find the one with most text
            all_divs = soup.find_all('div', class_=True)
            best_div = None
            max_text_length = 0
            
            for div in all_divs:
                text = div.get_text(strip=True)
                if len(text) > max_text_length and len(text) > 100:  # Minimum 100 chars
                    # Avoid navigation, footer, header
                    classes = ' '.join(div.get('class', []))
                    if not any(skip in classes.lower() for skip in ['nav', 'menu', 'footer', 'header', 'sidebar']):
                        max_text_length = len(text)
                        best_div = div
            
            if best_div:
                body = best_div
                classes = ' '.join(best_div.get('class', []))
                logger.info(f"      ✅ Found best content div with classes: {classes}")
                logger.info(f"      ✅ Content length: {max_text_length} chars")
            else:
                # Last resort: dump some classes for debugging
                sample_classes = [' '.join(d.get('class', [])) for d in all_divs[:10]]
                logger.warning(f"      ⚠️ Sample div classes found: {sample_classes}")

        if body:
            # 1. Process Images BEFORE stripping tags
            image_captions = process_images_in_html(body, real_url)
            
            # 2. Clean up junk
            for s in body(["script", "style", "form", "button", "nav", "header", "footer"]): 
                s.decompose()
            
            # Extract text
            text = body.get_text(separator="\n", strip=True)
            
            # Clean up excessive whitespace
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            text = '\n'.join(lines)
            
            # 3. Combine Text + Image Captions
            if image_captions:
                final_content = f"{text}\n\n--- Visual Context ---\n{image_captions}"
            else:
                final_content = text
            
            # Validate content length
            if len(final_content.strip()) < 50:
                logger.warning(f"      ⚠️ Content too short ({len(final_content)} chars)")
                return None
            
            logger.info(f"      ✅ Successfully extracted {len(final_content)} characters")
            return {"title": title, "content": final_content, "url": real_url}
        else:
            logger.warning(f"      ⚠️ No usable content body found for {url}")
            
    except Exception as e:
        logger.error(f"      ❌ Error parsing {url}: {e}")
    return None

def crawl_freshdesk_portal(base_url):
    """
    Robust Crawler: Home -> Solutions/Categories -> Folders -> Articles
    """
    article_urls = set()
    
    # 1. Homepage
    logger.info(f"   🕷️ Connecting to {base_url}...")
    soup, real_url = get_soup(base_url)
    if not soup: return []

    # 2. Find Solutions Link
    solutions_url = urljoin(real_url, "/support/solutions")
    
    # Handle language variants
    if "/en/support" in real_url:
        solutions_url = real_url.replace("/home", "/solutions") if "/home" in real_url else urljoin(real_url, "/en/support/solutions")
    elif "/fr/support" in real_url:
        solutions_url = real_url.replace("/home", "/solutions") if "/home" in real_url else urljoin(real_url, "/fr/support/solutions")
    elif "support.irembo.gov.rw" in real_url:
        solutions_url = "https://support.irembo.gov.rw/support/solutions"

    logger.info(f"   🕷️ Checking Solutions Page: {solutions_url}")
    soup, _ = get_soup(solutions_url)
    
    if not soup:
        logger.info("   ⚠️ Could not access solutions page, scanning homepage links instead...")
        soup, _ = get_soup(real_url)
        if not soup:
            return []

    # 3. Find Folders & Categories
    folder_links = []
    
    # Strategy A: Direct Folder Links
    for a in soup.find_all('a', href=True):
        full_link = urljoin(real_url, a['href'])
        if "/folders/" in a['href']:
            folder_links.append(full_link)
        # Strategy B: Category Links -> Folders
        elif "/categories/" in a['href']:
            # Dig into category
            time.sleep(0.3)  # Be nice to the server
            cat_soup, _ = get_soup(full_link)
            if cat_soup:
                for ca in cat_soup.find_all('a', href=True):
                    if "/folders/" in ca['href']:
                        folder_links.append(urljoin(full_link, ca['href']))
            
    folder_links = list(set(folder_links))
    logger.info(f"      Found {len(folder_links)} folders.")

    # 4. Dig into Folders to find Articles
    for folder_url in folder_links:
        time.sleep(0.5)  # Rate limiting
        f_soup, _ = get_soup(folder_url)
        if not f_soup: continue
        
        count = 0
        for a in f_soup.find_all('a', href=True):
            if "/articles/" in a['href']:
                full_art = urljoin(folder_url, a['href'])
                if full_art not in article_urls:
                    article_urls.add(full_art)
                    count += 1
        
        if count > 0:
            logger.info(f"         Found {count} articles in folder: {folder_url}")
        
    return list(article_urls)

def scrape_portal(ignored_arg=None):
    """
    Main scraping function that processes all target sites.
    """
    all_documents = []
    
    for site in TARGETS:
        logger.info(f"\n🚀 Processing Site: {site}")
        
        # Crawl the portal to find article URLs
        urls = crawl_freshdesk_portal(site)
        logger.info(f"   🕷️ Found {len(urls)} articles to process.")
        
        for i, url in enumerate(urls):
            data = scrape_article_html(url)
            
            if data and len(data["content"]) > 50:
                all_documents.append(Document(
                    page_content=data["content"],
                    metadata={
                        "source": data["url"], 
                        "title": data["title"], 
                        "product": "Irembo"
                    }
                ))
                logger.info(f"      ✅ Added document: {data['title'][:50]}...")
            else:
                logger.info(f"      🗑️ Dropped {url} (Empty/Short)")
            
            # Rate limiting - be respectful
            if (i + 1) % 5 == 0: 
                time.sleep(1)
                logger.info(f"      💤 Rate limiting... ({i + 1}/{len(urls)} processed)")

    logger.info(f"\n🎉 TOTAL SCRAPED: {len(all_documents)} documents.")
    return all_documents

if __name__ == "__main__":
    docs = scrape_portal()
    logger.info(f"\n📊 Final Results:")
    for i, doc in enumerate(docs[:5]):  # Show first 5
        logger.info(f"   {i+1}. {doc.metadata['title']}")
        logger.info(f"      Content length: {len(doc.page_content)} chars")
        logger.info(f"      Source: {doc.metadata['source']}")