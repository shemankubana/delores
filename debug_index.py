from backend.rag import RAGPipeline

def inspect_index():
    rag = RAGPipeline()
    rag.load_vector_store()
    
    query = "What are the working hours for Irembo support?"
    print(f"Query: {query}")
    
    results = rag.retrieve(query, k=5)
    for i, doc in enumerate(results):
        print(f"\nResult {i+1}:")
        print(f"Source: {doc.metadata.get('source')}")
        print(f"Content Preview: {doc.page_content[:300]}...")

if __name__ == "__main__":
    inspect_index()
