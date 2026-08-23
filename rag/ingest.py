import os
import uuid
from langchain_text_splitters import RecursiveCharacterTextSplitter
from PyPDF2 import PdfReader

from db.postgres import SessionLocal, Document
from db.qdrant_client import client, COLLECTION_NAME
from qdrant_client.http.models import PointStruct
from rag.embeddings import embed_batch

# We split large text into chunks of 512 characters, keeping 50 characters of overlap 
# so we don't accidentally cut sentences in half.
text_splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=50)

def extract_text(file_path: str) -> str:
    """Reads a file (PDF or TXT) and extracts all its text into a single string."""
    if file_path.endswith('.pdf'):
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        return text
    else:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

def ingest_document(file_path: str):
    """
    1. Reads the file.
    2. Splits it into small chunks.
    3. Turns chunks into embeddings.
    4. Saves embeddings to Qdrant and logs the file in Postgres.
    """
    print(f"Starting ingestion for {file_path}...")
    
    # 1. Read and chunk the text
    raw_text = extract_text(file_path)
    print(raw_text, end="\n------------------------\n")
    chunks = text_splitter.split_text(raw_text)
    print(len(chunks),chunks,   end="\n------------------------\n")
    # 2. Convert text chunks to vector embeddings
    vectors = embed_batch(chunks)
    
    # 3. Create a unique ID for this document in Postgres
    doc_id = str(uuid.uuid4())
    filename = os.path.basename(file_path)
    
    # 4. Prepare data points for Qdrant
    points = []
    for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
        points.append(
            PointStruct(
                id=str(uuid.uuid4()), # Unique ID for the chunk
                vector=vector,        # The 384 numbers
                payload={             # Metadata
                    "doc_id": doc_id,
                    "source": filename,
                    "chunk_index": i,
                    "text": chunk     # Save the actual text so the agent can read it later
                }
            )
        )
    
    # 5. Save to Qdrant
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )
    
    # 6. Save a record in our Postgres database
    session = SessionLocal()
    try:
        new_doc = Document(id=doc_id, filename=filename, processed=True)
        session.add(new_doc)
        session.commit()
    finally:
        session.close()
        
    print(f"Successfully ingested '{filename}' into {len(chunks)} chunks.")
