import os
import sys

# Add parent directory to path so we can import rag modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.ingest import ingest_document
from rag.retriever import retrieve


def test_pipeline():
    # Construct the path to our sample document
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    doc_path = os.path.join(base_dir, "data", "sample_docs", "test_doc.txt")
    
    print("=== 1. Testing Ingestion ===")
    ingest_document(doc_path)
    print("Ingestion complete.\n")
    
    print("=== 2. Testing Retrieval ===")
    query = "Who were the astronauts that walked on the moon?"
    print(f"User Query: '{query}'\n")
    
    results = retrieve(query, top_k=2)
    
    for i, res in enumerate(results):
        print(f"Result {i+1} (Match Score: {res['score']:.4f})")
        print(f"Source Document: {res['source']}")
        print(f"Extracted Text: {res['text'].strip()}\n")

if __name__ == "__main__":
    test_pipeline()
