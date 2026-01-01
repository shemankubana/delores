import requests
import json
import sys

def verify_stream():
    url = "http://localhost:8000/chat"
    payload = {
        "query": "What is Irembo?",
        "language": "en"
    }
    
    print(f"Sending request to {url}...")
    try:
        with requests.post(url, json=payload, stream=True) as response:
            if response.status_code != 200:
                print(f"Error: {response.status_code}")
                print(response.text)
                return

            print("Response stream started:")
            print("-" * 20)
            
            first_chunk = True
            for chunk in response.iter_content(chunk_size=None):
                if chunk:
                    text = chunk.decode('utf-8')
                    if first_chunk:
                        print(f"METADATA: {text.strip()}")
                        first_chunk = False
                        # Try parsing metadata
                        try:
                            meta = json.loads(text)
                            print(f"  Sources: {len(meta.get('sources', []))}")
                        except:
                            print("  (Could not parse metadata JSON)")
                    else:
                        sys.stdout.write(text)
                        sys.stdout.flush()
            
            print("\n" + "-" * 20)
            print("Stream finished.")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    verify_stream()
