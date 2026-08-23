from db.qdrant_client import client, COLLECTION_NAME
from rag.embeddings import embed_text

def retrieve(query: str, top_k: int = 5) -> list[dict]:
    """
    Takes a user's question, turns it into a vector, and asks Qdrant for the most similar chunks.
    Returns a list of dictionaries containing the text and metadata.
    """
    # 1. Convert the user's question into a vector embedding
    query_vector = embed_text(query)
    
    # 2. Search Qdrant for the closest matches
    search_result = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=top_k
    ).points
    
    # 3. Format the results nicely so the agent can read them
    results = []
    for hit in search_result:
        # hit.payload contains the metadata we saved during ingestion (like the text itself)
        results.append({
            "score": hit.score,
            "source": hit.payload.get("source"),
            "text": hit.payload.get("text")
        })
    print('results', results)
    return results
