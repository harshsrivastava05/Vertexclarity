import streamlit as st
import sys
import os
import json
import streamlit.components.v1 as components

# Add parent dir to path to import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from graph.storage import GraphStorage
from graph.query import QueryEngine
from chat.llm import LLMClient

# Page Config
st.set_page_config(
    page_title="Vertex Clarity",
    page_icon="🕸️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for minimalist look
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
    }
    .stTextInput > div > div > input {
        background-color: #262730;
        color: white;
    }
    h1 {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        color: #f0f2f6;
    }
    .stChatMessage {
        background-color: transparent;
    }
</style>
""", unsafe_allow_html=True)

st.title("🕸️ Vertex Clarity")
st.caption("AI-Powered Engineering Knowledge Graph")

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

# Load Graph & Engine only once
@st.cache_resource
def get_engine():
    storage = GraphStorage()
    # Check if graph is empty, if so, maybe build it? 
    if storage.graph.number_of_nodes() == 0:
         # Try to load again just in case build_graph ran recently
         storage.load()
    return QueryEngine(storage)

@st.cache_resource
def get_llm():
    return LLMClient()

engine = get_engine()
llm = get_llm()

# Sidebar - Graph Stats
with st.sidebar:
    st.header("Graph Status")
    if engine.graph.number_of_nodes() > 0:
        col1, col2 = st.columns(2)
        col1.metric("Nodes", engine.graph.number_of_nodes())
        col2.metric("Edges", engine.graph.number_of_edges())
        st.success("Graph Loaded")
    else:
        st.error("Graph Empty")
        st.info("Run `python build_graph.py` or restart the container.")

# Tabs for Chat and Visualization
tab1, tab2 = st.tabs(["💬 Chat", "🕸️ Architecture"])

with tab1:
    # Chat Interface
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ex: What breaks if orders-db fails?"):
        # 1. User Message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 2. Processing
        with st.chat_message("assistant"):
            
            # Use spinner for the "thinking" state (Intent Parsing & Tool Execution)
            with st.spinner("Analyzing graph..."):
                try:
                    # A. Intent Parsing
                    intent = llm.parse_intent(prompt)
                    tool = intent.get("tool")
                    params = intent.get("params", {})
                    
                    # B. Execute Tool
                    result = None
                    debug_info = f"Tool: `{tool}`\nParams: `{params}`"
                    
                    if tool == "get_owner":
                        result = engine.get_owner(params.get("node_id"))
                    elif tool == "upstream":
                        result = engine.upstream(params.get("node_id"))
                    elif tool == "downstream":
                        result = engine.downstream(params.get("node_id"))
                    elif tool == "blast_radius":
                        result = engine.blast_radius(params.get("node_id"))
                    elif tool == "path":
                        result = engine.path(params.get("from_id"), params.get("to_id"))
                    elif tool == "get_nodes":
                        result = engine.get_nodes(params.get("type"))
                    elif tool == "chat":
                         result = params.get("response")
                    else:
                        result = {"error": f"Unknown tool: {tool}"}
                    
                    # C. Synthesize Response (Streaming)
                    if tool == "chat":
                        final_response_stream = result # String (not stream)
                    elif tool == "unknown" or tool is None:
                        final_response_stream = "I'm not sure which service or component you are referring to. Could you try specifying the full name (e.g., 'payment-service')?"
                    else:
                        # Returns a generator for streaming
                        final_response_stream = llm.summarize_results(prompt, result)
                    
                except (requests.RequestException, json.JSONDecodeError) as e:
                    st.error("LLM Connection Error")
                    print(f"LLM Connection Error: {e}")
                    final_response_stream = "Sorry, I'm having trouble connecting to the language model. Please check the connection."
                except Exception as e:
                    st.error("An unexpected error occurred")
                    print(f"An unexpected error occurred: {e}")
                    final_response_stream = "An unexpected error occurred. Please try again later."
            
            # Stream the output
            if isinstance(final_response_stream, str):
                st.markdown(final_response_stream)
                st.session_state.messages.append({"role": "assistant", "content": final_response_stream})
            else:
                response = st.write_stream(final_response_stream)
                st.session_state.messages.append({"role": "assistant", "content": response})

            # Debug Info (Collapsed) - Show AFTER extraction
            with st.expander("🛠️ Debug Info"):
                try:
                    st.text(debug_info)
                    if isinstance(result, (dict, list)):
                        st.json(result)
                    else:
                        st.write(result)
                except:
                    pass

with tab2:
    st.header("Graph Visualization")
    try:
        from pyvis.network import Network
        import tempfile
        
        # Create Pyvis network with Dark Modern Theme
        net = Network(height="750px", width="100%", bgcolor="#0E1117", font_color="white", directed=True)
        net.from_nx(engine.graph)
        
        # Physics: Optimized for stability and aesthetics (Constellation look)
        net.set_options("""
        {
          "nodes": {
            "font": {
              "strokeWidth": 0,
              "color": "white"
            }
          },
          "edges": {
            "color": {
              "color": "#666666",
              "highlight": "#ffffff",
              "hover": "#ffffff",
              "inherit": false,
              "opacity": 0.8
            },
            "width": 2,
            "smooth": {
              "type": "continuous"
            },
            "arrows": {
              "to": {
                "enabled": true,
                "scaleFactor": 0.8
              }
            }
          },
          "physics": {
            "forceAtlas2Based": {
              "gravitationalConstant": -110,
              "springLength": 100,
              "springConstant": 0.05,
              "damping": 0.9
            },
            "minVelocity": 0.75,
            "solver": "forceAtlas2Based",
            "stabilization": {
              "enabled": true,
              "iterations": 1000
            }
          }
        }
        """)
        
        # Color & Icon Scheme - Deep Space Neon
        type_colors = {
            'service': {'color': '#00d4ff', 'highlight': '#80eaff'},   # Cyber Blue
            'database': {'color': '#ff0055', 'highlight': '#ff80aa'},  # Neon Pink
            'team': {'color': '#ffffff', 'highlight': '#e0e0e0'},      # White
            'cache': {'color': '#ffbd00', 'highlight': '#ffe280'},     # Bright Yellow
            'unknown': {'color': '#999999'}
        }
        
        for node in net.nodes:
            n_attributes = engine.graph.nodes[node['id']]
            n_type = n_attributes.get('type', 'unknown')
            colors = type_colors.get(n_type, type_colors['unknown'])
            
            # Node Styling
            node['color'] = {
                'background': colors['color'],
                'border': '#1A1A1A',
                'highlight': {'background': colors['highlight'], 'border': '#FFFFFF'},
                'hover': {'background': colors['highlight'], 'border': '#FFFFFF'}
            }
            node['title'] = f"<b>{n_type.upper()}</b>: {node['label']}"
            node['borderWidth'] = 1
            node['shadow'] = True
            node['font'] = {
                'size': 16, 
                'color': 'white', 
                'face': 'Verdana',
                'background': '#0E1117'
            }
            
            # Size and Shape
            if n_type == 'team':
                node['size'] = 35
                node['shape'] = 'box'
                node['font']['size'] = 20
                node['mass'] = 4
                node['font']['background'] = 'none' # Box handles contrast
                node['color']['background'] = '#2b2b2b' # Dark grey box for team
                node['color']['border'] = 'white'
                node['font']['color'] = 'white' # Team text inside dark box
            elif n_type == 'database':
                node['size'] = 12
                node['shape'] = 'database'
            else:
                node['size'] = 15
                node['shape'] = 'dot'

        # Generate HTML
        with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
            net.save_graph(tmp.name)
            tmp.close()
            with open(tmp.name, 'r', encoding='utf-8') as f:
                html_data = f.read()
            os.unlink(tmp.name)
            
        components.html(html_data, height=720, scrolling=False)
        st.info("💡 **Interaction**: Drag nodes to rearrange, scroll to zoom, hover for details.")
        
    except ImportError:
        st.warning("Install `pyvis` to see the graph.")
    except Exception as e:
        st.error(f"Visualization Error: {e}")
