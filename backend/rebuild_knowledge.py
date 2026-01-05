import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.scraper import scrape_portal
from backend.rag import RAGPipeline

def rebuild():
    print("🚀 Starting Knowledge Base Rebuild...")
    
    # 1. Scrape
    docs = scrape_portal()
    
    # 2. Ingest
    if docs:
        rag = RAGPipeline()
        rag.initialize_vector_store(docs)
        print("✅ Rebuild Complete!")
    else:
        print("❌ No documents found.")

if __name__ == "__main__":
    rebuild()
