import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from config import Config

Base = declarative_base()

class Document(Base):
    __tablename__ = 'documents'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow)
    processed = Column(Boolean, default=False)

class QueryLog(Base):
    __tablename__ = 'query_logs'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent = Column(String, nullable=False)
    tool = Column(String, nullable=False)
    input = Column(Text, nullable=False)
    output_summary = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

class Report(Base):
    __tablename__ = 'reports'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    topic = Column(String, nullable=False)
    s3_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Ensure connect_args for SQLite to prevent thread issues
connect_args = {"check_same_thread": False} if Config.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(Config.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Create all tables in the database if they don't exist."""
    Base.metadata.create_all(bind=engine)

def get_session():
    """Provide a transactional scope around a series of operations."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
