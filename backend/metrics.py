import sqlite3
import json
import uuid
from datetime import datetime
import os

# Use absolute path relative to this file to avoid CWD confusion
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "metrics.db")

class MetricsManager:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Initialize the SQLite database and create tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_logs (
                id TEXT PRIMARY KEY,
                timestamp DATETIME,
                query TEXT,
                response TEXT,
                sources TEXT,
                latency_ms REAL,
                ttft_ms REAL,
                feedback_score INTEGER
            )
        ''')
        
        conn.commit()
        conn.close()

    def log_interaction(self, query: str, response: str, sources: list, latency_ms: float, ttft_ms: float = 0.0) -> str:
        """
        Log a chat interaction to the database.
        Returns the request_id.
        """
        request_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO chat_logs (id, timestamp, query, response, sources, latency_ms, ttft_ms, feedback_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, NULL)
        ''', (request_id, timestamp, query, response, json.dumps(sources), latency_ms, ttft_ms))
        
        conn.commit()
        conn.close()
        return request_id

    def update_feedback(self, request_id: str, score: int):
        """Update the feedback score for a specific interaction."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE chat_logs 
            SET feedback_score = ?
            WHERE id = ?
        ''', (score, request_id))
        
        conn.commit()
        conn.close()
