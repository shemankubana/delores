from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .scraper import scrape_portal
from .rag import RAGPipeline
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Initialize RAG
rag = RAGPipeline()
rag.load_vector_store()

class ChatRequest(BaseModel):
    query: str
    product: str | None = None
    language: str = "en"  # "en", "fr", "rw"

@app.get("/")
def read_root():
    return {"status": "Delores Backend Running"}

@app.post("/chat")
def chat(request: ChatRequest):
    result = rag.answer_query(request.query, request.language)
    return {
        "response": result["response"],
        "sources": result["sources"],
        "language": result["language"],
        "timestamp": datetime.now().isoformat()
    }

@app.post("/scrape")
def trigger_scrape():
    try:
        documents = scrape_portal("SEED_DATA")
        rag.initialize_vector_store(documents)
        return {"status": "Scraping and Ingestion Complete", "count": len(documents)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
