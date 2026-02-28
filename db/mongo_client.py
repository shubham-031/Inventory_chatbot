from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()


class MongoDBClient:
    """MongoDB connection manager"""
    
    def __init__(self):
        self.client = None
        self.db = None
        self.uri = os.getenv("MONGODB_URI")
        
    def connect(self):
        """Establish MongoDB connection"""
        if self.client is None:
            try:
                self.client = MongoClient(self.uri)
                # Get database name from URI or use default
                db_name = "inventry"  # Change this to match your database
                self.db = self.client[db_name]
                print(f"✅ Connected to MongoDB database: {db_name}")
                return self.db
            except Exception as e:
                print(f"❌ MongoDB Connection Error: {e}")
                raise
        return self.db
    
    def disconnect(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
            print("✅ MongoDB connection closed")
    
    def get_collection(self, collection_name: str):
        """Get a specific collection"""
        if self.db is None:
            self.connect()
        return self.db[collection_name]


# Singleton instance
mongo_client = MongoDBClient()