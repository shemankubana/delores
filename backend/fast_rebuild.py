import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.scraper import scrape_portal
from backend.rag import RAGPipeline

def fast_rebuild():
    print("🚀 Starting FAST Knowledge Base Rebuild (Limit 15, No Images)...")
    
    # 1. Scrape with limits
    # We scrape 15 docs. Since homepage is added to list, it should be included.
    docs = scrape_portal(limit=15, skip_images=True)
    
    # 2. Ingest
    if docs:
        rag = RAGPipeline()
        rag.initialize_vector_store(docs)
        print("✅ Rebuild Complete!")
    else:
        print("❌ No documents found.")

if __name__ == "__main__":
    fast_rebuild()
