from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.document_loaders import PyPDFLoader
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain

# 1. Load Gemini LLM
llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0)

# 2. Load embeddings
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

# 3. Load & chunk a document
loader = PyPDFLoader("my_private_doc.pdf")
docs = loader.load()

splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
chunks = splitter.split_documents(docs)

# 4. Store in Chroma vector DB
vectordb = Chroma.from_documents(chunks, embedding=embeddings, persist_directory="chroma_store")

retriever = vectordb.as_retriever(search_kwargs={"k": 3})

# 5. Add memory
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# 6. Build Conversational RAG chain
# qa_chain = ConversationalRetrievalChain.from_llm(
#     llm=llm,
#     retriever=retriever,
#     memory=memory,
#     return_source_documents=True
# )
#
#
# query = "Summarize the main findings in this document."
# result = qa_chain({"question": query})
#
# print("\n🤖 Answer:\n", result["answer"])
# print("\n📄 Sources:\n", [doc.metadata for doc in result["source_documents"]])
#
# # Continue dialogue (memory remembers!)
# followup = "And how does that relate to climate change?"
# result2 = qa_chain({"question": followup})
# print("\n🤖 Follow-up:\n", result2["answer"])


from langchain.agents import Tool, initialize_agent

# Wrap retriever as a function (tool)
def search_kb(query: str) -> str:
    docs = retriever.get_relevant_documents(query)
    return "\n".join([d.page_content for d in docs])

kb_tool = Tool(
    name="KnowledgeBaseSearch",
    func=search_kb,
    description="Searches the uploaded private docs for relevant information."
)

agent = initialize_agent(
    tools=[kb_tool],
    llm=llm,
    agent="chat-conversational-react-description",
    memory=memory,
    verbose=True
)

print(agent.run("What does my document say about renewable energy?"))