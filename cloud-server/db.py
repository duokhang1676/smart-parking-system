from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os

def get_db():
    """
    Kết nối đến MongoDB và trả về đối tượng database.
    """
    # Load biến môi trường từ file .env
    load_dotenv()

    # Lấy connection string từ biến môi trường
    uri = os.getenv("MONGO_URI")

    # Create a new client and connect to the server
    client = MongoClient(uri, server_api=ServerApi('1'))

    # Send a ping to confirm a successful connection
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)

    db = client["Smart_Parking"]
    return db


db = get_db()
customers_collection = db["customers"]  # Collection MongoDB
customers = list(customers_collection.find({}, {"_id": 0}))
print(customers)
