from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from .local_model import local_models
import os

class RAGPipeline:
    def __init__(self):
        self.vector_store = None
        # Use HuggingFace local embeddings
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        
    def initialize_vector_store(self, documents):
        """
        Ingest documents into FAISS vector store.
        """
        if not documents:
            return
            
        print(f"Ingesting {len(documents)} documents locally...")
        self.vector_store = FAISS.from_documents(documents, self.embeddings)
        self.vector_store.save_local("faiss_index")
        print("Ingestion complete and index saved.")

    def load_vector_store(self):
        if os.path.exists("faiss_index"):
            self.vector_store = FAISS.load_local("faiss_index", self.embeddings, allow_dangerous_deserialization=True)

    def retrieve(self, query, k=2): # Reduced k to fit in context
        if not self.vector_store:
            return []
        return self.vector_store.similarity_search(query, k=k)

    def answer_query(self, query, language="en"):
        if not self.vector_store:
            return {
                "response": "I am not yet initialized with knowledge. Please trigger a scrape first.",
                "sources": [],
                "language": language
            }

        # 1. Retrieve
        docs = self.retrieve(query)
        
        # 2. Context Construction & Truncation
        # TinyLlama has 2048 token limit. We limit context to ~1500 tokens (approx 6000 chars)
        raw_context = "\n\n".join([d.page_content for d in docs])
        context = raw_context[:6000] 
        
        # 3. Prompt construction
        prompt = f"""You are Delores, a helpful assistant for Irembo services.
Answer the question based ONLY on the context below.
If the answer is not in the context, say "I don't know."

Context:
{context}

Question: {query}

Answer:"""
        
        # 3. Generate using Local LLM
        response_text = local_models.generate_response(prompt)
        
        # 4. Format Output
        sources = [{"title": d.metadata.get("title", "Unknown"), "url": d.metadata.get("source", "#"), "product": "Irembo"} for d in docs]
        
        return {
            "response": response_text,
            "sources": sources,
            "language": language
        }
