import requests
import json
import os
from typing import Dict, Any, List

class LLMClient:
    def __init__(self, base_url: str = None, model: str = None):
        self.base_url = base_url or os.getenv("LLM_BASE_URL", "http://localhost:11434")
        self.model = model or os.getenv("LLM_MODEL", "llama3.1")
        self.api_url = f"{self.base_url}/api/generate"

    def generate(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
             "options": {
                "temperature": 0.0 # Deterministic
            }
        }
        try:
            response = requests.post(self.api_url, json=payload)
            response.raise_for_status()
            return response.json().get("response", "")
        except requests.RequestException as e:
            print(f"LLM Error: {e}")
            return str(e)

    def parse_intent(self, user_query: str) -> Dict[str, Any]:
        """
        Translates natural language to formatted JSON for graph queries.
        """
        system_prompt = """
You are an intelligent assistant for an Engineering Knowledge Graph.
Your job is to translate user questions into a JSON object representing the graph query to run.

Available Tools/Queries:
1. `get_owner(node_id)`: Who owns a service/db?
2. `upstream(node_id)`: What depends on this? (Reverse dependencies)
3. `downstream(node_id)`: What does this depend on?
4. `blast_radius(node_id)`: Full impact analysis if this fails.
5. `path(from_id, to_id)`: How does X connect to Y?
6. `get_nodes(type)`: List all services/databases/teams.
7. `unknown`: If you cannot determine the intent.

Instructions:
- Extract the `node_id` or `type` from the text.
- `node_id` should try to include type prefix if obvious (e.g. service:order-service), otherwise just the name.
- Return ONLY valid JSON.

Examples:
Q: "Who owns payment-service?"
JSON: {"tool": "get_owner", "params": {"node_id": "service:payment-service"}}

Q: "What does order-service depend on?"
JSON: {"tool": "downstream", "params": {"node_id": "service:order-service"}}

Q: "What breaks if orders-db goes down?"
JSON: {"tool": "upstream", "params": {"node_id": "database:orders-db"}}

Q: "Impact of redis-main failure?"
JSON: {"tool": "blast_radius", "params": {"node_id": "cache:redis-main"}}

Q: "What happens if payment fails?"
JSON: {"tool": "blast_radius", "params": {"node_id": "service:payment-service"}}

Q: "Show me all databases"
JSON: {"tool": "get_nodes", "params": {"type": "database"}}

Q: "How does api-gateway connect to payments-db?"
JSON: {"tool": "path", "params": {"from_id": "service:api-gateway", "to_id": "database:payment-service"}}

Q: "Hi"
JSON: {"tool": "chat", "params": {"response": "Hello! Ask me about your engineering infrastructure."}}
"""
        
        full_prompt = f"{system_prompt}\n\nQ: \"{user_query}\"\nJSON:"
        
        response = self.generate(full_prompt)
        print(f"DEBUG: Raw LLM Response: [{response}]")
        
        # Cleanup response to ensure JSON
        cleaned = response.strip()
        
        # Try to find JSON block using regex or substring
        try:
            start_index = cleaned.find('{')
            end_index = cleaned.rfind('}')
            if start_index != -1 and end_index != -1:
                cleaned = cleaned[start_index : end_index + 1]
            else:
                # No braces found, LLM probably just chatted
                return {"tool": "chat", "params": {"response": cleaned}}
                
            return json.loads(cleaned)
        except json.JSONDecodeError:
             # Fallback if valid JSON structure but decode fails
            return {"tool": "chat", "params": {"response": "I couldn't parse the intent. Please try again."}}

    def generate_stream(self, prompt: str):
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": 0.0
            }
        }
        try:
            with requests.post(self.api_url, json=payload, stream=True) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        body = json.loads(line)
                        token = body.get("response", "")
                        if token:
                            yield token
        except requests.RequestException as e:
            yield f"LLM Error: {e}"

    def summarize_results(self, user_query: str, tool_output: Any):
        """
        Converts structured tool output back to natural language. Returns a generator.
        """
        prompt = f"""
You are an intelligent Engineering Assistant for a cloud infrastructure. 
You are analyzing a Knowledge Graph of services, databases, and teams.
You are NOT a customer support agent. Do NOT apologize for payment failures.

User Question: "{user_query}"
System Data: {json.dumps(tool_output)}

Instructions:
- Use the System Data to answer the User Question.
- If the data contains an error (like "Node not found"), explain it clearly as a system query error.
- Keep it concise and technical.
"""
        return self.generate_stream(prompt)
