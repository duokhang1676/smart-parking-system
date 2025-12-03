from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QDateEdit, 
                             QLineEdit, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QSizePolicy, QPushButton, QMessageBox, QCompleter)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QDate, QTimer, QStringListModel
from datetime import datetime, timedelta
import requests

# Import config helpers
from database.db_manager import get_parking_id, get_cloud_server_url
from modules.theme_colors import AppColors

class HistoryPage(QWidget):
    def __init__(self):
        super().__init__()

        self.setStyleSheet(f"background-color: {AppColors.BG_WHITE};")
        layout = QVBoxLayout(self)

        # Láº¥y thÃ´ng tin tá»« config
        self.parking_id = get_parking_id()
        self.cloud_server_url = get_cloud_server_url()

        # Cache cho license plates (tá»‘i Æ°u hiá»‡u suáº¥t search)
        self.license_plates_cache = []
        self.cache_timer = QTimer()
        self.cache_timer.timeout.connect(self.update_license_cache)
        
        # Debounce timer cho search (trÃ¡nh query liÃªn tá»¥c khi gÃµ)
        self.search_debounce_timer = QTimer()
        self.search_debounce_timer.setSingleShot(True)
        self.search_debounce_timer.timeout.connect(self.perform_search)

        # Top layout
        main_layout = QVBoxLayout()

        # Search and Date Selector
        search_date_layout = QHBoxLayout()

        # Date picker - LUÃ”N TRáº®NG CHá»® ÄEN
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
        self.date_picker.setDate(QDate.currentDate())  # NgÃ y hÃ´m nay
        search_date_layout.addWidget(self.date_picker)

        # Search bar - LUÃ”N TRáº®NG CHá»® ÄEN (khÃ´ng Ä‘á»•i theo theme)
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
        self.completer.setFilterMode(Qt.MatchContains)  # TÃ¬m substring
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer_model = QStringListModel()
        self.completer.setModel(self.completer_model)
        self.search_field.setCompleter(self.completer)
        
        # Button "Search All" - MÃ u gradient tÃ­m khá»›p navigation
        self.search_all_button = QPushButton("ðŸ” All")
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
        self.search_all_button.setToolTip("TÃ¬m kiáº¿m táº¥t cáº£ cÃ¡c ngÃ y")
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
        font.setPointSize(14)  # TÄƒng kÃ­ch thÆ°á»›c font
        self.table_widget.setFont(font)

        # Adjust header font
        header_font = QFont()
        header_font.setPointSize(16)  # Font chá»¯ lá»›n hÆ¡n cho header
        self.table_widget.horizontalHeader().setFont(header_font)

        # Adjust table layout
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)  # Cá»™t tá»± Ä‘á»™ng giÃ£n
        self.table_widget.horizontalHeader().setStretchLastSection(True)  # Cá»™t cuá»‘i chiáº¿m háº¿t pháº§n dÆ°
        self.table_widget.setAlternatingRowColors(False)
        self.table_widget.setRowCount(0)  # Ban Ä‘áº§u khÃ´ng cÃ³ dá»¯ liá»‡u
        
        # Apply initial theme (will be overridden by apply_theme_style)

        # Ensure the table expands to fill available space and scrollbars appear
        self.table_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # Set size policy
        self.table_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)  # Always show vertical scrollbar
        self.table_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)  # Always show horizontal scrollbar

        # Prevent editing
        self.table_widget.setEditTriggers(QTableWidget.NoEditTriggers)  # Disable editing

        # Add table to the main layout
        main_layout.addWidget(self.table_widget)

        # Refresh button - MÃ u gradient tÃ­m khá»›p navigation
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

        # Connect search field vÃ  date picker
        # DÃ¹ng textChanged thay vÃ¬ returnPressed Ä‘á»ƒ auto-search vá»›i debounce
        self.search_field.textChanged.connect(self.on_search_text_changed)
        self.search_field.returnPressed.connect(self.search_data)  # Giá»¯ láº¡i Enter Ä‘á»ƒ search ngay
  
        # Load cache vÃ  refresh table
        self.update_license_cache()
        self.refresh_table()

    def update_license_cache(self):
        """Update cache danh sÃ¡ch biá»ƒn sá»‘ xe tá»« API"""
        try:
            # Gá»i API Ä‘á»ƒ láº¥y táº¥t cáº£ histories
            api_url = f"{self.cloud_server_url}histories/get_parking_histories"
            response = requests.post(api_url, json={"user_id": "all"}, timeout=5)
            
            if response.status_code == 200:
                data = response.json().get("data", [])
                # Láº¥y unique license plates
                license_plates = list(set([item.get("license_plate", "") for item in data if item.get("license_plate")]))
                self.license_plates_cache = sorted(license_plates)
                self.completer_model.setStringList(self.license_plates_cache)
            
        except Exception as e:
            print(f"Error updating license cache: {e}")
    
    def on_search_text_changed(self):
        """ÄÆ°á»£c gá»i khi user gÃµ vÃ o search field - dÃ¹ng debounce"""
        # Há»§y timer cÅ© náº¿u Ä‘ang cháº¡y
        self.search_debounce_timer.stop()
        
        # Chá»‰ auto-search náº¿u cÃ³ text (trÃ¡nh query rá»—ng)
        if self.search_field.text().strip():
            # Äá»£i 500ms sau khi user ngá»«ng gÃµ má»›i search
            self.search_debounce_timer.start(300)
    
    def perform_search(self):
        """Thá»±c hiá»‡n search thá»±c sá»± sau khi debounce"""
        self.search_data()
    
    def search_all_data(self):
        """TÃ¬m kiáº¿m táº¥t cáº£ cÃ¡c ngÃ y (khÃ´ng filter ngÃ y) qua API"""
        self.table_widget.setRowCount(0)
        search_query = self.search_field.text().strip()
        
        try:
            # Gá»i API Ä‘á»ƒ láº¥y táº¥t cáº£ histories
            api_url = f"{self.cloud_server_url}histories/get_parking_histories"
            response = requests.post(api_url, json={"user_id": "all"}, timeout=10)
            
            if response.status_code != 200:
                QMessageBox.warning(self, "Warning", "KhÃ´ng thá»ƒ láº¥y dá»¯ liá»‡u tá»« server")
                return
            
            data = response.json().get("data", [])
            
            # Filter theo search query náº¿u cÃ³
            if search_query:
                data = [item for item in data if search_query.lower() in item.get("license_plate", "").lower()]
            
            # Populate table
            for row, record in enumerate(data):
            # Populate the table with filtered data
            for row, record in enumerate(data):
                self.table_widget.insertRow(row)
                
                self.table_widget.setItem(row, 0, QTableWidgetItem(record.get("license_plate", "")))
                self.table_widget.setItem(row, 1, QTableWidgetItem("N/A"))
                
                # Time In
                time_in_str = record.get("time_in", "")
                if time_in_str:
                    try:
                        time_in_dt = datetime.fromisoformat(time_in_str.replace("Z", "+00:00"))
                        time_in_str = time_in_dt.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        pass
                self.table_widget.setItem(row, 2, QTableWidgetItem(time_in_str))
                
                # Time Out
                time_out_str = record.get("time_out", "")
                if time_out_str:
                    try:
                        time_out_dt = datetime.fromisoformat(time_out_str.replace("Z", "+00:00"))
                        time_out_str = time_out_dt.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        pass
                self.table_widget.setItem(row, 3, QTableWidgetItem(time_out_str))
                
                # Parking Time
                parking_time = record.get("parking_time", 0)
                formatted_time = format_parking_time(parking_time)
                self.table_widget.setItem(row, 4, QTableWidgetItem(formatted_time))
                
                # Total Price
                total_price = record.get("total_price", 0)
                self.table_widget.setItem(row, 5, QTableWidgetItem(f"{total_price:,.0f} VNÄ"))
                self.table_widget.setItem(row, 4, QTableWidgetItem(formatted_time))
                
                # Total Price
                total_price = record.get("total_price", 0)
                self.table_widget.setItem(row, 5, QTableWidgetItem(f"{total_price:,.0f} VNÄ"))
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Lá»—i khi tÃ¬m kiáº¿m:\n{str(e)}")


    def refresh_table(self):
        """Refresh the data from API and update the table."""
        self.table_widget.setRowCount(0)

        try:
            # Gá»i API Ä‘á»ƒ láº¥y táº¥t cáº£ histories
            api_url = f"{self.cloud_server_url}histories/get_parking_histories"
            response = requests.post(api_url, json={"user_id": "all"}, timeout=10)
            
            if response.status_code != 200:
                QMessageBox.warning(self, "Warning", "KhÃ´ng thá»ƒ láº¥y dá»¯ liá»‡u tá»« server")
                return
            
            data = response.json().get("data", [])

            # Populate the table with data from API
            for row, record in enumerate(data):
                self.table_widget.insertRow(row)
                
                # License Plate
                self.table_widget.setItem(row, 0, QTableWidgetItem(record.get("license_plate", "")))
                
                # User ID (khÃ´ng cÃ³ trong API response)
                self.table_widget.setItem(row, 1, QTableWidgetItem("N/A"))
                
