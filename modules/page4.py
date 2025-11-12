from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QLineEdit, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QSizePolicy, QPushButton, QMessageBox, QCompleter)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QDate, QTimer, QStringListModel
from datetime import datetime, timedelta
from database.db_manager import get_collection, db_manager, get_parking_id

class CustomersPage(QWidget):
    def __init__(self):
        super().__init__()

        self.setStyleSheet("background-color: #FFFFFF;")
        layout = QVBoxLayout(self)

        # Kết nối tới MongoDB
        try:
            self.collection = get_collection("registers")  
            
            # Kiểm tra kết nối
            if not db_manager.is_connected():
                raise ConnectionError("Không thể kết nối MongoDB")
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Database Error",
                f"Không thể kết nối MongoDB:\n{str(e)}\n\n"
                "Kiểm tra:\n"
                "1. MongoDB server đang chạy\n"
                "2. File .env có connection string đúng\n"
                "3. Network connection (nếu dùng Atlas)"
            )
            self.collection = None

        self.parking_id = get_parking_id()

        # Cache cho license plates (tối ưu hiệu suất search)
        self.license_plates_cache = []
        self.cache_timer = QTimer()
        self.cache_timer.timeout.connect(self.update_license_cache)

        # Debounce timer cho search (tránh spam queries)
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)  # Chỉ chạy 1 lần
        self.search_timer.timeout.connect(self.search_data)

        # Top layout
        main_layout = QVBoxLayout()

        # Search and Date Selector
        search_date_layout = QHBoxLayout()

        # Search bar
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Search by License...")
        self.search_field.setStyleSheet("padding: 5px; font-size: 14px;")
        search_date_layout.addWidget(self.search_field)
        
        # Setup QCompleter cho auto-suggest
        self.completer = QCompleter()
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchContains)  # Tìm substring
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer_model = QStringListModel()
        self.completer.setModel(self.completer_model)
        self.search_field.setCompleter(self.completer)

        main_layout.addLayout(search_date_layout)

        # Table widget
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(4)
        self.table_widget.setHorizontalHeaderLabels(["User ID", "License Plate", "Register Time", "Expried"])

        # Adjust font
        font = QFont()
        font.setPointSize(14)  # Tăng kích thước font
        self.table_widget.setFont(font)

        # Adjust header font
        header_font = QFont()
        header_font.setPointSize(16)  # Font chữ lớn hơn cho header
        self.table_widget.horizontalHeader().setFont(header_font)

        # Adjust table layout
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)  # Cột tự động giãn
        self.table_widget.horizontalHeader().setStretchLastSection(True)  # Cột cuối chiếm hết phần dư
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.setRowCount(0)  # Ban đầu không có dữ liệu

        # Ensure the table expands to fill available space and scrollbars appear
        self.table_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # Set size policy
        self.table_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)  # Always show vertical scrollbar
        self.table_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)  # Always show horizontal scrollbar

        # Prevent editing
        self.table_widget.setEditTriggers(QTableWidget.NoEditTriggers)  # Disable editing

        # Add table to the main layout
        main_layout.addWidget(self.table_widget)

        # Refresh button
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setStyleSheet("font-size: 14px; padding: 5px;")
        self.refresh_button.clicked.connect(self.refresh_table)  # Connect refresh button to function
        main_layout.addWidget(self.refresh_button)

        layout.addLayout(main_layout)
        self.setLayout(layout)

        # Bind F5 key to refresh the table
        self.setFocusPolicy(Qt.StrongFocus)
        self.keyPressEvent = self.handle_key_press

        # Connect search field with debouncing
        self.search_field.returnPressed.connect(self.search_data)      # Immediate search on Enter
        self.search_field.textChanged.connect(self.on_search_changed)  # Debounced search as you type
        
        # Update cache mỗi 30 giây
        self.cache_timer.start(30000)
        self.update_license_cache()  # Load cache lần đầu
  
        self.refresh_table()

    def update_license_cache(self):
        """Update cache danh sách biển số để dùng cho auto-suggest"""
        try:
            # Lấy tất cả biển số đã đăng ký của bãi xe này
            registers = self.collection.find(
                {"parking_id": self.parking_id},
                {"license_plate": 1, "_id": 0}
            )
            
            # Extract unique license plates
            self.license_plates_cache = sorted(set(
                reg.get("license_plate", "") 
                for reg in registers 
                if reg.get("license_plate")
            ))
            
            # Update completer model
            self.completer_model.setStringList(self.license_plates_cache)
            
        except Exception as e:
            print(f"Error updating license cache: {e}")

    def on_search_changed(self):
        """Debounced search: Chỉ search sau khi user ngừng gõ 300ms"""
        self.search_timer.stop()  # Hủy timer cũ nếu có
        
        # Visual feedback khi đang chờ
        search_query = self.search_field.text().strip()
        if search_query:
            self.search_field.setPlaceholderText("Searching...")
        else:
            self.search_field.setPlaceholderText("Search by License...")
            
        self.search_timer.start(300)  # Đặt timer mới 300ms

    def refresh_table(self):
        """Refresh the data from MongoDB and update the table."""
        # Clear existing data in the table
        self.table_widget.setRowCount(0)
        
        # Reset search placeholder
        self.search_field.setPlaceholderText("Search by License...")

        # Retrieve data from MongoDB collection - Fixed: Đúng cấu trúc database
        data = self.collection.find(
            {"parking_id": self.parking_id}  # Filter by parking_id
        ).sort("register_time", -1)  # Sort by register_time descending

        # Populate the table with data from MongoDB
        for row, record in enumerate(data):
            self.table_widget.insertRow(row)
            self.table_widget.setItem(row, 0, QTableWidgetItem(record.get("user_id", "")))
            self.table_widget.setItem(row, 1, QTableWidgetItem(record.get("license_plate", "")))
            # Parse and format dates
            expired_str = CustomersPage.format_date(record.get("expired"))
            register_time_str = CustomersPage.format_date(record.get("register_time"))

            # Add formatted dates to the table
            self.table_widget.setItem(row, 2, QTableWidgetItem(register_time_str))
            self.table_widget.setItem(row, 3, QTableWidgetItem(expired_str))

    @staticmethod
    def format_date(date_object):
        """
        Convert ISODate object to dd-MM-yyyy HH:MM:SS format.
        Handles missing or invalid dates gracefully.
        """
        try:
            if isinstance(date_object, datetime):
                return date_object.strftime("%d-%m-%Y %H:%M:%S")
            elif isinstance(date_object, str):
                # Handle ISO string format
                date_parsed = datetime.fromisoformat(date_object.replace("Z", "+00:00"))
                return date_parsed.strftime("%d-%m-%Y %H:%M:%S")
        except (ValueError, TypeError, AttributeError):
            pass
        return "Invalid Date"


    def search_data(self):
        """Search the data based on license plate (supports partial matching)."""
        # Clear existing data in the table
        self.table_widget.setRowCount(0)
        
        # Get the search query from search field
        search_query = self.search_field.text().strip()

        # Nếu search box rỗng, hiển thị tất cả
        if not search_query:
            self.refresh_table()
            return

        # Thực hiện truy vấn với regex để tìm kiếm linh hoạt (case-insensitive partial match)
        data = self.collection.find({
            "parking_id": self.parking_id,  # Filter by parking_id
            "license_plate": {"$regex": search_query, "$options": "i"}  # Partial match, case-insensitive
        }).sort("register_time", -1)
        
        # Đếm số kết quả
        result_count = self.collection.count_documents({
            "parking_id": self.parking_id,
            "license_plate": {"$regex": search_query, "$options": "i"}
        })
        
        # Populate the table with filtered data
        for row, record in enumerate(data):
            self.table_widget.insertRow(row)
            self.table_widget.setItem(row, 0, QTableWidgetItem(record.get("user_id", "")))
            self.table_widget.setItem(row, 1, QTableWidgetItem(record.get("license_plate", "")))
            # Parse and format dates
            expired_str = CustomersPage.format_date(record.get("expired"))
            register_time_str = CustomersPage.format_date(record.get("register_time"))

            # Add formatted dates to the table
            self.table_widget.setItem(row, 2, QTableWidgetItem(register_time_str))
            self.table_widget.setItem(row, 3, QTableWidgetItem(expired_str))
        
        # Update placeholder với số kết quả
        if result_count == 0:
            self.search_field.setPlaceholderText(f"No results for '{search_query}'")
        else:
            self.search_field.setPlaceholderText(f"Found {result_count} result(s)")

    def handle_key_press(self, event):
        """Handle key press events, specifically F5 for refresh."""
        if event.key() == Qt.Key_F5:
            self.refresh_table()  # Refresh table when F5 is pressed
