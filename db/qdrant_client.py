from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

from config import Config


def get_qdrant_client():
    if not Config.QDRANT_API_KEY and ("localhost" in Config.QDRANT_URL or "127.0.0.1" in Config.QDRANT_URL):
        # Local Qdrant via Docker
        return QdrantClient(url=Config.QDRANT_URL)
    elif Config.QDRANT_URL == ":memory:":
        # In-memory mode (good for dev if no cloud/local set up)
        return QdrantClient(location=":memory:")
    else:
        # Qdrant Cloud
        return QdrantClient(url=Config.QDRANT_URL, api_key=Config.QDRANT_API_KEY)

client = get_qdrant_client()
COLLECTION_NAME = Config.COLLECTION_NAME

def init_qdrant():
    """Initializes the Qdrant collection if it doesn't exist."""
    collections = client.get_collections().collections
    exists = any(c.name == COLLECTION_NAME for c in collections)
    
    if not exists:
        # all-MiniLM-L6-v2 uses 384 dimensions and Cosine similarity
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )
        print(f"Created Qdrant collection: {COLLECTION_NAME}")
    else:
        print(f"Qdrant collection '{COLLECTION_NAME}' already exists.")
