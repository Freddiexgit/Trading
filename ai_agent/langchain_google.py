from typing import Annotated
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END, MessagesState



class AgentState(MessagesState):
    company_of_interest: str
    trade_date: str
    messages: Annotated[list[tuple[str, str]], "Conversation history"]

def llm_node(state: AgentState):
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
    user_message = state.get("messages") # last message content
    response = llm.invoke(user_message)
    state.get("messages").append(("ai", response.content))
    return state

def build_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("llm_node", llm_node)
    workflow.add_edge(START, "llm_node")
    workflow.add_edge("llm_node", END)
    return workflow.compile()

if __name__ == "__main__":
    os.environ["GOOGLE_API_KEY"] = "AIzaSyCH5ud2Fnskl"
    graph = build_graph()
    init_agent_state = AgentState(
        messages=[
            ("system", "You are a helpful financial analyst..."),  # your system prompt
            ("human", "what is the profit prediction of RBLX?"),
        ],
        company_of_interest="RBLX",
        trade_date="2025-07-01",
    )
    result = graph.invoke(init_agent_state)
    print(result["messages"])


