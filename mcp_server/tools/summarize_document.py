from langchain_google_genai import ChatGoogleGenerativeAI
from config import Config

# Initialize the Gemini model for summarization
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    api_key=Config.GEMINI_API_KEY
)

def summarize_document(text: str) -> str:
    """
    Summarizes a large piece of text.
    Use this when you have retrieved a long document chunk and need a concise summary.
    """
    print("summarize document tool run")
    prompt = f"Please provide a concise summary of the following text:\n\n{text}"
    response = llm.invoke(prompt)
    return response.content
