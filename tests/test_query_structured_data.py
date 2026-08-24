import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db.postgres import init_db, SessionLocal, Document, QueryLog
from mcp_server.tools.query_structured_data import query_structured_data


def setup_module(module):
    """Create tables once, in the throwaway test SQLite DB, before these tests run."""
    init_db()


def test_document_count_empty():
    session = SessionLocal()
    session.query(Document).delete()
    session.commit()
    session.close()

    result = query_structured_data("document_count")
    assert "0 documents" in result


def test_document_count_after_insert():
    session = SessionLocal()
    session.add(Document(filename="test.pdf"))
    session.commit()
    session.close()

    result = query_structured_data("document_count")
    assert "1 documents" in result


def test_recent_logs_empty():
    session = SessionLocal()
    session.query(QueryLog).delete()
    session.commit()
    session.close()

    result = query_structured_data("recent_logs")
    assert result == "No recent logs found."


def test_invalid_question_type_is_rejected():
    result = query_structured_data("not_a_real_type")
    assert "Invalid question_type" in result
