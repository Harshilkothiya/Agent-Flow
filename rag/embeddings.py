from langchain_huggingface import HuggingFaceEndpointEmbeddings

from config import Config

# Use Hugging Face Inference API for embeddings instead of local execution.
# This sends the text to Hugging Face servers to be converted into 384 dimensions.
embeddings_model = HuggingFaceEndpointEmbeddings(
    model="BAAI/bge-small-en-v1.5",
    huggingfacehub_api_token=Config.HUGGINGFACE_API_KEY
)

def embed_text(text: str) -> list[float]:
    """
    Takes a single string of text and converts it into a list of 384 numbers (an embedding vector).
    This allows Qdrant to understand the 'meaning' of the text.
    """
    return embeddings_model.embed_query(text)

def embed_batch(texts: list[str]) -> list[list[float]]:
    """
    Takes a list of strings and converts them all into embedding vectors at once.
    This is much faster than doing them one by one when uploading a big document.
    """
    return embeddings_model.embed_documents(texts)
