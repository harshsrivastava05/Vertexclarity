import requests
import json

def check_ollama():
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "llama3.1",
        "prompt": "Say 'Ollama is working'",
        "stream": False
    }
    try:
        print(f"Connecting to {url}...")
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        print("Success!")
        print("Response:", data.get("response"))
    except Exception as e:
        print("Failed to connect to Ollama.")
        print(f"Error: {e}")

if __name__ == "__main__":
    check_ollama()
