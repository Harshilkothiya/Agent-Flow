import sys
import os
import warnings
import logging

# Suppress annoying warnings from underlying libraries
warnings.filterwarnings("ignore")
logging.getLogger("google").setLevel(logging.ERROR)
logging.getLogger("langchain_google_genai").setLevel(logging.ERROR)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

from agents.mcp_client import mcp_session
from agents.retrieval_agent import build_retrieval_graph
from agents.action_agent import build_action_graph
from config import Config

logger = logging.getLogger(__name__)

# ---------------------------------------------------------
# Main Orchestrator (The Boss)
# ---------------------------------------------------------
class OrchestratorState(TypedDict):
    messages: Annotated[list, add_messages]
    next_step: str

llm = ChatGoogleGenerativeAI(model="gemini-3.6-flash", api_key=Config.GEMINI_API_KEY)

async def run_agent(question: str):
    async with mcp_session() as (_session, tools):
        
        retrieval_app = build_retrieval_graph(tools)
        action_app = build_action_graph(tools)
        
        async def supervisor_node(state: OrchestratorState):
            sys_msg = SystemMessage(content=(
                "You are the supervisor. Route the user's request.\n"
                "If they want to search knowledge or summarize documents, output EXACTLY: RETRIEVAL\n"
                "If they want to query database stats or generate a report, output EXACTLY: ACTION\n"
                "Otherwise, answer them directly."
            ))
            response = await llm.ainvoke([sys_msg] + state["messages"])
            
            content_raw = response.content
            if isinstance(content_raw, list):
                content = "".join([b.get("text", "") for b in content_raw if isinstance(b, dict)]).strip().upper()
            else:
                content = str(content_raw).strip().upper()
            if "RETRIEVAL" in content:
                return {"next_step": "retrieval"}
            elif "ACTION" in content:
                return {"next_step": "action"}
            else:
                return {"messages": [response], "next_step": "end"}

        async def call_retrieval(state: OrchestratorState):
            logger.info("ROUTED TO: Retrieval Agent")
            result = await retrieval_app.ainvoke({"messages": state["messages"]})
            return {"messages": result["messages"][-1]}

        async def call_action(state: OrchestratorState):
            logger.info("ROUTED TO: Action Agent")
            result = await action_app.ainvoke({"messages": state["messages"]})
            return {"messages": result["messages"][-1]}

        workflow = StateGraph(OrchestratorState)
        workflow.add_node("supervisor", supervisor_node)
        workflow.add_node("retrieval", call_retrieval)
        workflow.add_node("action", call_action)
        
        workflow.set_entry_point("supervisor")
        workflow.add_conditional_edges(
            "supervisor",
            lambda x: x["next_step"],
            {"retrieval": "retrieval", "action": "action", "end": END}
        )
        workflow.add_edge("retrieval", END)
        workflow.add_edge("action", END)
        
        app = workflow.compile()
        
        inputs = {"messages": [HumanMessage(content=question)]}
        async for output in app.astream(inputs, stream_mode="updates"):
            yield output

async def main():
    print("\n--- Testing Orchestrator ---")
    question = "what last call i made"
    print(f"Question: {question}\n")
    
    async for output in run_agent(question):
        for state in output.values():
            if "messages" in state:
                msg_or_list = state["messages"]
                msg = msg_or_list[-1] if isinstance(msg_or_list, list) else msg_or_list
                
                if msg.type == "ai":
                    content = msg.content
                    if isinstance(content, list):
                        text = "".join([b.get("text", "") for b in content if isinstance(b, dict)])
                    else:
                        text = str(content)
                    if text.strip():
                        print(f"Answer:\n{text.strip()}\n")

if __name__ == "__main__":
    # Setup simple file logging for detailed steps
    logging.basicConfig(filename='orchestrator.log', level=logging.INFO, 
                        format='%(asctime)s - %(message)s', force=True)
    asyncio.run(main())
