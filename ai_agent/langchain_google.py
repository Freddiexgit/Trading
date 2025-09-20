from langchain_core.messages import HumanMessage
from typing import Annotated
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END, MessagesState
from langchain.tools import tool
from langgraph.checkpoint.memory import MemorySaver




class AgentState(MessagesState):
    company_of_interest: str
    trade_date: str
    messages: Annotated[list[tuple[str, str]], "Conversation history"]


@tool
def get_weather(city: str) -> str:
    """Get the weather for a given city."""
    return f"The weather in {city} is sunny and 22°C."

tools = [get_weather]

# --- 2. Define LLM Node with function calling ---
# llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash",google_api_key=os.getenv("GOOGLE_API_KEY"))
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    google_api_key=os.getenv("GOOGLE_API_KEY")  # ✅ pass explicitly
)
llm_with_tools = llm.bind_tools(tools)
def llm_node(state: AgentState):

    user_message = state.get("messages") # last message content
    response = llm_with_tools.invoke(user_message)
    state.get("messages").append(("ai", response.content))
    return state

def build_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("llm_node", llm_node)
    workflow.add_edge(START, "llm_node")
    workflow.add_edge("llm_node", END)
    return workflow.compile()

if __name__ == "__main__":
    os.environ["GOOGLE_API_KEY"] = "AIzaSyCH5ud2FnsklQ-c95YJPDJrIHWJiCxHFDw"
    graph = build_graph()
    state = {"messages": [HumanMessage(content="What’s the weather in Paris?")]}
    result = graph.invoke(state, config={"configurable": {"thread_id": "demo"}})
    print(result["messages"][-1].content)
