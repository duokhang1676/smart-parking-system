"""
MongoDB Database Manager
Quản lý kết nối MongoDB tập trung cho toàn bộ ứng dụng
"""

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import os
from dotenv import load_dotenv

# Load biến môi trường
load_dotenv()


class DatabaseManager:
    """Singleton class để quản lý kết nối MongoDB"""
    
    _instance = None
    _client = None
    _db = None
    
    def __new__(cls):
        """Singleton pattern - chỉ tạo 1 instance duy nhất"""
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Khởi tạo kết nối MongoDB"""
        # Không tự động connect nữa - chỉ connect khi cần
        pass
    
    def connect(self):
        """Kết nối tới MongoDB (chỉ gọi khi thực sự cần)"""
        # Nếu đã connect rồi thì bỏ qua
        if self._client is not None:
            return
            
        try:
            # Lấy connection string từ biến môi trường
            # Mặc định: localhost nếu không có .env
            MONGODB_URI = os.getenv(
                "MONGODB_URI",
                "mongodb://localhost:27017/"
            )
            DATABASE_NAME = os.getenv("DATABASE_NAME", "server_local")
            
            # Tạo MongoClient với timeout 5 giây
            self._client = MongoClient(
                MONGODB_URI,
                serverSelectionTimeoutMS=5000
            )
            
            # Test kết nối
            self._client.admin.command('ping')
            
            # Kết nối database
            self._db = self._client[DATABASE_NAME]
            
            print(f"✅ Kết nối MongoDB thành công!")
            print(f"📍 URI: {MONGODB_URI[:50]}...")
            print(f"🗄️  Database: {DATABASE_NAME}")
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            print(f"⚠️  Không thể kết nối MongoDB: {e}")
            print(f"💡 Ứng dụng sẽ chạy với API mode (không cần MongoDB local)")
            self._client = None
            self._db = None
            # Không raise exception nữa - để app vẫn chạy được
        except Exception as e:
            print(f"⚠️  Lỗi không xác định: {e}")
            self._client = None
            self._db = None
    
    def get_client(self):
        """Trả về MongoClient instance"""
        if self._client is None:
            self.connect()
        return self._client
    
    def get_database(self):
        """Trả về Database instance"""
        if self._db is None:
            self.connect()
        return self._db
    
    def get_collection(self, collection_name):
        """
        Trả về Collection instance
        
        Args:
            collection_name (str): Tên collection (vd: "History", "Customers")
        
        Returns:
            Collection: MongoDB collection object
        """
        if self._db is None:
            self.connect()
        return self._db[collection_name]
    
    def close(self):
        """Đóng kết nối MongoDB"""
        if self._client:
            self._client.close()
            print("Đã đóng kết nối MongoDB")
            self._client = None
            self._db = None
    
    def is_connected(self):
        """Kiểm tra kết nối có hoạt động không"""
        if self._client is None:
            return False
        try:
            self._client.admin.command('ping')
            return True
        except:
            return False
    
    def list_collections(self):
        """Liệt kê tất cả collections trong database"""
        if self._db is None:
            return []
        return self._db.list_collection_names()


# Tạo instance global để sử dụng trong toàn bộ app
db_manager = DatabaseManager()


# Helper functions để sử dụng nhanh
def get_collection(collection_name):
    """
    Helper function để lấy collection nhanh
    
    Usage:
        from app.database.db_manager import get_collection
        history_col = get_collection("History")
    """
    return db_manager.get_collection(collection_name)


def get_database():
    """
    Helper function để lấy database
    
    Usage:
        from app.database.db_manager import get_database
        db = get_database()
    """
    return db_manager.get_database()


def get_client():
    """
    Helper function để lấy MongoClient
    
    Usage:
        from app.database.db_manager import get_client
        client = get_client()
    """
    return db_manager.get_client()


def get_parking_id():
    """
    Helper function để lấy PARKING_ID từ .env
    
    Usage:
        from app.database.db_manager import get_parking_id
        parking_id = get_parking_id()
    
    Returns:
        str: ID của bãi xe (mặc định: "parking_001")
    """
    return os.getenv("PARKING_ID", "parking_001")


def get_cloud_server_url():
    """
    Helper function để lấy CLOUD_SERVER_URL từ .env
    
    Usage:
        from app.database.db_manager import get_cloud_server_url
        url = get_cloud_server_url()
    
    Returns:
        str: URL của cloud server (mặc định: "https://parking-cloud-server.onrender.com/api/")
    """
    return os.getenv("CLOUD_SERVER_URL", "https://parking-cloud-server.onrender.com/api/")
