from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QDateEdit, 
                             QLineEdit, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QSizePolicy, QPushButton, QMessageBox, QCompleter)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QDate, QTimer, QStringListModel
from datetime import datetime, timedelta

# Import DatabaseManager
from database.db_manager import get_collection, db_manager
from modules.theme_colors import AppColors

class HistoryPage(QWidget):
    def __init__(self):
        super().__init__()

        self.setStyleSheet(f"background-color: {AppColors.BG_WHITE};")
        layout = QVBoxLayout(self)

        # Kết nối tới MongoDB qua DatabaseManager
        try:
            self.collection = get_collection("histories") 
            
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

        # Cache cho license plates (tối ưu hiệu suất search)
        self.license_plates_cache = []
        self.cache_timer = QTimer()
        self.cache_timer.timeout.connect(self.update_license_cache)
        
        # Debounce timer cho search (tránh query liên tục khi gõ)
        self.search_debounce_timer = QTimer()
        self.search_debounce_timer.setSingleShot(True)
        self.search_debounce_timer.timeout.connect(self.perform_search)

        # Top layout
        main_layout = QVBoxLayout()

        # Search and Date Selector
        search_date_layout = QHBoxLayout()

        # Date picker - LUÔN TRẮNG CHỮ ĐEN
        self.date_picker = QDateEdit()
        self.date_picker.setDisplayFormat("yyyy-MM-dd")
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setStyleSheet(f"""
            QDateEdit {{
                padding: 8px;
                font-size: 14px;
                background-color: {AppColors.SEARCH_BG};
                color: {AppColors.SEARCH_TEXT};
                border: 2px solid {AppColors.SEARCH_BORDER};
                border-radius: 6px;
            }}
        """)
        self.date_picker.setDate(QDate.currentDate())  # Ngày hôm nay
        search_date_layout.addWidget(self.date_picker)

        # Search bar - LUÔN TRẮNG CHỮ ĐEN (không đổi theo theme)
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
        
        # Button "Search All" - Màu gradient tím khớp navigation
        self.search_all_button = QPushButton("🔍 All")
        self.search_all_button.setStyleSheet(f"""
            QPushButton {{
                font-size: 14px;
                padding: 8px;
                max-width: 180px;
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
        self.search_all_button.setToolTip("Tìm kiếm tất cả các ngày")
        self.search_all_button.clicked.connect(self.search_all_data)
        search_date_layout.addWidget(self.search_all_button)

        main_layout.addLayout(search_date_layout)

        # Table widget
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(6)
        self.table_widget.setHorizontalHeaderLabels([
            "License Plate", "User ID", "Time In", "Time Out", "Parking Time (h)", "Total Price"
        ])

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

        # Connect search field và date picker
        # Dùng textChanged thay vì returnPressed để auto-search với debounce
        self.search_field.textChanged.connect(self.on_search_text_changed)
        self.search_field.returnPressed.connect(self.search_data)  # Giữ lại Enter để search ngay
  
        # Load cache và refresh table
        self.update_license_cache()
        self.refresh_table()

    def update_license_cache(self):
        """Update cache danh sách biển số xe từ MongoDB"""
        if self.collection is None:
            return
        
        try:
            # Lấy tất cả license plates unique (distinct)
            self.license_plates_cache = self.collection.distinct("license_plate")
            
            # Update model cho QCompleter
            self.completer_model.setStringList(self.license_plates_cache)
            
        except Exception as e:
            print(f"Error updating license cache: {e}")
    
    def on_search_text_changed(self):
        """Được gọi khi user gõ vào search field - dùng debounce"""
        # Hủy timer cũ nếu đang chạy
        self.search_debounce_timer.stop()
        
        # Chỉ auto-search nếu có text (tránh query rỗng)
        if self.search_field.text().strip():
            # Đợi 500ms sau khi user ngừng gõ mới search
            self.search_debounce_timer.start(300)
    
    def perform_search(self):
        """Thực hiện search thực sự sau khi debounce"""
        self.search_data()
    
    def search_all_data(self):
        """Tìm kiếm tất cả các ngày (không filter ngày)"""
        if self.collection is None:
            QMessageBox.warning(self, "Warning", "Không có kết nối database")
            return
        
        # Clear existing data in the table
        self.table_widget.setRowCount(0)
        
        # Get the search query from search field
        search_query = self.search_field.text().strip()
        
        try:
            # Tạo query filter (chỉ license plate, không filter ngày)
            query_filter = {}
            
            if search_query:
                query_filter["license_plate"] = {"$regex": search_query, "$options": "i"}
            
            # Thực hiện truy vấn
            data = list(self.collection.find(query_filter).sort("time_out", -1))
            
            # Populate the table with filtered data
            for row, record in enumerate(data):
                self.table_widget.insertRow(row)
                
                # License Plate
                self.table_widget.setItem(row, 0, QTableWidgetItem(record.get("license_plate", "")))
                
                # User ID
                self.table_widget.setItem(row, 1, QTableWidgetItem(record.get("user_id", "")))
                
                # Time In
                time_in = record.get("time_in", "")
                time_in_str = time_in.strftime('%Y-%m-%d %H:%M:%S') if time_in else ""
                self.table_widget.setItem(row, 2, QTableWidgetItem(time_in_str))
                
                # Time Out
                time_out = record.get("time_out", "")
                time_out_str = time_out.strftime('%Y-%m-%d %H:%M:%S') if time_out else ""
                self.table_widget.setItem(row, 3, QTableWidgetItem(time_out_str))
                
                # Parking Time (hours)
                parking_time = record.get("parking_time", 0)
                formatted_time = format_parking_time(parking_time)
                self.table_widget.setItem(row, 4, QTableWidgetItem(formatted_time))
                
                # Total Price
                total_price = record.get("total_price", 0)
                self.table_widget.setItem(row, 5, QTableWidgetItem(f"{total_price:,.0f} VNĐ"))
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Lỗi khi tìm kiếm:\n{str(e)}")


    def refresh_table(self):
        """Refresh the data from MongoDB and update the table."""
        # Kiểm tra kết nối
        if self.collection is None:
            QMessageBox.warning(self, "Warning", "Không có kết nối database")
            return
        
        # Clear existing data in the table
        self.table_widget.setRowCount(0)

        try:
            # Retrieve data from MongoDB collection
            data = self.collection.find().sort("time_out", -1)

            # Populate the table with data from MongoDB
            for row, record in enumerate(data):
                self.table_widget.insertRow(row)
                
                # License Plate
                self.table_widget.setItem(row, 0, QTableWidgetItem(record.get("license_plate", "")))
                
                # User ID
                self.table_widget.setItem(row, 1, QTableWidgetItem(record.get("user_id", "")))
                
                # Time In
                time_in = record.get("time_in", "")
                time_in_str = time_in.strftime('%Y-%m-%d %H:%M:%S') if time_in else ""
                self.table_widget.setItem(row, 2, QTableWidgetItem(time_in_str))
                
                # Time Out
                time_out = record.get("time_out", "")
                time_out_str = time_out.strftime('%Y-%m-%d %H:%M:%S') if time_out else ""
                self.table_widget.setItem(row, 3, QTableWidgetItem(time_out_str))
                
                # Parking Time (hours)
                parking_time = record.get("parking_time", 0)
                formatted_time = format_parking_time(parking_time)
                self.table_widget.setItem(row, 4, QTableWidgetItem(formatted_time))

                # Total Price
                total_price = record.get("total_price", 0)
                self.table_widget.setItem(row, 5, QTableWidgetItem(f"{total_price:,.0f} VNĐ"))
            
            # Update cache sau khi refresh (để có data mới nhất)
            self.update_license_cache()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Lỗi khi tải dữ liệu:\n{str(e)}")

    def search_data(self):
        """Search the data based on the selected date and license (hỗ trợ tìm gần đúng)."""
        # Kiểm tra kết nối
        if self.collection is None:
            QMessageBox.warning(self, "Warning", "Không có kết nối database")
            return
        
        # Clear existing data in the table
        self.table_widget.setRowCount(0)

        # Get the selected date from date picker
        selected_date = self.date_picker.date().toString("yyyy-MM-dd")
        
        # Get the search query from search field
        search_query = self.search_field.text().strip()

        try:
            # Chuyển đổi selected_date thành một đối tượng datetime
            date_object = datetime.strptime(selected_date, "%Y-%m-%d")

            # Tạo ISODate cho MongoDB (đặt giờ là 00:00:00)
            start_of_day = datetime(date_object.year, date_object.month, date_object.day)

            # Tạo đối tượng end_of_day (23:59:59) của ngày đã chọn
            end_of_day = start_of_day + timedelta(days=1)  # Cộng thêm 1 ngày để lấy ngày hôm sau

            # Tạo query filter
            query_filter = {
                "time_out": {
                    "$gte": start_of_day,  # Tìm tài liệu có time_out lớn hơn hoặc bằng 00:00:00 của ngày đã chọn
                    "$lt": end_of_day  # Tìm tài liệu có time_out nhỏ hơn 00:00:00 của ngày hôm sau
                }
            }
            
            # Thêm điều kiện license plate nếu có search query
            # Dùng regex để tìm gần đúng (case-insensitive, substring match)
            if search_query:
                query_filter["license_plate"] = {"$regex": search_query, "$options": "i"}
            
            # Thực hiện truy vấn
            data = list(self.collection.find(query_filter).sort("time_out", -1))
            
            # Populate the table with filtered data
            for row, record in enumerate(data):
                self.table_widget.insertRow(row)
                
                # License Plate
                self.table_widget.setItem(row, 0, QTableWidgetItem(record.get("license_plate", "")))
                
                # User ID
                self.table_widget.setItem(row, 1, QTableWidgetItem(record.get("user_id", "")))
                
                # Time In
                time_in = record.get("time_in", "")
                time_in_str = time_in.strftime('%Y-%m-%d %H:%M:%S') if time_in else ""
                self.table_widget.setItem(row, 2, QTableWidgetItem(time_in_str))
                
                # Time Out
                time_out = record.get("time_out", "")
                time_out_str = time_out.strftime('%Y-%m-%d %H:%M:%S') if time_out else ""
                self.table_widget.setItem(row, 3, QTableWidgetItem(time_out_str))
                
                # Parking Time (hours)
                parking_time = record.get("parking_time", 0)
                self.table_widget.setItem(row, 4, QTableWidgetItem(f"{parking_time:.2f}"))
                
                # Total Price
                total_price = record.get("total_price", 0)
                self.table_widget.setItem(row, 5, QTableWidgetItem(f"{total_price:,.0f} VNĐ"))
                
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
                    gridline-color: {AppColors.TEXT_BLACK};
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

def format_parking_time(hours):
        h = int(hours)
        m = int((hours - h) * 60)
        if h > 0:
            return f"{h} giờ {m} phút"
        return f"{m} phút"