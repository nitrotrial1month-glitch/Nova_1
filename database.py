import os
import pymongo
from pymongo import MongoClient
import certifi

# Render থেকে MONGO_URL ভেরিয়েবলটি নেবে
MONGO_URL = os.getenv("MONGO_URL")
ca = certifi.where()

if not MONGO_URL:
    print("❌ Error: MONGO_URL environment variable not found!")
    db = None
else:
    try:
        # ক্লাস্টারের সাথে কানেকশন
        cluster = MongoClient(MONGO_URL, tlsCAFile=ca)
        db = cluster["NovaBotDB"] # আপনার নতুন ডাটাবেসের নাম
        print("✅ MongoDB Connected Successfully!")
    except Exception as e:
        print(f"❌ MongoDB Connection Failed: {e}")
        db = None

class Database:
    @staticmethod
    def get_collection(name):
        """যেকোনো কালেকশন (যেমন: inventory, settings) কল করার শর্টকাট"""
        if db is not None:
            return db[name]
        return None

    # ইকোনমি ব্যালেন্স আপডেট করার ফাংশন
    @staticmethod
    def update_balance(user_id, amount):
        col = Database.get_collection("inventory")
        if col is None: return 0
        uid = str(user_id)
        col.update_one({"_id": uid}, {"$inc": {"balance": amount}}, upsert=True)
        return col.find_one({"_id": uid}).get("balance", 0)

    # ইকোনমি ব্যালেন্স চেক করার ফাংশন
    @staticmethod
    def get_balance(user_id):
        col = Database.get_collection("inventory")
        if col is None: return 0
        data = col.find_one({"_id": str(user_id)})
        return data.get("balance", 0) if data else 0
      
