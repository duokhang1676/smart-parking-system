from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QGridLayout, QFrame, QScrollArea, QPushButton)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QSize
from PyQt5.QtGui import QColor, QPalette, QFont, QIcon
import qtawesome as qta
import requests
from database.db_manager import get_parking_id, get_cloud_server_url

class ParkingSlotPage(QWidget):
    def __init__(self):
        super().__init__()
        
        # Lấy PARKING_ID từ config
        self.parking_id = get_parking_id()
        
        # Lấy Cloud Server URL từ config
        self.cloud_server_url = get_cloud_server_url()
        self.url_cloud_server = self.cloud_server_url  # Alias để Thread có thể dùng
        
        self.slot_names = ['A0', 'B0', 'C0', 'D0', 'A1', 'B1', 'C1', 'D1', 
                          'A2', 'B2', 'C2', 'D2', 'A3', 'B3', 'C3', 'D3', 
                          'A4', 'B4', 'C4', 'D4']
        self.slots = {}
        self.duplicate_licenses = {}  # Track duplicate license plates
        
        # Theme state (default dark)
        self.is_dark_theme = True
        
        self.init_ui()

        # Timer for data update
        self.timer = QTimer()
        self.timer.timeout.connect(self.fetch_and_update_data)
        self.timer.start(1000)

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)
        
        # ========== DASHBOARD STATS ==========
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)
        
        # Stat cards
        self.total_slots_card = self.create_stat_card(
            "Total Slots", "20", 
            qta.icon('fa5s.car', color='#2196F3'), 
            "#E3F2FD", "#2196F3"
        )
        self.occupied_card = self.create_stat_card(
            "Occupied", "0", 
            qta.icon('fa5s.parking', color='#F44336'), 
            "#FFEBEE", "#F44336"
        )
        self.available_card = self.create_stat_card(
            "Available", "20", 
            qta.icon('fa5s.check-circle', color='#4CAF50'), 
            "#E8F5E9", "#4CAF50"
        )
        self.occupancy_card = self.create_stat_card(
            "Occupancy", "0%", 
            qta.icon('fa5s.chart-pie', color="#F7D9AD"), 
            "#FFF3E0", "#FFC163"
        )
        
        stats_layout.addWidget(self.total_slots_card)
        stats_layout.addWidget(self.occupied_card)
        stats_layout.addWidget(self.available_card)
        stats_layout.addWidget(self.occupancy_card)
        
        main_layout.addLayout(stats_layout)
        
        # ========== WARNING BANNER (Hidden by default) ==========
        self.warning_banner = QFrame()
        self.warning_banner.setObjectName("warningBanner")
        self.warning_banner.setStyleSheet("""
            #warningBanner {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FF6B6B, stop:1 #EE5A6F);
                border-radius: 8px;
                border-left: 4px solid #C62828;
                padding: 12px;
            }
        """)
        
        warning_layout = QHBoxLayout()
        
        # Warning icon
        warning_icon = QLabel()
        warning_icon.setPixmap(qta.icon('fa5s.exclamation-triangle', color='white').pixmap(QSize(24, 24)))
        
        # Warning text
        self.warning_text = QLabel()
        self.warning_text.setStyleSheet("""
            color: white;
            font-size: 14px;
            font-weight: bold;
        """)
        
        warning_layout.addWidget(warning_icon)
        warning_layout.addWidget(self.warning_text, 1)
        self.warning_banner.setLayout(warning_layout)
        self.warning_banner.hide()  # Hidden initially
        
        main_layout.addWidget(self.warning_banner)
        
        # ========== PARKING SLOTS GRID ==========
        # Scroll area for slots
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        slots_container = QWidget()
        slots_layout = QGridLayout()
        slots_layout.setSpacing(12)
        
        for i, slot_name in enumerate(self.slot_names):
            slot_widget = self.create_modern_slot(slot_name, "")
            slots_layout.addWidget(slot_widget, i // 4, i % 4)
            self.slots[slot_name] = slot_widget
        
        slots_container.setLayout(slots_layout)
        scroll.setWidget(slots_container)
        main_layout.addWidget(scroll)
        
        # ========== REFRESH BUTTON ==========
        refresh_btn = QPushButton()
        refresh_btn.setText("Refresh Now")
        refresh_btn.setIcon(qta.icon('fa5s.sync-alt', color='white'))
        refresh_btn.clicked.connect(self.fetch_and_update_data)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #00BCD4;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00ACC1;
            }
            QPushButton:pressed {
                background-color: #0097A7;
            }
        """)
        main_layout.addWidget(refresh_btn, alignment=Qt.AlignCenter)
        
        self.setLayout(main_layout)
    
    def create_stat_card(self, title, value, icon, bg_color, text_color):
        """Create a modern stat card with icon"""
        card = QFrame()
        card.setObjectName("statCard")
        card.setStyleSheet(f"""
            #statCard {{
                background-color: {bg_color};
                border-radius: 12px;
                border-left: 4px solid {text_color};
                padding: 16px;
            }}
        """)
        
        layout = QHBoxLayout()
        layout.setSpacing(12)
        
        # Icon
        icon_label = QLabel()
        icon_label.setPixmap(icon.pixmap(QSize(40, 40)))
        layout.addWidget(icon_label)
        
        # Text
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            color: {text_color};
            font-size: 12px;
            font-weight: 600;
            opacity: 0.8;
        """)
        
        value_label = QLabel(value)
        value_label.setObjectName("valueLabel")
        value_label.setStyleSheet(f"""
            color: {text_color};
            font-size: 24px;
            font-weight: bold;
        """)
        
        text_layout.addWidget(title_label)
        text_layout.addWidget(value_label)
        
        layout.addLayout(text_layout)
        layout.addStretch()
        
        card.setLayout(layout)
        card.setMinimumHeight(100)
        
        return card
    
    def create_modern_slot(self, slot_name, license_value):
        """Create a modern parking slot widget with gradient and animations"""
        slot_widget = QWidget()
        slot_widget.setObjectName("parkingSlot")
        slot_widget.setFixedSize(160, 120)
        
        slot_layout = QVBoxLayout()
        slot_layout.setContentsMargins(12, 12, 12, 12)
        slot_layout.setSpacing(8)
        
        # Header: Icon + Slot name
        header = QHBoxLayout()
        header.setSpacing(6)
        
        icon_label = QLabel()
        car_icon = qta.icon('fa5s.car', color='white')
        icon_label.setPixmap(car_icon.pixmap(QSize(20, 20)))
        icon_label.setObjectName("slotIcon")
        
        name_label = QLabel(slot_name)
        name_label.setObjectName("slotName")
        name_label.setStyleSheet("""
            color: white;
            font-size: 16px;
            font-weight: bold;
        """)
        
        header.addWidget(icon_label)
        header.addWidget(name_label)
        header.addStretch()
        
        # License plate
        license_label = QLabel(license_value or "Available")
        license_label.setObjectName("licensePlate")
        license_label.setAlignment(Qt.AlignCenter)
        license_label.setWordWrap(True)
        
        slot_layout.addLayout(header)
        slot_layout.addWidget(license_label)
        slot_widget.setLayout(slot_layout)
        
        self.update_modern_slot_color(slot_widget, license_value, False)
        
        return slot_widget

    def update_modern_slot_color(self, widget, text, is_duplicate=False):
        """Update slot color with gradient and animation"""
        icon_label = widget.findChild(QLabel, "slotIcon")
        license_label = widget.findChild(QLabel, "licensePlate")
        
        if is_duplicate:
            # Warning style (yellow/orange) for duplicate
            widget.setStyleSheet("""
                #parkingSlot {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #FFA726, stop:1 #FB8C00);
                    border-radius: 12px;
                    border: 3px solid #E65100;
                }
            """)
            if icon_label:
                icon_label.setPixmap(qta.icon('fa5s.exclamation-triangle', color='white').pixmap(QSize(20, 20)))
            if license_label:
                license_label.setStyleSheet("""
                    color: white;
                    font-size: 13px;
                    background: rgba(0,0,0,0.4);
                    border-radius: 6px;
                    padding: 8px;
                    font-weight: bold;
                """)
        elif text:
            # Occupied (red)
            widget.setStyleSheet("""
                #parkingSlot {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #EF5350, stop:1 #E53935);
                    border-radius: 12px;
                    border: 2px solid #C62828;
                }
            """)
            if icon_label:
                icon_label.setPixmap(qta.icon('fa5s.car', color='white').pixmap(QSize(20, 20)))
            if license_label:
                license_label.setStyleSheet("""
                    color: white;
                    font-size: 14px;
                    background: rgba(0,0,0,0.3);
                    border-radius: 6px;
                    padding: 10px;
                    font-weight: bold;
                """)
        else:
            # Available (green)
            widget.setStyleSheet("""
                #parkingSlot {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #66BB6A, stop:1 #43A047);
                    border-radius: 12px;
                    border: 2px solid #2E7D32;
                }
            """)
            if icon_label:
                icon_label.setPixmap(qta.icon('fa5s.check-circle', color='white').pixmap(QSize(20, 20)))
            if license_label:
                license_label.setStyleSheet("""
                    color: rgba(255,255,255,0.7);
                    font-size: 13px;
                    font-style: italic;
                """)
        
        # Smooth fade animation
        animation = QPropertyAnimation(widget, b"windowOpacity")
        animation.setDuration(300)
        animation.setStartValue(0.7)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.OutCubic)
        animation.start()

    def fetch_and_update_data(self):
        """Fetch data from API and update slots + stats + check duplicates"""
        api_url = f"{self.cloud_server_url}parking_slots/get_parking_slots"
        
        try:
            # Call API with parking_id
            data = {"parking_id": self.parking_id}
            response = requests.post(api_url, json=data)
            
            if response.status_code != 200:
                return
            
            data = response.json()["data"]
            occupied_list = data['occupied_list']
            occupied_license_list = data['occupied_license_list']
            occupied_data = dict(zip(occupied_list, occupied_license_list))
            
            # ========== CHECK FOR DUPLICATE LICENSE PLATES ==========
            license_counts = {}
            for license_plate in occupied_license_list:
                if license_plate:  # Skip empty
                    license_counts[license_plate] = license_counts.get(license_plate, 0) + 1
            
            # Find duplicates (license appearing in multiple slots)
            duplicates = {lic: count for lic, count in license_counts.items() if count > 1}
            self.duplicate_licenses = duplicates
            
            # Show/hide warning banner
            if duplicates:
                duplicate_list = ", ".join([f"{lic} ({count} slots)" for lic, count in duplicates.items()])
                self.warning_text.setText(f"⚠️ DUPLICATE DETECTED: {duplicate_list}")
                self.warning_banner.show()
            else:
                self.warning_banner.hide()
            
            # ========== UPDATE SLOTS ==========
            for slot_name, widget in self.slots.items():
                license_value = occupied_data.get(slot_name, "")
                license_label = widget.findChild(QLabel, "licensePlate")
                
                if license_label:
                    license_label.setText(str(license_value) if license_value else "Available")
                
                # Check if this slot has duplicate license
                is_duplicate = license_value in duplicates if license_value else False
                self.update_modern_slot_color(widget, license_value, is_duplicate)
            
            # ========== UPDATE STATS ==========
            total = len(self.slot_names)
            occupied = len(occupied_list)
            available = total - occupied
            occupancy_rate = int((occupied / total) * 100) if total > 0 else 0
            
            # Update stat cards
            self.update_stat_value(self.occupied_card, str(occupied))
            self.update_stat_value(self.available_card, str(available))
            self.update_stat_value(self.occupancy_card, f"{occupancy_rate}%")
            
        except Exception as e:
            print(f"Error fetching data: {e}")
    
    def update_stat_value(self, card, new_value):
        """Update stat card value with animation"""
        value_label = card.findChild(QLabel, "valueLabel")
        if value_label:
            value_label.setText(new_value)
    
    def apply_theme_style(self, is_dark):
        """Apply theme-specific colors to stats and slots"""
        self.is_dark_theme = is_dark
        
        if is_dark:
            # Dark mode - vibrant colors on dark background
            stat_colors = [
                ("#1E3A5F", "#64B5F6"),  # Blue
                ("#4A1C1C", "#EF5350"),  # Red
                ("#1B5E20", "#66BB6A"),  # Green
                ("#E65100", "#FFA726"),  # Orange
            ]
        else:
            # Light mode - pastel colors
            stat_colors = [
                ("#E3F2FD", "#1976D2"),  # Light Blue
                ("#FFEBEE", "#C62828"),  # Light Red
                ("#E8F5E9", "#2E7D32"),  # Light Green
                ("#FFF3E0", "#E65100"),  # Light Orange
            ]
        
        # Update stat cards
        stats = [self.total_slots_card, self.occupied_card, self.available_card, self.occupancy_card]
        icons = ['fa5s.car', 'fa5s.parking', 'fa5s.check-circle', 'fa5s.chart-pie']
        
        for i, (card, (bg, text_color), icon_name) in enumerate(zip(stats, stat_colors, icons)):
            card.setStyleSheet(f"""
                #statCard {{
                    background-color: {bg};
                    border-radius: 12px;
                    border-left: 4px solid {text_color};
                    padding: 16px;
                }}
            """)
            
            # Update text colors
            title_label = card.findChildren(QLabel)[1]  # Title
            value_label = card.findChild(QLabel, "valueLabel")
            
            title_label.setStyleSheet(f"color: {text_color}; font-size: 12px; font-weight: 600;")
            if value_label:
                value_label.setStyleSheet(f"color: {text_color}; font-size: 24px; font-weight: bold;")
        
        # Re-render all slots with current data
        for slot_name, widget in self.slots.items():
            license_label = widget.findChild(QLabel, "licensePlate")
            if license_label:
                license_value = license_label.text()
                if license_value == "Available":
                    license_value = ""
                is_duplicate = license_value in self.duplicate_licenses if license_value else False
                self.update_modern_slot_color(widget, license_value, is_duplicate)
