from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QDateEdit, 
                             QLineEdit, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QSizePolicy, QPushButton, QMessageBox, QCompleter)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QDate, QTimer, QStringListModel
from datetime import datetime, timedelta

from database.db_manager import db_manager, get_collection, get_parking_id
from modules.theme_colors import AppColors

class CarsInParkingPage(QWidget):
    def __init__(self):
        super().__init__()

        self.setStyleSheet(f"background-color: {AppColors.BG_WHITE};")
        layout = QVBoxLayout(self)

        # Lấy PARKING_ID từ config
        self.parking_id = get_parking_id()

        # Kết nối tới MongoDB
        try:
            self.collection = get_collection("parked_vehicles")  
            
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
        
        # Setup QCompleter cho auto-suggest (SAU khi tạo search_field)
        self.completer = QCompleter()
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchContains)  # Tìm substring
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer_model = QStringListModel()
        self.completer.setModel(self.completer_model)
        self.search_field.setCompleter(self.completer)  # ← Bây giờ OK!

        # Button "Search All" - Màu gradient tím khớp navigation
        self.search_all_button = QPushButton("🔍 All")
        self.search_all_button.setStyleSheet(f"""
            QPushButton {{
                font-size: 14px;
                padding: 8px;
                max-width: 100px;
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
        self.search_all_button.setToolTip("Tìm kiếm tất cả xe đang đỗ")
        self.search_all_button.clicked.connect(self.search_all_data)
        search_date_layout.addWidget(self.search_all_button)
        
        # Add search layout to main layout
        main_layout.addLayout(search_date_layout)

        # Table widget
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(6)  # Thêm cột Slot
        self.table_widget.setHorizontalHeaderLabels([
            "License Plate", "User ID", "Customer Type", "Time In", "Parking Time", "Slot"
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
        
        # Apply initial theme (will be overridden by apply_theme_style)
        self.table_widget.setRowCount(0)  # Ban đầu không có dữ liệu

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

        # Connect search field and date picker to search function
        self.search_field.textChanged.connect(self.on_search_text_changed)
        self.search_field.returnPressed.connect(self.search_data)
  
        # Load cache và refresh table
        self.update_license_cache()
        self.refresh_table()

    def update_license_cache(self):
        """
        Update cache danh sách biển số xe từ MongoDB.
        Data có cấu trúc NESTED (lồng nhau)!
        CHỈ lấy xe từ bãi hiện tại (self.parking_id)
        """
        if self.collection is None:
            return
        
        try:
            license_plates = []
            
            # Lấy ONLY document của bãi xe hiện tại
            parking_doc = self.collection.find_one({"parking_id": self.parking_id})
            
            if parking_doc:
                # Lấy mảng "list" chứa các xe
                vehicles = parking_doc.get("list", [])
                
                # Loop qua từng xe trong mảng
                for vehicle in vehicles:
                    plate = vehicle.get("license_plate", "")
                    if plate and plate not in license_plates:
                        license_plates.append(plate)
            
            self.license_plates_cache = license_plates
            self.completer_model.setStringList(self.license_plates_cache)
            
        except Exception as e:
            print(f"Lỗi update cache: {e}")
    
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
        """Tìm tất cả xe đang đỗ (bỏ qua filter)"""
        if not self.search_field.text().strip():
            self.refresh_table()
        else:
            self.search_data()

    def refresh_table(self):
        """
        Refresh the data from MongoDB and update the table.
        
        NESTED data structure!
        Document structure:
        {
          "parking_id": "parking_001",
            "list": [
                {"license_plate": "30K-55055", "user_id": "00", ...},
                {"license_plate": "30G-49344", "user_id": "01", ...}
            ]
        }
        """
        if self.collection is None:
            QMessageBox.warning(self, "Warning", "No database connection")
            return
        
        self.table_widget.setRowCount(0)

        try:
            # Lấy ONLY document của bãi xe hiện tại
            parking_doc = self.collection.find_one({"parking_id": self.parking_id})
            
            if not parking_doc:
                print(f"Parking not found: {self.parking_id}")
                return
            
            row = 0
            
            # Lấy danh sách xe trong bãi (nested array)
            vehicles = parking_doc.get("list", [])
            
            # Loop qua từng xe
            for vehicle in vehicles:
                self.table_widget.insertRow(row)
                
                # Cột 0: License Plate
                self.table_widget.setItem(row, 0, QTableWidgetItem(
                    vehicle.get("license_plate", "")
                ))
                
                # Cột 1: User ID
                self.table_widget.setItem(row, 1, QTableWidgetItem(
                    vehicle.get("user_id", "")
                ))
                
                # Cột 2: Customer Type
                self.table_widget.setItem(row, 2, QTableWidgetItem(
                    vehicle.get("customer_type", "")
                ))
                
                # Cột 3: Time In
                time_in = vehicle.get("time_in")
                
                # Xử lý 2 format: ISO string hoặc datetime object
                if isinstance(time_in, str):
                    # Parse ISO string: "2025-09-06T10:03:07.846794"
                    try:
                        time_in = datetime.fromisoformat(time_in.replace('Z', '+00:00'))
                    except:
                        time_in = None
                
                time_in_str = time_in.strftime('%Y-%m-%d %H:%M:%S') if time_in else "N/A"
                self.table_widget.setItem(row, 3, QTableWidgetItem(time_in_str))
                
                # Cột 4: Parking Time (REAL-TIME calculation)
                if time_in:
                    parking_hours = (datetime.now() - time_in).total_seconds() / 3600
                    parking_time_str = self.format_parking_time(parking_hours)
                else:
                    parking_time_str = "N/A"
                
                self.table_widget.setItem(row, 4, QTableWidgetItem(parking_time_str))
                
                # Cột 5: Slot
                self.table_widget.setItem(row, 5, QTableWidgetItem(
                    vehicle.get("slot_name", "")
                ))
                
                row += 1
            
            # Update cache sau khi refresh
            self.update_license_cache()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Cannot load data:\n{str(e)}")

    def search_data(self):
        """Search the data based on the selected date and license."""
        import re
        
        # Clear existing data in the table
        self.table_widget.setRowCount(0)
        
        # Get the search query from search field
        search_query = self.search_field.text().strip()
        
        if not search_query:
            # If search is empty, show all data
            self.refresh_table()
            return
        
        try:
            # Fetch ONLY bãi xe hiện tại
            parking_doc = self.collection.find_one({"parking_id": self.parking_id})
            
            if not parking_doc:
                print(f"Parking is not found: {self.parking_id}")
                return
            
            # Create case-insensitive regex pattern
            pattern = re.compile(search_query, re.IGNORECASE)
            
            # Loop through vehicles to find matches
            row = 0
            vehicles = parking_doc.get("list", [])
            for vehicle in vehicles:
                license_plate = vehicle.get("license_plate", "")
                
                # Filter by regex pattern
                if pattern.search(license_plate):
                    self.table_widget.insertRow(row)
                    
                    # Column 0: License Plate
                    self.table_widget.setItem(row, 0, QTableWidgetItem(license_plate))
                    
                    # Column 1: User ID
                    user_id = vehicle.get("user_id", "")
                    self.table_widget.setItem(row, 1, QTableWidgetItem(user_id))
                    
                    # Column 2: Customer Type
                    customer_type = vehicle.get("customer_type", "")
                    self.table_widget.setItem(row, 2, QTableWidgetItem(customer_type))
                    
                    # Column 3: Time In
                    time_in = vehicle.get("time_in", "")
                    if isinstance(time_in, str):
                        try:
                            time_in = datetime.fromisoformat(time_in.replace('Z', '+00:00'))
                        except:
                            time_in = datetime.now()
                    time_in_str = time_in.strftime('%Y-%m-%d %H:%M:%S') if time_in else ""
                    self.table_widget.setItem(row, 3, QTableWidgetItem(time_in_str))
                    
                    # Column 4: Parking Time (real-time calculation)
                    if time_in:
                        parking_hours = (datetime.now() - time_in).total_seconds() / 3600
                        parking_time_str = self.format_parking_time(parking_hours)
                    else:
                        parking_time_str = "N/A"
                    self.table_widget.setItem(row, 4, QTableWidgetItem(parking_time_str))
                    
                    # Column 5: Slot
                    slot_name = vehicle.get("slot_name", "")
                    self.table_widget.setItem(row, 5, QTableWidgetItem(slot_name))
                    
                    row += 1
        
        except Exception as e:
            QMessageBox.critical(self, "Search Error", f"Error searching data: {str(e)}")


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

    def format_parking_time(self, hours):
        """Format parking time thành 'Xh Ym' dễ đọc hơn"""
        h = int(hours)
        m = int((hours - h) * 60)
        if h > 0:
            return f"{h}h {m}m"
        return f"{m}m"
