import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# Load Llama 3 model and tokenizer
model_name = "meta-llama/Meta-Llama-3-8B-Instruct"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

# Prepare your question
question = "What is the claims process?"
inputs = tokenizer(question, return_tensors="pt")

# Generate answer
with torch.no_grad():
    outputs = model.generate(**inputs, max_new_tokens=100)
    answer = tokenizer.decode(outputs[0], skip_special_tokens=True)

print(answer)