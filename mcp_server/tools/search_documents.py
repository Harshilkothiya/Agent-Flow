import sys
import os
# Ensure we can import our rag module
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from rag.retriever import retrieve

def search_documents(query: str, top_k: int = 5) -> str:
    """
    Search the document knowledge base using vector similarity.
    Use this tool when you need to find information from the uploaded documents.
    """
    print("search document tool run")
    results = retrieve(query, top_k)
    
    if not results:
        return "No relevant documents found."
        
    formatted = []
    for i, res in enumerate(results):
        formatted.append(f"Result {i+1} (Source: {res['source']}):\n{res['text']}")
        
    return "\n\n".join(formatted)
