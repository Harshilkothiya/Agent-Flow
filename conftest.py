import os

# Force a throwaway local SQLite DB and dummy keys so tests never touch
# real cloud services or need real secrets in CI.
os.environ.setdefault("NEON_DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("GEMINI_API_KEY", "test-key-not-used")
os.environ.setdefault("QDRANT_API_KEY", "test-key-not-used")
os.environ.setdefault("HUGGINGFACE_API_KEY", "test-key-not-used")
