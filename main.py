import PyQt5
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QWidget, QStackedWidget, QFrame)
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QIcon, QFont

# Try import qt_material, fallback if not available
try:
    from qt_material import apply_stylesheet
    HAS_QT_MATERIAL = True
except ImportError:
    HAS_QT_MATERIAL = False
    print("⚠️ qt_material not installed. Running with basic theme.")
    print("Install with: pip install qt-material QtAwesome")

import qtawesome as qta
from app.modules.page1 import ParkingSlotPage 
from app.modules.page2 import HistoryPage
from app.modules.page3 import CarsInParkingPage
from app.modules.page4 import CustomersPage
from app.modules.page5 import CoordinatesSetup
from app.modules.page6 import ParkingInfoPage
from app.modules.page7 import EnvironmentPage
from app.modules.page8 import VehicleSearchPage
from app.modules.theme_colors import AppColors

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🅿️ Smart Parking Management System")
        self.setGeometry(80, 50, 1450, 900)
        self.setMinimumSize(1200, 700)

        # Root container
        root_widget = QWidget()
        root_layout = QHBoxLayout(root_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ========== SIDEBAR NAVIGATION ==========
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setStyleSheet(f"""
            QFrame#sidebar {{
                background: {AppColors.get_gradient_style()};
                border-right: 2px solid {AppColors.WHITE_OVERLAY_10};
            }}
        """)
        sidebar.setFixedWidth(300)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(20, 30, 20, 20)
        sidebar_layout.setSpacing(15)
        0 
        # Logo/Brand
        brand_layout = QVBoxLayout()
        brand_layout.setSpacing(8)
        
        logo_label = QLabel("🅿️")
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setStyleSheet(f"""
            font-size: 48px;
            background: {AppColors.WHITE_OVERLAY_20};
            border-radius: 50%;
            padding: 15px;
            margin-bottom: 10px;
            border: 3px solid {AppColors.WHITE_OVERLAY_30};
        """)
        
        brand_title = QLabel("Smart Parking")
        brand_title.setAlignment(Qt.AlignCenter)
        brand_title.setStyleSheet(f"""
            color: {AppColors.TEXT_WHITE};
            font-size: 22px;
            font-weight: bold;
            letter-spacing: 1px;
        """)
        
        brand_subtitle = QLabel("Management System")
        brand_subtitle.setAlignment(Qt.AlignCenter)
        brand_subtitle.setStyleSheet(f"""
            color: {AppColors.WHITE_OVERLAY_70};
            font-size: 12px;
            letter-spacing: 0.5px;
        """)
        
        brand_layout.addWidget(logo_label)
        brand_layout.addWidget(brand_title)
        brand_layout.addWidget(brand_subtitle)
        sidebar_layout.addLayout(brand_layout)
        
        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet(f"""
            background: {AppColors.WHITE_OVERLAY_20};
            border: none;
            height: 1px;
            margin: 20px 0;
        """)
        sidebar_layout.addWidget(divider)

        def create_sidebar_button(text, icon_name, description=""):
            """Create modern sidebar button"""
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(15, 12, 15, 12)
            btn_layout.setSpacing(12)
            
            # Icon
            icon_label = QLabel()
            icon_label.setPixmap(qta.icon(icon_name, color='white').pixmap(24, 24))
            
            # Text
            text_layout = QVBoxLayout()
            text_layout.setSpacing(2)
            
            title = QLabel(text)
            title.setStyleSheet(f"""
                color: {AppColors.TEXT_WHITE};
                font-size: 15px;
                font-weight: 600;
            """)
            
            if description:
                desc = QLabel(description)
                desc.setStyleSheet(f"""
                    color: {AppColors.WHITE_OVERLAY_60};
                    font-size: 11px;
                """)
                text_layout.addWidget(title)
                text_layout.addWidget(desc)
            else:
                text_layout.addWidget(title)
            
            btn_layout.addWidget(icon_label)
            btn_layout.addLayout(text_layout)
            btn_layout.addStretch()
            
            btn_widget.setStyleSheet(f"""
                QWidget {{
                    background: {AppColors.TRANSPARENT};
                    border-radius: 10px;
                    border: none;
                }}
                QWidget:hover {{
                    background: {AppColors.WHITE_OVERLAY_15};
                    border: 1px solid {AppColors.WHITE_OVERLAY_30};
                }}
            """)
            btn_widget.setCursor(Qt.PointingHandCursor)
            btn_widget.setFixedHeight(70)
            btn_widget.setMinimumWidth(250)
            
            return btn_widget

        # Navigation Section
        nav_label = QLabel("NAVIGATION")
        nav_label.setStyleSheet(f"""
            color: {AppColors.WHITE_OVERLAY_50};
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 1px;
            padding: 10px 0 5px 5px;
        """)
        sidebar_layout.addWidget(nav_label)
        
        self.btn_page1 = create_sidebar_button("Dashboard", "fa5s.home", "Parking overview")
        self.btn_page2 = create_sidebar_button("History", "fa5s.history", "Past records")
        self.btn_page3 = create_sidebar_button("Active Cars", "fa5s.parking", "Currently parked")
        self.btn_page4 = create_sidebar_button("Customers", "fa5s.users", "Registered users")
        self.btn_page5 = create_sidebar_button("Settings", "fa5s.cog", "Configuration")
        self.btn_page7 = create_sidebar_button("Environment", "fa5s.leaf", "Air quality")
        self.btn_page8 = create_sidebar_button("Vehicle Search", "fa5s.search", "Search images")

        sidebar_layout.addWidget(self.btn_page1)
        sidebar_layout.addWidget(self.btn_page2)
        sidebar_layout.addWidget(self.btn_page3)
        sidebar_layout.addWidget(self.btn_page4)
        sidebar_layout.addWidget(self.btn_page5)
        sidebar_layout.addWidget(self.btn_page7)
        sidebar_layout.addWidget(self.btn_page8)
        sidebar_layout.addStretch()
        
        # Bottom Section - Theme Toggle
        bottom_section = QVBoxLayout()
        bottom_section.setSpacing(10)
        
        theme_section = QLabel("APPEARANCE")
        theme_section.setStyleSheet(f"""
            color: {AppColors.WHITE_OVERLAY_50};
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 1px;
            padding: 5px 0 5px 5px;
        """)
        bottom_section.addWidget(theme_section)
        
        self.theme_toggle_btn = QPushButton("🌙 Dark Mode")
        self.theme_toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background: {AppColors.WHITE_OVERLAY_10};
                color: {AppColors.TEXT_WHITE};
                padding: 12px 15px;
                border: 1px solid {AppColors.WHITE_OVERLAY_20};
                border-radius: 8px;
                text-align: left;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background: {AppColors.WHITE_OVERLAY_15};
            }}
        """)
        self.theme_toggle_btn.clicked.connect(self.toggle_theme)
        bottom_section.addWidget(self.theme_toggle_btn)
        
        sidebar_layout.addLayout(bottom_section)
        root_layout.addWidget(sidebar)

        # ========== MAIN CONTENT CONTAINER ==========
        main_container = QWidget()
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Top Bar with Page Title
        top_bar = QFrame()
        top_bar.setObjectName("topBar")
        top_bar.setStyleSheet(f"""
            QFrame#topBar {{
                background: {AppColors.BG_WHITE};
                border-bottom: 1px solid {AppColors.BORDER_MEDIUM};
            }}
        """)
        top_bar.setFixedHeight(100)
        
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(30, 15, 30, 15)
        
        # Page Title
        self.page_title = QLabel("Dashboard")
        self.page_title.setStyleSheet(f"""
            color: {AppColors.TEXT_DARK};
            font-size: 24px;
            font-weight: bold;
        """)
        
        # Breadcrumb
        self.breadcrumb = QLabel("Home / Dashboard")
        self.breadcrumb.setStyleSheet(f"""
            color: {AppColors.TEXT_GRAY};
            font-size: 13px;
        """)
        
        title_layout = QVBoxLayout()
        title_layout.setSpacing(5)
        title_layout.addWidget(self.page_title)
        title_layout.addWidget(self.breadcrumb)
        
        top_bar_layout.addLayout(title_layout)
        top_bar_layout.addStretch()
        
        # Admin Button (clickable)
        self.admin_btn = QPushButton("👤 Admin")
        self.admin_btn.setStyleSheet(f"""
            QPushButton {{
                color: {AppColors.TEXT_SECONDARY};
                font-size: 14px;
                font-weight: 500;
                background: {AppColors.BG_HOVER_LIGHT};
                padding: 8px 15px;
                border-radius: 20px;
                border: none;
            }}
            QPushButton:hover {{
                background: #D1C4E9;
                color: #5E35B1;
            }}
        """)
        self.admin_btn.setCursor(Qt.PointingHandCursor)
        self.admin_btn.clicked.connect(lambda: self.navigate_to(self.page6, "Parking Information", "Admin / Parking Info"))
        top_bar_layout.addWidget(self.admin_btn)
        
        main_layout.addWidget(top_bar)
        
        # Content Area with Wrapper
        content_wrapper = QWidget()
        content_wrapper_layout = QVBoxLayout(content_wrapper)
        content_wrapper_layout.setContentsMargins(30, 25, 30, 25)
        
        self.content_area = QStackedWidget()
        self.content_area.setStyleSheet(f"""
            QStackedWidget {{
                background: {AppColors.BG_LIGHT};
                border-radius: 12px;
            }}
        """)
        content_wrapper_layout.addWidget(self.content_area)
        
        main_layout.addWidget(content_wrapper)
        root_layout.addWidget(main_container)

        # Initialize Pages
        self.page1 = ParkingSlotPage()
        self.page2 = HistoryPage()
        self.page3 = CarsInParkingPage()
        self.page4 = CustomersPage()
        self.page5 = CoordinatesSetup()
        self.page6 = ParkingInfoPage()
        self.page7 = EnvironmentPage()
        self.page8 = VehicleSearchPage()

        self.content_area.addWidget(self.page1)
        self.content_area.addWidget(self.page2)
        self.content_area.addWidget(self.page3)
        self.content_area.addWidget(self.page4)
        self.content_area.addWidget(self.page5)
        self.content_area.addWidget(self.page6)
        self.content_area.addWidget(self.page7)
        self.content_area.addWidget(self.page8)

        # Connect Navigation Buttons
        self.btn_page1.mousePressEvent = lambda e: self.navigate_to(self.page1, "Dashboard", "Home / Dashboard")
        self.btn_page2.mousePressEvent = lambda e: self.navigate_to(self.page2, "History", "Home / History")
        self.btn_page3.mousePressEvent = lambda e: self.navigate_to(self.page3, "Active Cars", "Home / Active Cars")
        self.btn_page4.mousePressEvent = lambda e: self.navigate_to(self.page4, "Customers", "Home / Customers")
        self.btn_page5.mousePressEvent = lambda e: self.navigate_to(self.page5, "Settings", "Home / Settings")
        self.btn_page7.mousePressEvent = lambda e: self.navigate_to(self.page7, "Environment", "Home / Environment")
        self.btn_page8.mousePressEvent = lambda e: self.navigate_to(self.page8, "Vehicle Search", "Home / Vehicle Search")

        self.setCentralWidget(root_widget)
        
        # Load saved theme preference and apply initial styles
        settings = QSettings('SmartParking', 'ThemeConfig')
        is_dark = 'dark' in settings.value('theme', 'dark_teal.xml')
        self.apply_initial_styles(is_dark)
        self.update_theme_icon()
    
    def navigate_to(self, page, title, breadcrumb):
        """Navigate to a page and update header"""
        self.content_area.setCurrentWidget(page)
        self.page_title.setText(title)
        self.breadcrumb.setText(breadcrumb)
    
    def apply_initial_styles(self, is_dark):
        """Apply theme styles to all pages on startup"""
        # Apply to Page 2, 3, 4, 6, 7, 8 tables
        for page in [self.page2, self.page3, self.page4, self.page6, self.page7, self.page8]:
            if hasattr(page, 'apply_theme_style'):
                page.apply_theme_style(is_dark)
        
        # Apply to Page 1 slots
        if hasattr(self.page1, 'apply_theme_style'):
            self.page1.apply_theme_style(is_dark)
    
    def toggle_theme(self):
        """Toggle between dark and light mode"""
        settings = QSettings('SmartParking', 'ThemeConfig')
        current_theme = settings.value('theme', 'light_teal.xml')
        
        # Switch theme
        if 'dark' in current_theme:
            new_theme = 'light_teal.xml'
        else:
            new_theme = 'dark_teal.xml'
        
        # Save preference
        settings.setValue('theme', new_theme)
        
        # Apply new theme
        try:
            if HAS_QT_MATERIAL:
                apply_stylesheet(QApplication.instance(), theme=new_theme, extra={
                    'density_scale': '0',
                    'font_family': 'Segoe UI',
                    'font_size': '10px',
                })
        except Exception as e:
            print(f"Theme switch error: {e}")
        
        # Update icon
        self.update_theme_icon()
        
        # Refresh all pages styling
        self.refresh_page_styles()
    
    def update_theme_icon(self):
        """Update toggle button text based on current theme"""
        settings = QSettings('SmartParking', 'ThemeConfig')
        current_theme = settings.value('theme', 'dark_teal.xml')
        
        if 'dark' in current_theme:
            self.theme_toggle_btn.setText("🌙 Dark Mode")
            self.theme_toggle_btn.setToolTip("Switch to Light Mode")
        else:
            self.theme_toggle_btn.setText("☀️ Light Mode")
            self.theme_toggle_btn.setToolTip("Switch to Dark Mode")
    
    def refresh_page_styles(self):
        """Refresh styling for all pages after theme change"""
        settings = QSettings('SmartParking', 'ThemeConfig')
        is_dark = 'dark' in settings.value('theme', 'dark_teal.xml')
        
        # Refresh Page 2, 3, 4, 6, 7, 8 table styles
        for page in [self.page2, self.page3, self.page4, self.page6, self.page7, self.page8]:
            if hasattr(page, 'apply_theme_style'):
                page.apply_theme_style(is_dark)
        
        # Refresh Page 1 slot styles
        if hasattr(self.page1, 'apply_theme_style'):
            self.page1.apply_theme_style(is_dark)


if __name__ == "__main__":
    import sys
    import os
    import warnings
    
    # Suppress qt_material warnings
    warnings.filterwarnings('ignore', category=UserWarning)
    
    app = QApplication(sys.argv)
    
    # ========== APPLY MATERIAL DESIGN THEME ==========
    # Suppress SVG warnings on Windows
    os.environ['QT_LOGGING_RULES'] = 'qt.svg.warning=false;qt.svg.info=false'
    
    if HAS_QT_MATERIAL:
        # Load saved theme preference (default: dark_teal)
        settings = QSettings('SmartParking', 'ThemeConfig')
        theme_name = settings.value('theme', 'dark_teal.xml')
        
        try:
            apply_stylesheet(app, theme=theme_name, extra={
                'density_scale': '0',
                'font_family': 'Segoe UI',
                'font_size': '10px',
            })
        except Exception as e:
            print(f"Theme warning (non-critical): {e}")
    else:
        # Basic fallback styling without qt_material
        app.setStyle('Fusion')
        print("✅ Using Fusion style (built-in Qt theme)")
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
