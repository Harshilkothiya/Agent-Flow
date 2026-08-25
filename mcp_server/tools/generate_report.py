import uuid

from langchain_google_genai import ChatGoogleGenerativeAI

from config import Config
from db.postgres import Report, SessionLocal
from rag.retriever import retrieve

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    api_key=Config.GEMINI_API_KEY
)

def generate_report(topic: str) -> str:
    """
    Generates a comprehensive report on a given topic by pulling data from Qdrant,
    writing the report with Gemini, and logging the report in Postgres.
    """
    # 1. Gather data using our RAG pipeline
    print("Generate tool run")
    docs = retrieve(topic, top_k=3)
    context = "\n\n".join([d['text'] for d in docs])
    
    # 2. Generate the report using Gemini
    prompt = f"Write a comprehensive report on '{topic}' based on this context:\n\n{context}"
    report_content = llm.invoke(prompt).content
    
    # 3. Log the report generation in Postgres
    session = SessionLocal()
    try:
        new_report = Report(
            id=str(uuid.uuid4()),
            topic=topic,
            s3_path="local_only_for_now" # S3 is deferred
        )
        session.add(new_report)
        session.commit()
    finally:
        session.close()
        
    return f"Report generated and saved for topic: {topic}\n\nPreview:\n{report_content[:500]}..."
