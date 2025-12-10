from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QFrame, QPushButton, QMessageBox, QGridLayout)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import qtawesome as qta
import requests
from datetime import datetime
import paho.mqtt.client as mqtt

from database.db_manager import get_parking_id, get_cloud_server_url
from modules.theme_colors import AppColors


class EnvironmentPage(QWidget):
    def __init__(self):
        super().__init__()
        
        # Theme state
        self.is_dark_theme = True
        
        # Lấy thông tin từ config
        self.parking_id = get_parking_id()
        self.cloud_server_url = get_cloud_server_url()
        
        # Data storage
        self.env_data = None
        
        # MQTT Configuration
        self.mqtt_broker = "broker.hivemq.com"
        self.mqtt_port = 1883
        self.mqtt_topic_light = "parking/light"
        self.mqtt_topic_barrier_in = "parking/barrier/in"
        self.mqtt_topic_barrier_out = "parking/barrier/out"
        
        # State variables
        self.light_state = False  # False = off, True = on
        self.barrier_in_state = False  # False = closed, True = open
        self.barrier_out_state = False  # False = closed, True = open
        
        # Initialize MQTT client
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_mqtt_connect
        self.mqtt_client.on_publish = self.on_mqtt_publish
        
        try:
            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, 60)
            self.mqtt_client.loop_start()
        except Exception as e:
            print(f"[MQTT ERROR] Failed to connect: {e}")
        
        self.init_ui()
    
    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # ========== HEADER SECTION ==========
        header_frame = QFrame()
        header_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #11998e, stop:1 #38ef7d);
                border-radius: 12px;
                padding: 20px;
            }}
        """)
        
        header_layout = QHBoxLayout()
        
        # Icon
        icon_label = QLabel()
        icon_label.setPixmap(qta.icon('fa5s.leaf', color='white').pixmap(80, 80))
        header_layout.addWidget(icon_label)
        
        # Title
        title_layout = QVBoxLayout()
        title_layout.setSpacing(8)
        
        title = QLabel("Environment Monitoring")
        title.setStyleSheet("""
            color: white;
            font-size: 28px;
            font-weight: bold;
        """)
        
        subtitle = QLabel("Real-time environmental conditions")
        subtitle.setStyleSheet("""
            color: rgba(255, 255, 255, 0.9);
            font-size: 14px;
        """)
        
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        title_layout.addStretch()
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        header_frame.setLayout(header_layout)
        main_layout.addWidget(header_frame)
        
        # ========== ENVIRONMENT CARDS ==========
        cards_layout = QGridLayout()
        cards_layout.setSpacing(20)
        
        # Temperature Card
        self.temp_card = self.create_env_card(
            "Temperature",
            "--°C",
            qta.icon('fa5s.thermometer-half', color='#FF6B6B'),
            "#FFE5E5",
            "#FF6B6B"
        )
        cards_layout.addWidget(self.temp_card, 0, 0)
        
        # Humidity Card
        self.humidity_card = self.create_env_card(
            "Humidity",
            "--%",
            qta.icon('fa5s.tint', color='#4ECDC4'),
            "#E0F7F6",
            "#4ECDC4"
        )
        cards_layout.addWidget(self.humidity_card, 0, 1)
        
        # Light Card
        self.light_card = self.create_env_card(
            "Light Intensity",
            "-- lux",
            qta.icon('fa5s.sun', color='#FFD93D'),
            "#FFF9E5",
            "#FFD93D"
        )
        cards_layout.addWidget(self.light_card, 1, 0)
        
        # Status Card
        self.status_card = self.create_env_card(
            "System Status",
            "Waiting...",
            qta.icon('fa5s.info-circle', color='#95A5A6'),
            "#F0F0F0",
            "#95A5A6"
        )
        cards_layout.addWidget(self.status_card, 1, 1)
        
        main_layout.addLayout(cards_layout)
        
        # ========== DETAILS SECTION ==========
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
        section_title = QLabel("📊 Environmental Details")
        section_title.setStyleSheet("""
            color: #333;
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 10px;
        """)
        details_layout.addWidget(section_title)
        
        # Details grid
        self.details_grid = QGridLayout()
        self.details_grid.setSpacing(15)
        self.details_grid.setColumnStretch(1, 1)
        
        # Parking ID
        self.details_grid.addWidget(self.create_label_bold("Parking ID:"), 0, 0)
        self.parking_id_label = self.create_label_value(self.parking_id)
        self.details_grid.addWidget(self.parking_id_label, 0, 1)
        
        # Temperature Details
        self.details_grid.addWidget(self.create_label_bold("Temperature:"), 1, 0)
        self.temp_detail = self.create_label_value("--")
        self.details_grid.addWidget(self.temp_detail, 1, 1)
        
        # Humidity Details
        self.details_grid.addWidget(self.create_label_bold("Humidity:"), 2, 0)
        self.humidity_detail = self.create_label_value("--")
        self.details_grid.addWidget(self.humidity_detail, 2, 1)
        
        # Light Details
        self.details_grid.addWidget(self.create_label_bold("Light Intensity:"), 3, 0)
        self.light_detail = self.create_label_value("--")
        self.details_grid.addWidget(self.light_detail, 3, 1)
        
        # Last Update
        self.details_grid.addWidget(self.create_label_bold("Last Updated:"), 4, 0)
        self.last_update_label = self.create_label_value("Never")
        self.details_grid.addWidget(self.last_update_label, 4, 1)
        
        details_layout.addLayout(self.details_grid)
        details_frame.setLayout(details_layout)
        main_layout.addWidget(details_frame)
        
        # ========== CONTROL BUTTONS (ALL IN ONE ROW) ==========
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)
        
        # Refresh Button
        refresh_btn = QPushButton()
        refresh_btn.setText("🔄 Refresh")
        refresh_btn.setIcon(qta.icon('fa5s.sync-alt', color='white'))
        refresh_btn.clicked.connect(self.refresh_data)
        refresh_btn.setFixedWidth(180)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px 20px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7b91f7, stop:1 #8659b5);
            }
            QPushButton:pressed {
                background: #5E35B1;
            }
        """)
        buttons_layout.addWidget(refresh_btn)
        
        # Light Control Button
        self.light_btn = QPushButton()
        self.light_btn.setText("💡 Light ON")
        self.light_btn.setIcon(qta.icon('fa5s.lightbulb', color='white'))
        self.light_btn.clicked.connect(self.toggle_light)
        self.light_btn.setFixedWidth(180)
        buttons_layout.addWidget(self.light_btn)
        
        # Barrier IN Button
        self.barrier_in_btn = QPushButton()
        self.barrier_in_btn.setText("🚧 Barrier IN")
        self.barrier_in_btn.setIcon(qta.icon('fa5s.sign-in-alt', color='white'))
        self.barrier_in_btn.clicked.connect(self.toggle_barrier_in)
        self.barrier_in_btn.setFixedWidth(180)
        buttons_layout.addWidget(self.barrier_in_btn)
        
        # Barrier OUT Button
        self.barrier_out_btn = QPushButton()
        self.barrier_out_btn.setText("🚧 Barrier OUT")
        self.barrier_out_btn.setIcon(qta.icon('fa5s.sign-out-alt', color='white'))
        self.barrier_out_btn.clicked.connect(self.toggle_barrier_out)
        self.barrier_out_btn.setFixedWidth(180)
        buttons_layout.addWidget(self.barrier_out_btn)
        
        # Initialize button styles
        self.update_light_button_style()
        self.update_barrier_in_button_style()
        self.update_barrier_out_button_style()
        
        # Center all buttons
        button_container = QHBoxLayout()
        button_container.addStretch()
        button_container.addLayout(buttons_layout)
        button_container.addStretch()
        main_layout.addLayout(button_container)
        
        main_layout.addStretch()
        self.setLayout(main_layout)
    
    def create_env_card(self, title, value, icon, bg_color, text_color):
        """Create environment monitoring card"""
        card = QFrame()
        card.setObjectName("envCard")
        card.setStyleSheet(f"""
            #envCard {{
                background-color: {bg_color};
                border-radius: 15px;
                border-left: 5px solid {text_color};
                padding: 25px;
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Header with icon
        header_layout = QHBoxLayout()
        
        icon_label = QLabel()
        icon_label.setPixmap(icon.pixmap(50, 50))
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            color: {text_color};
            font-size: 14px;
            font-weight: 600;
        """)
        
        header_layout.addWidget(icon_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Value
        value_label = QLabel(value)
        value_label.setObjectName("valueLabel")
        value_label.setStyleSheet(f"""
            color: {text_color};
            font-size: 30px;
            font-weight: bold;
        """)
        
        layout.addLayout(header_layout)
        layout.addWidget(value_label)
        
        card.setLayout(layout)
        card.setMinimumHeight(150)
        
        return card
    
    def create_label_bold(self, text):
        """Create bold label"""
        label = QLabel(text)
        label.setStyleSheet("""
            color: #555;
            font-size: 14px;
            font-weight: bold;
        """)
        return label
    
    def create_label_value(self, text):
        """Create value label"""
        label = QLabel(text)
        label.setStyleSheet("""
            color: #333;
            font-size: 14px;
        """)
        label.setWordWrap(True)
        return label
    
    def refresh_data(self):
        """Fetch environment data from API"""
        try:
            # Gọi API
            api_url = f"{self.cloud_server_url}environments/get_environment"
            response = requests.post(api_url, json={"parking_id": self.parking_id}, timeout=10)
            
            if response.status_code != 200:
                QMessageBox.warning(self, "Warning", "Không thể lấy dữ liệu môi trường từ server")
                self.update_status("Error", "#E74C3C")
                return
            
            result = response.json()
            if result.get("status") != "success":
                QMessageBox.warning(self, "Warning", result.get("message", "Không tìm thấy dữ liệu"))
                self.update_status("Not Found", "#E67E22")
                return
            
            # Lấy dữ liệu
            self.env_data = result.get("data", {})
            
            # Cập nhật UI
            self.update_environment_display()
            self.update_status("Online", "#27AE60")
            
            # Cập nhật thời gian
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.last_update_label.setText(current_time)
            
        except requests.exceptions.Timeout:
            QMessageBox.critical(self, "Error", "Timeout khi kết nối tới server")
            self.update_status("Timeout", "#E74C3C")
        except requests.exceptions.ConnectionError:
            QMessageBox.critical(self, "Error", "Không thể kết nối tới server")
            self.update_status("Disconnected", "#E74C3C")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Lỗi: {str(e)}")
            self.update_status("Error", "#E74C3C")
    
    def update_environment_display(self):
        """Update UI with environment data"""
        if not self.env_data:
            return
        
        # Temperature
        temp = self.env_data.get("temperature", 0)
        temp_value_label = self.temp_card.findChild(QLabel, "valueLabel")
        if temp_value_label:
            temp_value_label.setText(f"{temp}°C")
        self.temp_detail.setText(f"{temp}°C - " + self.get_temp_status(temp))
        
        # Humidity
        humidity = self.env_data.get("humidity", 0)
        humidity_value_label = self.humidity_card.findChild(QLabel, "valueLabel")
        if humidity_value_label:
            humidity_value_label.setText(f"{humidity}%")
        self.humidity_detail.setText(f"{humidity}% - " + self.get_humidity_status(humidity))
        
        # Light
        light = self.env_data.get("light", 0)
        light_value_label = self.light_card.findChild(QLabel, "valueLabel")
        if light_value_label:
            light_value_label.setText(f"{light} lux")
        self.light_detail.setText(f"{light} lux - " + self.get_light_status(light))
    
    def update_status(self, status, color):
        """Update status card"""
        status_value_label = self.status_card.findChild(QLabel, "valueLabel")
        if status_value_label:
            status_value_label.setText(status)
            status_value_label.setStyleSheet(f"""
                color: {color};
                font-size: 30px;
                font-weight: bold;
            """)
    
    def get_temp_status(self, temp):
        """Get temperature status description"""
        if temp < 15:
            return "Cold"
        elif temp < 25:
            return "Comfortable"
        elif temp < 30:
            return "Warm"
        else:
            return "Hot"
    
    def get_humidity_status(self, humidity):
        """Get humidity status description"""
        if humidity < 30:
            return "Dry"
        elif humidity < 60:
            return "Comfortable"
        else:
            return "Humid"
    
    def get_light_status(self, light):
        """Get light status description"""
        if light < 100:
            return "Dark"
        elif light < 500:
            return "Dim"
        elif light < 1000:
            return "Normal"
        else:
            return "Bright"
    
    def apply_theme_style(self, is_dark):
        """Apply theme styling"""
        self.is_dark_theme = is_dark
        # Theme can be customized here if needed
    
    # ========== MQTT METHODS ==========
    def on_mqtt_connect(self, client, userdata, flags, rc):
        """Callback when MQTT connects"""
        if rc == 0:
            print(f"[MQTT CONNECTED] Successfully connected to broker {self.mqtt_broker}")
        else:
            print(f"[MQTT ERROR] Connection failed with code: {rc}")
    
    def on_mqtt_publish(self, client, userdata, mid):
        """Callback when MQTT publishes message"""
        print(f"[MQTT PUBLISHED] Message ID: {mid}")
    
    def toggle_light(self):
        """Toggle light on/off via MQTT"""
        self.light_state = not self.light_state
        message = "on" if self.light_state else "off"
        
        try:
            result = self.mqtt_client.publish(self.mqtt_topic_light, message, qos=1)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"[MQTT PUBLISH] Sent: {message} to {self.mqtt_topic_light}")
                self.update_light_button_style()
            else:
                print(f"[MQTT ERROR] Failed to publish: {result.rc}")
                QMessageBox.warning(
                    self,
                    "MQTT Error",
                    f"Failed to send command. Error code: {result.rc}"
                )
        except Exception as e:
            print(f"[MQTT ERROR] Exception: {e}")
            QMessageBox.critical(
                self,
                "Connection Error",
                f"Failed to communicate with MQTT broker:\n{str(e)}"
            )
    
    def update_light_button_style(self):
        """Update button appearance based on light state"""
        if self.light_state:
            # Light is ON - Yellow/Amber style
            self.light_btn.setText("💡 Light OFF")
            self.light_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #FFD93D, stop:1 #FFA500);
                    color: #333;
                    border: none;
                    border-radius: 10px;
                    padding: 12px 20px;
                    font-size: 15px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #FFE066, stop:1 #FFB833);
                }
                QPushButton:pressed {
                    background: #FF8C00;
                }
            """)
        else:
            # Light is OFF - Gray style
            self.light_btn.setText("💡 Light ON")
            self.light_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #95A5A6, stop:1 #7F8C8D);
                    color: white;
                    border: none;
                    border-radius: 10px;
                    padding: 12px 20px;
                    font-size: 15px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #A8B8B9, stop:1 #8C9C9D);
                }
                QPushButton:pressed {
                    background: #6C7A7B;
                }
            """)
    
    def toggle_barrier_in(self):
        """Toggle barrier IN open/close via MQTT"""
        self.barrier_in_state = not self.barrier_in_state
        message = "open" if self.barrier_in_state else "close"
        
        try:
            result = self.mqtt_client.publish(self.mqtt_topic_barrier_in, message, qos=1)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"[MQTT PUBLISH] Sent: {message} to {self.mqtt_topic_barrier_in}")
                self.update_barrier_in_button_style()
            else:
                print(f"[MQTT ERROR] Failed to publish: {result.rc}")
                QMessageBox.warning(
                    self,
                    "MQTT Error",
                    f"Failed to send command. Error code: {result.rc}"
                )
        except Exception as e:
            print(f"[MQTT ERROR] Exception: {e}")
            QMessageBox.critical(
                self,
                "Connection Error",
                f"Failed to communicate with MQTT broker:\n{str(e)}"
            )
    
    def toggle_barrier_out(self):
        """Toggle barrier OUT open/close via MQTT"""
        self.barrier_out_state = not self.barrier_out_state
        message = "open" if self.barrier_out_state else "close"
        
        try:
            result = self.mqtt_client.publish(self.mqtt_topic_barrier_out, message, qos=1)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"[MQTT PUBLISH] Sent: {message} to {self.mqtt_topic_barrier_out}")
                self.update_barrier_out_button_style()
            else:
                print(f"[MQTT ERROR] Failed to publish: {result.rc}")
                QMessageBox.warning(
                    self,
                    "MQTT Error",
                    f"Failed to send command. Error code: {result.rc}"
                )
        except Exception as e:
            print(f"[MQTT ERROR] Exception: {e}")
            QMessageBox.critical(
                self,
                "Connection Error",
                f"Failed to communicate with MQTT broker:\n{str(e)}"
            )
    
    def update_barrier_in_button_style(self):
        """Update barrier IN button appearance based on state"""
        if self.barrier_in_state:
            # Barrier is OPEN - Green style
            self.barrier_in_btn.setText("🚧 Close IN")
            self.barrier_in_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #56ab2f, stop:1 #a8e063);
                    color: white;
                    border: none;
                    border-radius: 10px;
                    padding: 12px 20px;
                    font-size: 15px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #6bc245, stop:1 #b8f073);
                }
                QPushButton:pressed {
                    background: #4A9428;
                }
            """)
        else:
            # Barrier is CLOSED - Red style
            self.barrier_in_btn.setText("🚧 Open IN")
            self.barrier_in_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #eb3349, stop:1 #f45c43);
                    color: white;
                    border: none;
                    border-radius: 10px;
                    padding: 12px 20px;
                    font-size: 15px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #f44456, stop:1 #ff6d50);
                }
                QPushButton:pressed {
                    background: #D42C3E;
                }
            """)
    
    def update_barrier_out_button_style(self):
        """Update barrier OUT button appearance based on state"""
        if self.barrier_out_state:
            # Barrier is OPEN - Green style
            self.barrier_out_btn.setText("🚧 Close OUT")
            self.barrier_out_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #56ab2f, stop:1 #a8e063);
                    color: white;
                    border: none;
                    border-radius: 10px;
                    padding: 12px 20px;
                    font-size: 15px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #6bc245, stop:1 #b8f073);
                }
                QPushButton:pressed {
                    background: #4A9428;
                }
            """)
        else:
            # Barrier is CLOSED - Red style
            self.barrier_out_btn.setText("🚧 Open OUT")
            self.barrier_out_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #eb3349, stop:1 #f45c43);
                    color: white;
                    border: none;
                    border-radius: 10px;
                    padding: 12px 20px;
                    font-size: 15px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #f44456, stop:1 #ff6d50);
                }
                QPushButton:pressed {
                    background: #D42C3E;
                }
            """)
