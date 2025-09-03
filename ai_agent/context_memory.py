from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
import os

os.environ["GOOGLE_API_KEY"] = "AIzaSyCH5ud2FnsklQ-c95YJPDJrIHWJiCxHFDw"
# 1. Initialize LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

# 2. Add memory (stores all dialogue turns)
memory = ConversationBufferMemory()

# 3. Wrap in a conversation chain
conversation = ConversationChain(
    llm=llm,
    memory=memory,
    verbose=True
)

# 4. Run chat turns
print(conversation.predict(input="Hi, I'm Freddie."))
print(conversation.predict(input="Can you remind me what my name is?"))
print(conversation.predict(input="Summarize our conversation so far."))