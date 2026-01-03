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

```mermaid
graph TD
    subgraph "Ingestion Layer"
        Files[Config Files] --> Connectors
        Connectors[Connectors (Docker, K8s, Teams)] --> Parser[BaseConnector]
    end
    
    subgraph "Core Engine"
        Parser --> Builder[Graph Builder]
        Builder --> Graph[NetworkX Graph]
    end
    
    subgraph "Interaction Layer"
        User --> UI[Streamlit UI]
        UI --> Query[Query Engine]
        Query --> Graph
        Query --> Context[Context Builder]
        Context --> LLM[Llama 3.1]
        LLM --> UI
    end
```

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

### 3. The Eyes: "Connectors" (The Connector Architecture)
**Challenge**: Modern infrastructure uses dozens of different formats (YAML, HCL, JSON).
**Solution**: We implemented a **Plugin-based Connector Architecture**.

- **The Flow**: 
  1. `Raw Files` are identified by extension.
  2. The appropriate `Connector` (e.g., `KubernetesConnector`) is instantiated.
  3. It parses the file and emits standardized `Node` and `Edge` objects.
  4. The `GraphBuilder` ingests these objects without knowing where they came from.

- **Why this matters**:
  - **Extensibility**: Adding support for a new tool (like **Terraform** or **Ansible**) is trivial. You create a single class inheriting from `BaseConnector` and implementing `parse()`.
  - **Isolation**: Improvements to the Kubernetes parser don't break the Docker parser.
  - **Future-Proofing**: The core graph engine never changes; only the plugins do.

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
