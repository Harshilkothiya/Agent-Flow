from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage
from config import Config

# ---------------------------------------------------------
# Retrieval Subgraph (Loops until it gets a good answer)
# ---------------------------------------------------------
class RetrievalState(TypedDict):
    messages: Annotated[list, add_messages]

llm = ChatGoogleGenerativeAI(model="gemini-3.6-flash", api_key=Config.GEMINI_API_KEY)

def build_retrieval_graph(tools):
    retrieval_tools = [t for t in tools if t.name in ["search_documents", "summarize_document"]]
    llm_with_tools = llm.bind_tools(retrieval_tools)
    async def agent_node(state: RetrievalState):
        sys_msg = SystemMessage(content="You are a specialized Retrieval Agent. You MUST use your tools to search the document database and provide answers based only on the retrieved context.")
        response = await llm_with_tools.ainvoke([sys_msg] + state["messages"])
        return {"messages": [response]}
        
    def should_continue(state: RetrievalState):
        last_message = state["messages"][-1]
        if last_message.tool_calls:
            return "tools"
        return END

    workflow = StateGraph(RetrievalState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(retrieval_tools))
    
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    workflow.add_edge("tools", "agent")
    
    return workflow.compile()
