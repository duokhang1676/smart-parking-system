from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QGridLayout, QFrame, QScrollArea, QLineEdit,
                             QPushButton, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap
import qtawesome as qta
from modules.theme_colors import AppColors
from database.db_manager import get_parking_id, get_cloud_server_url
import os


class ParkingInfoPage(QWidget):
    def __init__(self):
        super().__init__()
        
        # Theme state
        self.is_dark_theme = True
        
        # Lấy thông tin từ config
        self.parking_id = get_parking_id()
        self.cloud_server_url = get_cloud_server_url()
        
        self.init_ui()
    
    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setSpacing(20)
        
        # ========== HEADER SECTION ==========
        header_frame = QFrame()
        header_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 12px;
                padding: 20px;
            }}
        """)
        
        header_layout = QHBoxLayout()
        
        # Icon
        icon_label = QLabel()
        icon_label.setPixmap(qta.icon('fa5s.parking', color='white').pixmap(80, 80))
        header_layout.addWidget(icon_label)
        
        # Title
        title_layout = QVBoxLayout()
        title_layout.setSpacing(8)
        
        title = QLabel("Parking Information")
        title.setStyleSheet("""
            color: white;
            font-size: 28px;
            font-weight: bold;
        """)
        
        subtitle = QLabel("System Configuration & Details")
        subtitle.setStyleSheet("""
            color: rgba(255, 255, 255, 0.8);
            font-size: 14px;
        """)
        
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        title_layout.addStretch()
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        header_frame.setLayout(header_layout)
        content_layout.addWidget(header_frame)
        
        # ========== STATS OVERVIEW ==========
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)
        
        self.total_capacity_card = self.create_info_card(
            "Total Capacity", 
            "15 Slots", 
            qta.icon('fa5s.car', color='#2196F3'),
            "#E3F2FD", 
            "#2196F3"
        )
        
        self.parking_areas_card = self.create_info_card(
            "Parking Areas", 
            "3 Zones", 
            qta.icon('fa5s.map-marked-alt', color='#4CAF50'),
            "#E8F5E9", 
            "#4CAF50"
        )
        
        self.status_card = self.create_info_card(
            "System Status", 
            "🟢 Online", 
            qta.icon('fa5s.server', color='#00BCD4'),
            "#E0F7FA", 
            "#00BCD4"
        )
        
        stats_layout.addWidget(self.total_capacity_card)
        stats_layout.addWidget(self.parking_areas_card)
        stats_layout.addWidget(self.status_card)
        
        content_layout.addLayout(stats_layout)
        
        # ========== PARKING DETAILS ==========
        details_frame = QFrame()
        details_frame.setObjectName("detailsFrame")
        details_frame.setStyleSheet(f"""
            #detailsFrame {{
                background-color: white;
                border-radius: 12px;
                border: 1px solid #E0E0E0;
                padding: 20px;
            }}
        """)
        
        details_layout = QVBoxLayout()
        
        # Section title
        section_title = QLabel("📋 Parking Details")
        section_title.setStyleSheet("""
            color: #333;
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 10px;
        """)
        details_layout.addWidget(section_title)
        
        # Grid layout for info
        grid = QGridLayout()
        grid.setSpacing(15)
        grid.setColumnStretch(1, 1)
        
        # Info rows
        row = 0
        
        # Parking ID
        grid.addWidget(self.create_label_bold("Parking ID:"), row, 0)
        self.parking_id_value = self.create_label_value(self.parking_id)
        grid.addWidget(self.parking_id_value, row, 1)
        row += 1
        
        # Server URL
        grid.addWidget(self.create_label_bold("Cloud Server URL:"), row, 0)
        self.server_url_value = self.create_label_value(self.cloud_server_url)
        grid.addWidget(self.server_url_value, row, 1)
        row += 1
        
        # Total Slots
        grid.addWidget(self.create_label_bold("Total Parking Slots:"), row, 0)
        self.total_slots_value = self.create_label_value("15 slots")
        grid.addWidget(self.total_slots_value, row, 1)
        row += 1
        
        # Slot Configuration
        grid.addWidget(self.create_label_bold("Slot Configuration:"), row, 0)
        self.slot_config_value = self.create_label_value("3 zones (A, B, C) × 5 levels (0-4)")
        grid.addWidget(self.slot_config_value, row, 1)
        row += 1
        
        # Zone A
        grid.addWidget(self.create_label_bold("Zone A:"), row, 0)
        grid.addWidget(self.create_label_value("A0, A1, A2, A3, A4 (5 slots)"), row, 1)
        row += 1
        
        # Zone B
        grid.addWidget(self.create_label_bold("Zone B:"), row, 0)
        grid.addWidget(self.create_label_value("B0, B1, B2, B3, B4 (5 slots)"), row, 1)
        row += 1
        
        # Zone C
        grid.addWidget(self.create_label_bold("Zone C:"), row, 0)
        grid.addWidget(self.create_label_value("C0, C1, C2, C3, C4 (5 slots)"), row, 1)
        row += 1
        
        # Operating Hours
        grid.addWidget(self.create_label_bold("Operating Hours:"), row, 0)
        grid.addWidget(self.create_label_value("24/7 - Always Open"), row, 1)
        row += 1
        
        # Database
        grid.addWidget(self.create_label_bold("Database:"), row, 0)
        grid.addWidget(self.create_label_value("MongoDB (server_local)"), row, 1)
        row += 1
        
        details_layout.addLayout(grid)
        details_frame.setLayout(details_layout)
        content_layout.addWidget(details_frame)
        
        # ========== SYSTEM FEATURES ==========
        features_frame = QFrame()
        features_frame.setObjectName("featuresFrame")
        features_frame.setStyleSheet(f"""
            #featuresFrame {{
                background-color: white;
                border-radius: 12px;
                border: 1px solid #E0E0E0;
                padding: 20px;
            }}
        """)
        
        features_layout = QVBoxLayout()
        
        features_title = QLabel("⚡ System Features")
        features_title.setStyleSheet("""
            color: #333;
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 10px;
        """)
        features_layout.addWidget(features_title)
        
        # Features grid
        features_grid = QGridLayout()
        features_grid.setSpacing(15)
        
        features = [
            ("✅", "Real-time slot monitoring", "Monitor parking space availability in real-time"),
            ("✅", "License plate recognition", "Automatic vehicle identification system"),
            ("✅", "Duplicate detection", "Alert system for duplicate license plates"),
            ("✅", "Customer management", "Complete customer database with history"),
            ("✅", "Bill generation", "Automated billing and payment tracking"),
            ("✅", "Historical records", "Complete parking history with search functionality"),
        ]
        
        for i, (icon, title, desc) in enumerate(features):
            feature_widget = self.create_feature_item(icon, title, desc)
            features_grid.addWidget(feature_widget, i // 2, i % 2)
        
        features_layout.addLayout(features_grid)
        features_frame.setLayout(features_layout)
        content_layout.addWidget(features_frame)
        
        # ========== TECHNICAL INFO ==========
        tech_frame = QFrame()
        tech_frame.setObjectName("techFrame")
        tech_frame.setStyleSheet(f"""
            #techFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f093fb, stop:1 #f5576c);
                border-radius: 12px;
                padding: 20px;
            }}
        """)
        
        tech_layout = QVBoxLayout()
        
        tech_title = QLabel("🔧 Technical Information")
        tech_title.setStyleSheet("""
            color: white;
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 10px;
        """)
        tech_layout.addWidget(tech_title)
        
        tech_grid = QGridLayout()
        tech_grid.setSpacing(10)
        
        tech_info = [
            ("Framework:", "PyQt5 (Desktop Application)"),
            ("Detection Model:", "YOLOv8 (Car & License Plate)"),
            ("Database:", "MongoDB"),
            ("API Communication:", "REST API"),
            ("Update Interval:", "10 seconds (auto-refresh)"),
        ]
        
        for i, (label, value) in enumerate(tech_info):
            label_widget = QLabel(label)
            label_widget.setStyleSheet("""
                color: white;
                font-size: 13px;
                font-weight: bold;
            """)
            
            value_widget = QLabel(value)
            value_widget.setStyleSheet("""
                color: rgba(255, 255, 255, 0.9);
                font-size: 13px;
            """)
            
            tech_grid.addWidget(label_widget, i, 0)
            tech_grid.addWidget(value_widget, i, 1)
        
        tech_layout.addLayout(tech_grid)
        tech_frame.setLayout(tech_layout)
        content_layout.addWidget(tech_frame)
        
        content_layout.addStretch()
        content_widget.setLayout(content_layout)
        scroll.setWidget(content_widget)
        
        main_layout.addWidget(scroll)
        self.setLayout(main_layout)
    
    def create_info_card(self, title, value, icon, bg_color, text_color):
        """Create info card similar to page1 stat cards"""
        card = QFrame()
        card.setObjectName("infoCard")
        card.setStyleSheet(f"""
            #infoCard {{
                background-color: {bg_color};
                border-radius: 12px;
                border-left: 4px solid {text_color};
                padding: 20px;
            }}
        """)
        
        layout = QHBoxLayout()
        layout.setSpacing(15)
        
        # Icon
        icon_label = QLabel()
        icon_label.setPixmap(icon.pixmap(48, 48))
        layout.addWidget(icon_label)
        
        # Text
        text_layout = QVBoxLayout()
        text_layout.setSpacing(5)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            color: {text_color};
            font-size: 13px;
            font-weight: 600;
        """)
        
        value_label = QLabel(value)
        value_label.setStyleSheet(f"""
            color: {text_color};
            font-size: 22px;
            font-weight: bold;
        """)
        
        text_layout.addWidget(title_label)
        text_layout.addWidget(value_label)
        
        layout.addLayout(text_layout)
        layout.addStretch()
        
        card.setLayout(layout)
        card.setMinimumHeight(110)
        
        return card
    
    def create_label_bold(self, text):
        """Create bold label for grid"""
        label = QLabel(text)
        label.setStyleSheet("""
            color: #555;
            font-size: 14px;
            font-weight: bold;
        """)
        return label
    
    def create_label_value(self, text):
        """Create value label for grid"""
        label = QLabel(text)
        label.setStyleSheet("""
            color: #333;
            font-size: 14px;
        """)
        label.setWordWrap(True)
        return label
    
    def create_feature_item(self, icon, title, description):
        """Create feature item widget"""
        widget = QFrame()
        widget.setStyleSheet("""
            QFrame {
                background-color: #F8F9FA;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        
        layout = QHBoxLayout()
        layout.setSpacing(12)
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("""
            font-size: 24px;
        """)
        layout.addWidget(icon_label)
        
        # Text
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            color: #333;
            font-size: 14px;
            font-weight: bold;
        """)
        
        desc_label = QLabel(description)
        desc_label.setStyleSheet("""
            color: #666;
            font-size: 12px;
        """)
        desc_label.setWordWrap(True)
        
        text_layout.addWidget(title_label)
        text_layout.addWidget(desc_label)
        
        layout.addLayout(text_layout)
        widget.setLayout(layout)
        
        return widget
    
    def apply_theme_style(self, is_dark):
        """Apply theme styling"""
        self.is_dark_theme = is_dark
        
        # Update based on theme if needed
        # For now, this page uses fixed light colors for better readability
        pass
