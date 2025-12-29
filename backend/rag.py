import os
from tenacity import retry, stop_after_attempt, wait_exponential
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from transformers import pipeline

# Placeholder for Digital Umuganda Model loading
# from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
# from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
# model_name = "DigitalUmuganda/Joeynmt-kin-en" 

class RobustGoogleGenerativeAIEmbeddings(GoogleGenerativeAIEmbeddings):
    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=2, max=60))
    def embed_documents(self, texts, *args, **kwargs):
        return super().embed_documents(texts, *args, **kwargs)

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=2, max=60))
    def embed_query(self, text, *args, **kwargs):
        return super().embed_query(text, *args, **kwargs) 

class RAGPipeline:
    def __init__(self):
        self.vector_store = None
        self.embeddings = RobustGoogleGenerativeAIEmbeddings(model="models/embedding-001") # Requires GOOGLE_API_KEY
        self.llm = ChatGoogleGenerativeAI(model="gemini-pro", convert_system_message_to_human=True)
        
        # Initialize specialized Kinyarwanda models if needed here
        self.kin_translator = None # Lazy load to save memory if not running

    def initialize_vector_store(self, documents):
        """
        Ingest documents into FAISS vector store.
        Uses batching to avoid API rate limits.
        """
        import time
        from langchain_community.vectorstores import FAISS
        
        if not documents:
            return
            
        batch_size = 20
        total_docs = len(documents)
        print(f"Ingesting {total_docs} documents in batches of {batch_size}...")
        
        # Initialize with first batch to create the store
        first_batch = documents[:batch_size]
        self.vector_store = FAISS.from_documents(first_batch, self.embeddings)
        print(f"Batch 1 processed.")
        
        # Add remaining batches
        for i in range(batch_size, total_docs, batch_size):
            batch = documents[i : i + batch_size]
            try:
                self.vector_store.add_documents(batch)
                print(f"Batch {i//batch_size + 1} processed.")
                time.sleep(2) # Sleep to be polite to the embeddings API
            except Exception as e:
                print(f"Error adding batch {i}: {e}")
                
        self.vector_store.save_local("faiss_index")
        print("Ingestion complete and index saved.")

    def load_vector_store(self):
        if os.path.exists("faiss_index"):
            self.vector_store = FAISS.load_local("faiss_index", self.embeddings, allow_dangerous_deserialization=True)

    def retrieve(self, query, k=3):
        if not self.vector_store:
            return []
        return self.vector_store.similarity_search(query, k=k)

    def answer_query(self, query, language="en"):
        """
        Main RAG loop: Retrieve -> Augment -> Generate
        """
        if not self.vector_store:
            return {
                "response": "I am not yet initialized with knowledge. Please trigger a scrape first.",
                "sources": [],
                "language": language
            }

        # 1. Retrieve
        docs = self.retrieve(query)
        context = "\n\n".join([d.page_content for d in docs])
        
        # 2. Prompt
        template = """You are Delores, a helpful assistant for Irembo services (IremboGov, IremboPlus, One Stop Center).
        Answer the user's question using ONLY the context provided below.
        If the answer is not in the context, say you don't know and check the official website.
        
        Context:
        {context}
        
        Question: {question}
        
        Answer in {language}:"""
        
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm
        
        # 3. Generate
        response = chain.invoke({
            "context": context,
            "question": query,
            "language": language
        })
        
        # 4. Format Output
        sources = [{"title": d.metadata.get("title", "Unknown"), "url": d.metadata.get("source", "#"), "product": "Irembo"} for d in docs]
        
        return {
            "response": response.content,
            "sources": sources,
            "language": language
        }

if __name__ == "__main__":
    print("RAG Pipeline initialized.")
