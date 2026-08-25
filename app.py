import asyncio
import logging
import os
import tempfile

import streamlit as st

from agents.orchestrator import run_agent
from rag.ingest import ingest_document

# Suppress annoying background logs
logging.basicConfig(filename='orchestrator.log', level=logging.INFO, force=True)

st.set_page_config(page_title="AI Agent Platform", page_icon="🤖")
st.title("🤖 Enterprise AI Agent")

# ---------------------------------------------------------
# Sidebar: Document Upload & Ingestion
# ---------------------------------------------------------
with st.sidebar:
    st.header("📄 Knowledge Base")
    st.markdown("Upload documents here to make them instantly searchable by the AI.")
    
    uploaded_file = st.file_uploader("Upload a PDF or TXT file", type=["pdf", "txt"])
    
    if uploaded_file is not None and st.button("Process Document"):
        with st.spinner("Chunking, embedding, and storing in database..."):
            # 1. Save uploaded file temporarily
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, uploaded_file.name)
            
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            try:
                # 2. Ingest the document using our RAG pipeline
                ingest_document(temp_path)
                st.success(f"Successfully processed '{uploaded_file.name}'!")
            except Exception as e:  # noqa: BLE001
                st.error(f"Error during ingestion: {e}")
            finally:
                # 3. Delete the temporary raw file
                if os.path.exists(temp_path):
                    os.remove(temp_path)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Handle new user input
if prompt := st.chat_input("Ask me anything about your documents or databases..."):
    # Add to session state & display
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Bot response
    with st.chat_message("assistant"):
        status_box = st.empty()
        response_box = st.empty()
        
        async def fetch_response():
            final_text = ""
            status_box.info("🧠 Thinking...")
            
            # Stream events from our Orchestrator LangGraph
            async for output in run_agent(prompt):
                for node, state in output.items():
                    if node == "supervisor":
                        next_step = state.get('next_step', 'end')
                        if next_step == "retrieval":
                            status_box.warning("🔍 Searching Document Database...")
                        elif next_step == "action":
                            status_box.success("⚡ Querying Postgres Database...")
                    
                    if "messages" in state:
                        msg_or_list = state["messages"]
                        msg = msg_or_list[-1] if isinstance(msg_or_list, list) else msg_or_list
                        
                        if msg.type == "ai":
                            content = msg.content
                            text = "".join([b.get("text", "") for b in content if isinstance(b, dict)]) if isinstance(content, list) else str(content)
                            if text.strip():
                                final_text = text.strip()
            return final_text
            
        # Run the async loop safely in Streamlit
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                raise RuntimeError
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        final_answer = loop.run_until_complete(fetch_response())
        
        # Display final result
        status_box.empty() # Clear the status box
        response_box.markdown(final_answer)
        
        # Save to history
        st.session_state.messages.append({"role": "assistant", "content": final_answer})
