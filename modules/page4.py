from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QLineEdit, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QSizePolicy, QPushButton, QMessageBox, QCompleter)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QDate, QTimer, QStringListModel
from datetime import datetime, timedelta
import requests

from database.db_manager import get_parking_id, get_cloud_server_url
from modules.theme_colors import AppColors

class CustomersPage(QWidget):
    def __init__(self):
        super().__init__()

        self.setStyleSheet(f"background-color: {AppColors.BG_WHITE};")
        layout = QVBoxLayout(self)

        # Lấy thông tin từ config
        self.parking_id = get_parking_id()
        self.cloud_server_url = get_cloud_server_url()

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
        """Update cache danh sách biển số để dùng cho auto-suggest từ API"""
        try:
            # Gọi API để lấy danh sách registers
            api_url = f"{self.cloud_server_url}registers/get_register_list"
            response = requests.post(api_url, json={"parking_id": self.parking_id}, timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                registers = result.get("data", [])
                
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
        """Refresh the data from API and update the table."""
        # Clear existing data in the table
        self.table_widget.setRowCount(0)
        
        # Reset search placeholder
        self.search_field.setPlaceholderText("Search by License...")

        try:
            # Gọi API để lấy danh sách registers
            api_url = f"{self.cloud_server_url}registers/get_register_list"
            response = requests.post(api_url, json={"parking_id": self.parking_id}, timeout=10)
            
            if response.status_code != 200:
                QMessageBox.warning(self, "Warning", "Không thể lấy dữ liệu từ server")
                return
            
            result = response.json()
            registers = result.get("data", [])

            # Populate the table with data from API
            for row, record in enumerate(registers):
                self.table_widget.insertRow(row)
                self.table_widget.setItem(row, 0, QTableWidgetItem(record.get("user_id", "")))
                self.table_widget.setItem(row, 1, QTableWidgetItem(record.get("license_plate", "")))
                
                # Parse and format dates
                expired_str = CustomersPage.format_date(record.get("expired"))
                register_time_str = CustomersPage.format_date(record.get("register_time"))

                # Add formatted dates to the table
                self.table_widget.setItem(row, 2, QTableWidgetItem(register_time_str))
                self.table_widget.setItem(row, 3, QTableWidgetItem(expired_str))
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Lỗi khi tải dữ liệu:\n{str(e)}")

    @staticmethod
    def format_date(date_object):
        """
        Convert ISODate object to dd-MM-yyyy HH:MM:SS format.
        Handles missing or invalid dates gracefully.
        Supports: datetime object, ISO string, MongoDB $date format
        """
        try:
            # Case 1: datetime object
            if isinstance(date_object, datetime):
                return date_object.strftime("%d-%m-%Y %H:%M:%S")
            
            # Case 2: dict with $date key (MongoDB json_util format)
            elif isinstance(date_object, dict) and "$date" in date_object:
                date_str = date_object["$date"]
                date_parsed = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                return date_parsed.strftime("%d-%m-%Y %H:%M:%S")
            
            # Case 3: ISO string format
            elif isinstance(date_object, str):
                date_parsed = datetime.fromisoformat(date_object.replace("Z", "+00:00"))
                return date_parsed.strftime("%d-%m-%Y %H:%M:%S")
                
        except (ValueError, TypeError, AttributeError) as e:
            print(f"Error parsing date: {date_object}, error: {e}")
            pass
        
        return "Invalid Date"


    def search_data(self):
        """Search the data based on license plate (supports partial matching) via API."""
        # Clear existing data in the table
        self.table_widget.setRowCount(0)
        
        # Get the search query from search field
        search_query = self.search_field.text().strip()

        # Nếu search box rỗng, hiển thị tất cả
        if not search_query:
            self.refresh_table()
            return

        try:
            # Gọi API để lấy danh sách registers
            api_url = f"{self.cloud_server_url}registers/get_register_list"
            response = requests.post(api_url, json={"parking_id": self.parking_id}, timeout=10)
            
            if response.status_code != 200:
                self.search_field.setPlaceholderText(f"No results for '{search_query}'")
                return
            
            result = response.json()
            registers = result.get("data", [])
            
            # Filter theo search query (case-insensitive)
            filtered_data = [
                reg for reg in registers 
                if search_query.lower() in reg.get("license_plate", "").lower()
            ]
            
            # Populate the table with filtered data
            for row, record in enumerate(filtered_data):
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
            if len(filtered_data) == 0:
                self.search_field.setPlaceholderText(f"No results for '{search_query}'")
            else:
                self.search_field.setPlaceholderText(f"Found {len(filtered_data)} result(s)")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Lỗi khi tìm kiếm:\n{str(e)}")

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
