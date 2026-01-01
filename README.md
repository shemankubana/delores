# Irembo Chat (Delores)

This is an AI-powered chatbot for Irembo services, utilizing a local RAG (Retrieval-Augmented Generation) pipeline to answer user queries based on scraped support articles.

## Features
- **Frontend**: React (Vite) + TailwindCSS
- **Backend**: FastAPI
- **AI**: Local LLM (TinyLlama) + RAG (FAISS + SentenceTransformers)
- **Data**: Pre-scraped knowledge base from Irembo Agent Support

## Prerequisites
- Node.js (v18+)
- Python (v3.10+)

## Quick Start
Since the repository includes the pre-built knowledge base (`faiss_index/`), you do **not** need to scrape data manually.

### 1. Backend Setup
Navigate to the root directory and set up the Python environment:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt
```

**Note**: The first run might take a few minutes to download the local LLM models.

Start the backend server:
```bash
uvicorn backend.server:app --reload
```
The server will start at `http://localhost:8000`.

### 2. Frontend Setup
Open a new terminal, navigate to the project root:

```bash
npm install
npm run dev
```
The frontend will start at `http://localhost:5173`.

## Usage
- Open the frontend in your browser.
- Ask questions like "How do I pay for a service?" or "What is Irembo?".
- The system will use the local `faiss_index` to retrieve answers.

## Project Structure
- `backend/`: FastAPI server and RAG logic
- `src/`: React frontend code
- `faiss_index/`: Vector database (Pre-scraped data)
