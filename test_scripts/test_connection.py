import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAI
from pymongo import MongoClient
import sys

# Add current dir to path
sys.path.append(os.getcwd())

load_dotenv()

def test_gemini():
    print("Testing Gemini LLM...")
    try:
        from utils.helpers import model
        response = model.invoke("Reply with 'Hello World'")
        print(f"✅ Gemini Success: {response.strip()}")
        return True
    except Exception as e:
        print(f"❌ Gemini Error: {e}")
        return False

def test_mongodb():
    print("\nTesting MongoDB Connection...")
    uri = os.getenv("MONGODB_URI")
    try:
        client = MongoClient(uri)
        # Try to fetch info
        client.admin.command('ping')
        print("✅ MongoDB Success: Connection established")
        
        db = client['inventory']
        products = db.products.count_documents({})
        print(f"✅ MongoDB Success: Found {products} products in 'inventory' database")
        return True
    except Exception as e:
        print(f"❌ MongoDB Error: {e}")
        return False

if __name__ == "__main__":
    gemini_ok = test_gemini()
    mongo_ok = test_mongodb()
    
    if gemini_ok and mongo_ok:
        print("\n🎉 All services are connected successfully!")
    else:
        print("\n⚠️ Some services failed to connect.")
