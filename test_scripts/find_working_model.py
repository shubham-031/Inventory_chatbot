import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAI
import sys

load_dotenv()

models_to_try = [
    "gemini-1.5-flash-latest",
    "gemini-pro",
    "gemini-1.0-pro",
    "gemini-1.5-flash-latest-8b"
]

for model_name in models_to_try:
    print(f"Trying {model_name}...")
    try:
        llm = GoogleGenerativeAI(model=model_name)
        response = llm.invoke("Hi")
        print(f"✅ Success with {model_name}")
        break
    except Exception as e:
        print(f"❌ Failed with {model_name}: {e}")
