# from langchain_google_genai import ChatGoogleGenerativeAI
# config = {
#     "llm_provider": "google",
#     "deep_think_llm": "gemini-2.0-flash",
#     "quick_think_llm": "gemini-2.0-flash",
#     "backend_url": "https://generativelanguage.googleapis.com/v1"
# }
# deep_thinking_llm = ChatGoogleGenerativeAI(model=config["deep_think_llm"])
# quick_thinking_llm = ChatGoogleGenerativeAI(model=config["quick_think_llm"])
#
#
# # Trigger the LLM with a sample prompt
# response = deep_thinking_llm.invoke("trump's response to elon muck's new america parrty")
# print(response)

import google.generativeai as genai
genai.configure(api_key="AIzaSyCH5u")

model = genai.GenerativeModel("gemini-2.5-flash")
response = model.generate_content("trump's response to elon muck's new america party")
print (response)
print(response.text)

#
# response:
# GenerateContentResponse(
#     done=True,
#     iterator=None,
#     result=protos.GenerateContentResponse({
#       "candidates": [
#         {
#           "content": {
#             "parts": [
#               {
#                 "text": "Donald Trump's ....."
#               }
#             ],
#             "role": "model"
#           },
#           "finish_reason": "STOP",
#           "index": 0
#         }
#       ],
#       "usage_metadata": {
#         "prompt_token_count": 14,
#         "candidates_token_count": 836,
#         "total_token_count": 2700
#       },
#       "model_version": "gemini-2.5-flash"
#     }),
# )
# Donald Trump's ....