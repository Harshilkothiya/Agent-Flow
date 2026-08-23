import sys
import os

# Add parent directory to path so we can import config and db modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.postgres import init_db, SessionLocal, Document
from db.qdrant_client import init_qdrant

def seed():
    print("Initializing Relational Database (Postgres/SQLite)...")
    init_db()
    print("Database tables created.")
    
    print("\nInitializing Vector Database (Qdrant)...")
    init_qdrant()
    print("Qdrant initialized.")
    
    # Check if we have any docs as a quick test
    session = SessionLocal()
    try:
        count = session.query(Document).count()
        print(f"\nCurrent documents in DB: {count}")
    finally:
        session.close()

if __name__ == "__main__":
    seed()
