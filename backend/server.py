from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from .scraper import scrape_portal
from .scraper import scrape_portal
from .rag import RAGPipeline
from .metrics import MetricsManager
import os
import time
import json
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

# Initialize Metrics
metrics = MetricsManager()

class ChatRequest(BaseModel):
    query: str
    product: str | None = None
    language: str = "en"  # "en", "fr", "rw"

class FeedbackRequest(BaseModel):
    request_id: str
    score: int  # 1-5

@app.get("/")
def read_root():
    return {"status": "Delores Backend Running"}

@app.post("/chat")
def chat(request: ChatRequest):
    start_time = time.time()
    
    # We will capture data in the generator to log after streaming finishes
    def content_generator():
        ttft = None
        full_response = []
        sources = []
        
        # Generator from RAG
        stream = rag.answer_query_stream(request.query, request.language)
        
        # 1. First chunk is metadata
        try:
            metadata_json = next(stream)
            yield metadata_json
            
            # Parse metadata to store for logging
            meta_dict = json.loads(metadata_json)
            sources.extend(meta_dict.get("sources", []))
            
        except StopIteration:
            pass
            
        # 2. Stream tokens
        for token in stream:
            if ttft is None:
                ttft = (time.time() - start_time) * 1000  # ms
            
            full_response.append(token)
            yield token
            
        # 3. Log Interaction after stream ends
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        response_text = "".join(full_response)
        
        # Log to DB
        req_id = metrics.log_interaction(
            query=request.query,
            response=response_text,
            sources=sources,
            latency_ms=latency_ms,
            ttft_ms=ttft if ttft else 0.0
        )
        
        # Optionally yield the request_id as a final event or log it server-side
        # For now, we can print it or handle it. 
        # Ideally, we should send it to the client in the first metadata chunk, 
        # but since that comes from RAG, we might need to refactor. 
        # For simplicity, we assume client can't see ID yet unless we modify RAG. 
        # ACTUALLY: Let's refactor slightly to generate ID here (or return it in a header if we weren't streaming).
        # Since we are streaming, we can append a special footer or just log it for internal use.
        # BUT: The user needs the ID to send feedback. 
        # FIX: We will yield a final chunk with the ID.
        
        final_meta = json.dumps({"request_id": req_id, "type": "end_event"})
        yield f"\n\n__METADATA_END__:{final_meta}"

    return StreamingResponse(
        content_generator(), 
        media_type="text/plain"
    )

@app.post("/feedback")
def feedback(request: FeedbackRequest):
    try:
        metrics.update_feedback(request.request_id, request.score)
        return {"status": "Feedback received"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
