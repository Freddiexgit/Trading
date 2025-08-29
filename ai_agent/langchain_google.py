from typing import Annotated
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END, MessagesState
from langchain.tools import tool
from langgraph.checkpoint.memory import MemorySaver


# from langchain_community.document_loaders import PyPDFLoader
#
# # Example: load a PDF file
# loader = PyPDFLoader("sample.pdf")
# docs = loader.load()
#
# # Split docs into chunks
# splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
# splits = splitter.split_documents(docs)
#
# # Build FAISS index with embeddings
# vectorstore = FAISS.from_documents(splits, OpenAIEmbeddings())
# retriever = vectorstore.as_retriever()
# @tool
# def search_docs(query: str) -> str:
#     """Search knowledge base documents for relevant information."""
#     results = retriever.get_relevant_documents(query)
#     return "\n\n".join([doc.page_content for doc in results[:3]])


@tool
def get_weather(city: str) -> str:
    """Get the weather for a given city."""
    return f"The weather in {city} is sunny and 22°C."

class AgentState(MessagesState):
    company_of_interest: str
    trade_date: str
    messages: Annotated[list[tuple[str, str]], "Conversation history"]

tools = [get_weather]
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
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
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)




if __name__ == "__main__":
    os.environ["GOOGLE_API_KEY"] = ""
    graph = build_graph()
    init_agent_state = AgentState(
        messages=[
            ("system", "You are a helpful financial analyst..."),  # your system prompt
            ("human", "give me the foundmental analysis of Copart, Inc, human readable format "),
        ]
    )
    result = graph.invoke(init_agent_state)
    print(result["messages"])



