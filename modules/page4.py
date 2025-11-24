from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QLineEdit, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QSizePolicy, QPushButton, QMessageBox, QCompleter)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QDate, QTimer, QStringListModel
from datetime import datetime, timedelta
from database.db_manager import get_collection, db_manager, get_parking_id
from modules.theme_colors import AppColors

class CustomersPage(QWidget):
    def __init__(self):
        super().__init__()

        self.setStyleSheet(f"background-color: {AppColors.BG_WHITE};")
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

        # Search bar - LUÔN TRẮNG CHỮ ĐEN
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Search by License...")
        self.search_field.setStyleSheet(f"""
            QLineEdit {{
                padding: 8px;
                font-size: 14px;
                background-color: {AppColors.SEARCH_BG};
                color: {AppColors.SEARCH_TEXT};
                border: 2px solid {AppColors.SEARCH_BORDER};
                border-radius: 6px;
            }}
            QLineEdit:focus {{
                border-color: {AppColors.SEARCH_FOCUS};
            }}
        """)
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
        self.table_widget.setAlternatingRowColors(False)
        self.table_widget.setRowCount(0)  # Ban đầu không có dữ liệu
        
        # Apply initial theme (will be overridden by apply_theme_style)

        # Ensure the table expands to fill available space and scrollbars appear
        self.table_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # Set size policy
        self.table_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)  # Always show vertical scrollbar
        self.table_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)  # Always show horizontal scrollbar

        # Prevent editing
        self.table_widget.setEditTriggers(QTableWidget.NoEditTriggers)  # Disable editing

        # Add table to the main layout
        main_layout.addWidget(self.table_widget)

        # Refresh button - Màu gradient tím khớp navigation
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setStyleSheet(f"""
            QPushButton {{
                font-size: 14px;
                padding: 8px;
                background: {AppColors.get_gradient_style()};
                color: {AppColors.TEXT_WHITE};
                border: none;
                border-radius: 6px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {AppColors.get_hover_gradient_style()};
            }}
        """)
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
    
    def apply_theme_style(self, is_dark):
        """Apply theme-specific styling to table (called by MainWindow on theme toggle)"""
        if is_dark:
            # Dark mode
            self.table_widget.setStyleSheet(f"""
                QTableWidget {{
                    background-color: {AppColors.BG_DARK};
                    color: {AppColors.TEXT_WHITE};
                    gridline-color: {AppColors.BORDER_GRID_DARK};
                    border: 1px solid {AppColors.BORDER_DARK};
                }}
                QTableWidget::item {{
                    padding: 8px;
                    color: {AppColors.TEXT_WHITE};
                }}
                QTableWidget::item:selected {{
                    background-color: {AppColors.ACCENT_DARK_PURPLE};
                    color: {AppColors.TEXT_WHITE};
                }}
                QHeaderView::section {{
                    background-color: {AppColors.BG_DARK_HEADER};
                    color: {AppColors.TEXT_WHITE};
                    padding: 10px;
                    border: 1px solid {AppColors.BORDER_DARK};
                    font-weight: bold;
                }}
            """)
        else:
            # Light mode
            self.table_widget.setStyleSheet(f"""
                QTableWidget {{
                    background-color: {AppColors.BG_WHITE};
                    color: {AppColors.TEXT_BLACK};
                    gridline-color: {AppColors.BORDER_GRID_LIGHT};
                    border: 1px solid {AppColors.BORDER_LIGHT};
                }}
                QTableWidget::item {{
                    padding: 8px;
                    color: {AppColors.TEXT_BLACK};
                }}
                QTableWidget::item:selected {{
                    background-color: {AppColors.ACCENT_LIGHT_PURPLE};
                    color: {AppColors.TEXT_BLACK};
                }}
                QHeaderView::section {{
                    background-color: {AppColors.BG_LIGHT_GRAY};
                    color: {AppColors.TEXT_BLACK};
                    padding: 10px;
                    border: 1px solid {AppColors.BORDER_LIGHT};
                    font-weight: bold;
                }}
            """)
