from db.postgres import Document, QueryLog, SessionLocal


def query_structured_data(question_type: str) -> str:
    """
    Query the structured Postgres database safely.
    question_type must be one of:
      - 'document_count': Returns how many documents have been uploaded.
      - 'recent_logs': Returns the last 5 tool usages.
    """
    print("query structured tool run")
    session = SessionLocal()
    try:
        if question_type == 'document_count':
            count = session.query(Document).count()
            return f"There are {count} documents in the database."
            
        elif question_type == 'recent_logs':
            logs = session.query(QueryLog).order_by(QueryLog.timestamp.desc()).limit(5).all()
            if not logs:
                return "No recent logs found."
            
            output = []
            for log in logs:
                output.append(f"[{log.timestamp}] Agent '{log.agent}' used tool '{log.tool}'")
            return "\n".join(output)
            
        else:
            return "Invalid question_type. Supported types: 'document_count', 'recent_logs'."
    finally:
        session.close()
