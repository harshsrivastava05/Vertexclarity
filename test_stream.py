
import time
from chat.llm import LLMClient

def test_streaming():
    client = LLMClient()
    print("Requesting stream...")
    start = time.time()
    first_token_time = None
    
    stream = client.generate_stream("Count from 1 to 10 quickly.")
    
    full_text = ""
    for token in stream:
        if first_token_time is None:
            first_token_time = time.time()
            print(f"First token received after {first_token_time - start:.2f}s")
        print(f"Token: '{token}'", end="", flush=True)
        full_text += token
    
    print(f"\n\nTotal time: {time.time() - start:.2f}s")
    print(f"Full response: {full_text}")

if __name__ == "__main__":
    test_streaming()
