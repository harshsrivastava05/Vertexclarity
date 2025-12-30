import urllib.request
import json
import os

def check_llm():
    # Allow overriding model via environment variable, default to deepseek-r1:8b
    model = os.getenv("LLM_MODEL", "llama3.1")
    base_url = os.getenv("LLM_BASE_URL", "http://localhost:11434")
    url = f"{base_url}/api/generate"
    
    payload = {
        "model": model,
        "prompt": "Say 'LLM is working'",
        "stream": False
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})

    print(f"Connecting to {url} with model {model}...")
    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                result = json.loads(response.read().decode('utf-8'))
                print("Success!")
                print("Response:", result.get("response"))
            else:
                print(f"Failed with status code: {response.status}")
    except Exception as e:
        print("Failed to connect to LLM.")
        print(f"Error: {e}")

if __name__ == "__main__":
    check_llm()
