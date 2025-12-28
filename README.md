# Engineering Knowledge Graph (EKG) - VertexClarity

👋 **Welcome!**

This project is an **AI-powered Knowledge Graph** for your engineering infrastructure. 
Imagine asking: *"What breaks if the Payments Database goes down?"* and getting an instant, accurate answer without digging through GitHub repos or asking around in Slack.

## 🌟 What This Project Does

1.  **Reads Your Configs**: It scans your code files (Docker Compose, Kubernetes, Teams files).
2.  **Connects the Dots**: It builds a "Graph" - a visual map of how everything connects (Service A calls Service B, Team X owns Database Y).
3.  **Lets You Chat**: You can ask it questions in plain English, and it answers using that map.

---

## 🚀 How to Run It (The Easy Way)

**Prerequisites:**
- Docker installed on your computer.
- Ollama running locally (run `ollama run llama3.1` in a terminal).

**Steps:**
1.  Open a terminal in this folder.
2.  Run this command:
    ```bash
    docker-compose up --build
    ```
3.  Wait for it to start, then open your browser to: **http://localhost:8501**
4.  Start chatting! Or click the **"Graph Visualization"** tab to see the map.

---

## 🧠 System Design & Reasoning

Here is how we built it and **why** we made these choices.

### 1. The Core: "The Graph"
**Challenge**: Engineering info is scattered.
**Solution**: We used a **Graph Database** model.
- **Why?**: Infrastructure is naturally a network. Tables (rows/cols) are bad at "transitive dependencies" (A calls B calls C). Graphs are perfect for this.
- **Technology**: We used `NetworkX` (a Python library).
- **Reasoning**: For a prototype with <10,000 nodes, an in-memory graph is **instantly fast** and effectively "free" (no extra server to manage like Neo4j). It allows for rapid development.

### 2. The Brain: "Local LLM"
**Challenge**: We need to understand human questions like "Who owns this?".
**Solution**: We use **Llama 3.1** via **Ollama**.
- **Reasoning**: 
    - **Privacy**: Your infrastructure data never leaves your laptop. 
    - **Cost**: It's free. No OpenAI bills.
    - **Control**: We can tweak the model as much as we want.

### 3. The Eyes: "Connectors"
**Challenge**: Every tool (Docker, K8s, Terraform) has a different file format.
**Solution**: We built a "Plug-and-Play" connector system.
- **Design**: A generic `BaseConnector` that anyone can extend. 
- **Reasoning**: If you want to add Terraform support later, you assume write *one* file `terraform.py` and plug it in. You don't have to rewrite the whole system. This makes the project **future-proof**.

### 4. The Face: "Streamlit UI"
**Challenge**: We need a chat interface quickly.
**Solution**: **Streamlit**.
- **Reasoning**: It enables building a beautiful Web UI entirely in Python in minutes. It supports Chat interfaces and HTML rendering (for our graph visualization) out of the box.
- **Key Features**:
    - **Streaming Responses**: The LLM streams tokens immediately for a snappy feel.
    - **Interactive Visualization**: A "Graph Visualization" tab uses `PyVis` to render an interactive, physics-based map of your architecture (nodes auto-arrange to avoid clutter).
    - **Debugging**: An expandable "Debug Info" panel shows exactly which tool the AI picked and the raw JSON it produced.

---

## 📁 Project Structure (Where is everything?)

- **`data/`**: The raw files we are analyzing (teams, docker-compose).
- **`connectors/`**: The scripts that read those files.
- **`graph/`**: The brain that stores the connections and runs queries (like "blast radius").
- **`chat/`**: The website asking you for questions.
- **`tests/`**: Automatic checks to make sure the code isn't broken.

---

## 🛠 Manual Testing (For Developers)

If you want to run the checks yourself:

1.  Create a virtual environment:
    ```bash
    python -m venv vertexclarity
    .\vertexclarity\Scripts\activate
    ```
2.  Install requirements:
    ```bash
    pip install -r requirements.txt
    ```
3.  Run the tests:
    ```bash
    pytest tests/
    ```
