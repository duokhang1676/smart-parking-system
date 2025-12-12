"""
Theme Colors Configuration
Central storage for all color values used throughout the application
"""

class AppColors:
    """Centralized color palette for the entire application"""
    
    # Primary Gradient Colors (Navigation Bar)
    GRADIENT_START = "#0D47A1"
    GRADIENT_END = "#42A5F5"
    
    # Hover Gradient (Lighter version)
    GRADIENT_HOVER_START = "#7bf7e7"
    GRADIENT_HOVER_END = "#5d9dc2"
    
    # Primary Colors
    PRIMARY_PURPLE = "#667eea"
    PRIMARY_PURPLE_DARK = "#764ba2"
    
    # Accent Colors
    ACCENT_LIGHT_PURPLE = "#CE93D8"
    ACCENT_DARK_PURPLE = "#7B1FA2"
    
    # Background Colors
    BG_WHITE = "#FFFFFF"
    BG_LIGHT = "#F5F6FA"
    BG_DARK = "#2C393F"
    BG_DARK_HEADER = "#37474F"
    BG_LIGHT_GRAY = "#F5F5F5"
    BG_HOVER_LIGHT = "#ECF0F1"
    
    # Text Colors
    TEXT_BLACK = "#000000"
    TEXT_WHITE = "#FFFFFF"
    TEXT_DARK = "#2C3E50"
    TEXT_GRAY = "#7F8C8D"
    TEXT_SECONDARY = "#34495E"
    
    # Border Colors
    BORDER_LIGHT = "#CCCCCC"
    BORDER_MEDIUM = "#E0E0E0"
    BORDER_DARK = "#546E7A"
    BORDER_GRID_LIGHT = "#E0E0E0"
    BORDER_GRID_DARK = "#455A64"
    
    # Search Controls (Always White/Black)
    SEARCH_BG = "#FFFFFF"
    SEARCH_TEXT = "#000000"
    SEARCH_BORDER = "#CCCCCC"
    SEARCH_FOCUS = "#9C27B0"
    
    # Transparent/Overlay Colors
    TRANSPARENT = "transparent"
    WHITE_OVERLAY_10 = "rgba(255, 255, 255, 0.1)"
    WHITE_OVERLAY_15 = "rgba(255, 255, 255, 0.15)"
    WHITE_OVERLAY_20 = "rgba(255, 255, 255, 0.2)"
    WHITE_OVERLAY_30 = "rgba(255, 255, 255, 0.3)"
    WHITE_OVERLAY_50 = "rgba(255, 255, 255, 0.5)"
    WHITE_OVERLAY_60 = "rgba(255, 255, 255, 0.6)"
    WHITE_OVERLAY_70 = "rgba(255, 255, 255, 0.7)"
    
    @staticmethod
    def get_gradient_style():
        """Return CSS gradient string for primary gradient"""
        return f"""qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {AppColors.GRADIENT_START}, stop:1 {AppColors.GRADIENT_END})"""
    
    @staticmethod
    def get_hover_gradient_style():
        """Return CSS gradient string for hover state"""
        return f"""qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {AppColors.GRADIENT_HOVER_START}, stop:1 {AppColors.GRADIENT_HOVER_END})"""
    
    @staticmethod
    def get_button_style():
        """Return complete button stylesheet with gradient"""
        return f"""
            QPushButton {{
                background: {AppColors.get_gradient_style()};
                color: {AppColors.TEXT_WHITE};
                border: none;
                border-radius: 6px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {AppColors.get_hover_gradient_style()};
            }}
        """
    
    @staticmethod
    def get_search_control_style():
        """Return stylesheet for search controls (always white/black)"""
        return f"""
            QLineEdit, QDateEdit {{
                padding: 8px;
                font-size: 14px;
                background-color: {AppColors.SEARCH_BG};
                color: {AppColors.SEARCH_TEXT};
                border: 2px solid {AppColors.SEARCH_BORDER};
                border-radius: 6px;
            }}
            QLineEdit:focus, QDateEdit:focus {{
                border-color: {AppColors.SEARCH_FOCUS};
            }}
        """
