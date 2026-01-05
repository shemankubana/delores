import requests
import sqlite3
import json
import time
import sys

# Constants
BASE_URL = "http://localhost:8000"
DB_PATH = "backend/metrics.db"

def verify_logging():
    print("🚀 Starting Online Metrics Verification...")
    
    # 1. Send Chat Request
    print("   1. Sending Chat Request...")
    response = requests.post(f"{BASE_URL}/chat", json={"query": "Hello", "language": "en"}, stream=True)
    
    request_id = None
    response_text = ""
    
    for line in response.iter_lines():
        if line:
            decoded_line = line.decode('utf-8')
            response_text += decoded_line
            # Look for metadata end event
            if "__METADATA_END__" in decoded_line:
                # Format is usually __METADATA_END__:{json}
                try:
                    parts = decoded_line.split("__METADATA_END__:")
                    if len(parts) > 1:
                        meta = json.loads(parts[1])
                        request_id = meta.get("request_id")
                except:
                    pass

    if not request_id:
        print("   ❌ Failed to capture request_id from stream.")
        return
        
    print(f"   ✅ Request ID captured: {request_id}")
    
    # 2. Verify Log in DB
    print("   2. Verifying DB Log...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT query, response, feedback_score FROM chat_logs WHERE id = ?", (request_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        print("   ❌ Log NOT found in database.")
        return
        
    print(f"   ✅ Found log: Query='{row[0]}'")
    
    # 3. Send Feedback
    print("   3. Sending Feedback (Score: 5)...")
    fb_resp = requests.post(f"{BASE_URL}/feedback", json={"request_id": request_id, "score": 5})
    
    if fb_resp.status_code == 200:
        print("   ✅ Feedback submitted.")
    else:
        print(f"   ❌ Feedback submission failed: {fb_resp.status_code}")
        return

    # 4. Verify Feedback Update
    print("   4. Verifying Feedback in DB...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT feedback_score FROM chat_logs WHERE id = ?", (request_id,))
    row = cursor.fetchone()
    conn.close()

    if row and row[0] == 5:
        print("   ✅ Feedback score verified in DB!")
    else:
        print(f"   ❌ Feedback score NOT updated. Current: {row[0] if row else 'None'}")

if __name__ == "__main__":
    try:
        verify_logging()
    except Exception as e:
        print(f"❌ Error: {e}")
