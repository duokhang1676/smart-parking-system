"""
Database package
Quản lý kết nối MongoDB và các thao tác database
"""

from .db_manager import (
    DatabaseManager,
    db_manager,
    get_collection,
    get_database,
    get_client
)

__all__ = [
    'DatabaseManager',
    'db_manager',
    'get_collection',
    'get_database',
    'get_client'
]
