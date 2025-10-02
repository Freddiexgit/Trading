import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import tool

# Make sure the key is set
os.environ["GOOGLE_API_KEY"] =  "AIzaSyCH5ud2FnsklQ-c95YJPDJrIHWJiCxHFDw"

# 1. Initialize Gemini properly
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",   # ✅ use your model
    temperature=0,
    google_api_key=os.getenv("GOOGLE_API_KEY")  # ✅ explicit auth
)

# 2. Define a tool (function calling)
@tool
def get_weather(city: str) -> str:
    """Return the weather for a given city."""
    return f"The weather in {city} is sunny and 22°C."

tools = [get_weather]

# 3. Bind tools
llm_with_tools = llm.bind_tools(tools)

# 4. Invoke
from langchain_core.messages import HumanMessage

response = llm_with_tools.invoke([HumanMessage(content="What's the weather in Berlin?")])
print(response)