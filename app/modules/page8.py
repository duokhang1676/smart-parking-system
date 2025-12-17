from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QFrame, QPushButton, QMessageBox, QLineEdit, QScrollArea, QCompleter)
from PyQt5.QtCore import Qt, pyqtSignal, QUrl, QTimer, QStringListModel
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
import qtawesome as qta
import paho.mqtt.client as mqtt
import requests
from datetime import datetime

from app.database.db_manager import get_parking_id, get_cloud_server_url
from app.modules.theme_colors import AppColors


class VehicleSearchPage(QWidget):
    # Signal để cập nhật ảnh từ thread khác
    image_received = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
        # Theme state
        self.is_dark_theme = True
        
        # Lấy thông tin từ config
        self.parking_id = get_parking_id()
        self.cloud_server_url = get_cloud_server_url()
        
        # MQTT Configuration
        self.mqtt_broker = "broker.hivemq.com"
        self.mqtt_port = 1883
        self.mqtt_topic_search = "parking/vehicle/search"
        self.mqtt_topic_show = "parking/vehicle/show"
        
        # State variables
        self.current_license = ""
        self.current_image_url = ""
        
        # License plates cache for autocomplete
        self.license_plates_cache = []
        self.completer_model = QStringListModel()
        
        # Timer to update license plates cache
        self.cache_timer = QTimer()
        self.cache_timer.timeout.connect(self.update_license_cache)
        self.cache_timer.start(30000)  # Update every 30 seconds
        
        # Network manager cho load ảnh
        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self.on_image_loaded)
        
        # Initialize MQTT client
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_mqtt_connect
        self.mqtt_client.on_message = self.on_mqtt_message
        self.mqtt_client.on_publish = self.on_mqtt_publish
        
        # Connect signal
        self.image_received.connect(self.display_image)
        
        try:
            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, 60)
            self.mqtt_client.loop_start()
        except Exception as e:
            print(f"[MQTT ERROR] Failed to connect: {e}")
        
        self.init_ui()
    
    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # ========== SEARCH SECTION ==========
        search_frame = QFrame()
        search_frame.setObjectName("searchFrame")
        search_frame.setStyleSheet(f"""
            #searchFrame {{
                background-color: white;
                border-radius: 10px;
                border: 1px solid #E0E0E0;
                padding: 15px 20px;
            }}
        """)
        
        search_layout = QHBoxLayout()
        search_layout.setSpacing(15)
        
        # Title label
        title_label = QLabel("🔍 Vehicle Search:")
        title_label.setStyleSheet("""
            color: #333;
            font-size: 16px;
            font-weight: bold;
        """)
        search_layout.addWidget(title_label)
        
        search_layout.addWidget(title_label)
        
        # License plate input
        self.license_input = QLineEdit()
        self.license_input.setPlaceholderText("Enter license plate (e.g., 30K-55055)")
        self.license_input.setStyleSheet("""
            QLineEdit {
                padding: 12px 15px;
                font-size: 15px;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                background: #F8F9FA;
            }
            QLineEdit:focus {
                border: 2px solid #667eea;
                background: white;
            }
        """)
        
        # Setup autocomplete
        self.completer = QCompleter()
        self.completer.setModel(self.completer_model)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchContains)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.license_input.setCompleter(self.completer)
        
        # Connect events
        self.license_input.textChanged.connect(self.format_license_plate)
        self.license_input.returnPressed.connect(self.search_vehicle)
        search_layout.addWidget(self.license_input, stretch=3)
        
        # Search button
        self.search_btn = QPushButton()
        self.search_btn.setText("🔍 Search")
        self.search_btn.setIcon(qta.icon('fa5s.search', color='white'))
        self.search_btn.clicked.connect(self.search_vehicle)
        self.search_btn.setFixedWidth(150)
        self.search_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 15px;
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
        search_layout.addWidget(self.search_btn)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setFixedWidth(120)
        self.status_label.setStyleSheet("""
            color: #666;
            font-size: 13px;
            padding: 8px 10px;
            background: #F0F0F0;
            border-radius: 6px;
        """)
        search_layout.addWidget(self.status_label)
        
        search_frame.setLayout(search_layout)
        main_layout.addWidget(search_frame)
        
        # ========== IMAGE DISPLAY SECTION ==========
        image_frame = QFrame()
        image_frame.setObjectName("imageFrame")
        image_frame.setStyleSheet(f"""
            #imageFrame {{
                background-color: white;
                border-radius: 10px;
                border: 1px solid #E0E0E0;
                padding: 15px;
            }}
        """)
        
        image_layout = QVBoxLayout()
        image_layout.setSpacing(10)
        
        # Image display area
        image_display_frame = QFrame()
        image_display_frame.setMinimumHeight(650)
        image_display_frame.setStyleSheet("""
            QFrame {
                border: 2px dashed #E0E0E0;
                border-radius: 8px;
                background: #F8F9FA;
            }
        """)
        
        image_display_layout = QVBoxLayout()
        image_display_layout.setContentsMargins(10, 10, 10, 10)
        image_display_layout.setAlignment(Qt.AlignCenter)
        
        # Image label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("""
            QLabel {
                color: #999;
                font-size: 16px;
            }
        """)
        self.image_label.setText("No image to display\n\nEnter a license plate and click Search")
        
        image_display_layout.addWidget(self.image_label)
        image_display_frame.setLayout(image_display_layout)
        image_layout.addWidget(image_display_frame)
        
        # Image info
        self.image_info_label = QLabel("")
        self.image_info_label.setStyleSheet("""
            color: #666;
            font-size: 12px;
            padding: 5px 8px;
        """)
        self.image_info_label.setWordWrap(True)
        image_layout.addWidget(self.image_info_label)
        
        image_frame.setLayout(image_layout)
        main_layout.addWidget(image_frame, stretch=10)
        
        self.setLayout(main_layout)
        
        # Load initial license plates cache
        self.update_license_cache()
    
    def apply_theme_style(self, is_dark):
        """Apply theme styling"""
        self.is_dark_theme = is_dark
        # Theme can be customized here if needed
    
    def format_license_plate(self):
        """Auto format license plate: uppercase and add dash"""
        text = self.license_input.text()
        cursor_pos = self.license_input.cursorPosition()
        
        # Remove existing dash for reformatting
        text_no_dash = text.replace("-", "")
        
        # Convert to uppercase
        text_upper = text_no_dash.upper()
        
        # Auto add dash after position (e.g., 30K -> 30K-, or 30KS -> 30KS-)
        # Format: [digits][letter(s)]-[digits]
        formatted = text_upper
        
        # Find position to insert dash
        # Look for pattern: digits followed by letter(s)
        import re
        match = re.match(r'^(\d+[A-Z]+)(\d+)$', text_upper)
        if match:
            # Has both parts: add dash between
            formatted = f"{match.group(1)}-{match.group(2)}"
        elif re.match(r'^\d+[A-Z]+$', text_upper) and len(text_upper) > 2:
            # Only first part, ready for dash
            if text.endswith("-"):
                formatted = text_upper
            else:
                formatted = text_upper
        
        # Only update if text changed
        if formatted != text:
            # Block signals to avoid recursion
            self.license_input.blockSignals(True)
            self.license_input.setText(formatted)
            
            # Restore cursor position
            new_cursor_pos = cursor_pos
            if formatted.count("-") > text.count("-"):
                new_cursor_pos += 1
            self.license_input.setCursorPosition(min(new_cursor_pos, len(formatted)))
            
            self.license_input.blockSignals(False)
    
    def update_license_cache(self):
        """Update cache of license plates from API for autocomplete"""
        try:
            api_url = f"{self.cloud_server_url}parked_vehicles/get_parked_vehicles"
            response = requests.post(api_url, json={"parking_id": self.parking_id}, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                vehicles = data.get("parked_vehicles", [])
                
                # Get unique license plates
                license_plates = list(set([v.get("license_plate", "") for v in vehicles if v.get("license_plate")]))
                self.license_plates_cache = sorted(license_plates)
                self.completer_model.setStringList(self.license_plates_cache)
                
                print(f"[CACHE] Updated {len(self.license_plates_cache)} license plates")
        except Exception as e:
            print(f"[CACHE ERROR] Failed to update license cache: {e}")
    
    # ========== MQTT METHODS ==========
    def on_mqtt_connect(self, client, userdata, flags, rc):
        """Callback when MQTT connects"""
        if rc == 0:
            print(f"[MQTT CONNECTED] Successfully connected to broker {self.mqtt_broker}")
            # Subscribe to show topic
            client.subscribe(self.mqtt_topic_show, qos=1)
            print(f"[MQTT SUBSCRIBE] Subscribed to {self.mqtt_topic_show}")
        else:
            print(f"[MQTT ERROR] Connection failed with code: {rc}")
    
    def on_mqtt_message(self, client, userdata, msg):
        """Callback when MQTT receives message"""
        try:
            topic = msg.topic
            message = msg.payload.decode('utf-8')
            
            print(f"[MQTT RECEIVED] Topic: {topic}, Message: {message}")
            
            if topic == self.mqtt_topic_show:
                # Nhận được đường dẫn ảnh
                self.current_image_url = message
                self.image_received.emit(message)
                
        except Exception as e:
            print(f"[MQTT ERROR] Message processing error: {e}")
    
    def on_mqtt_publish(self, client, userdata, mid):
        """Callback when MQTT publishes message"""
        print(f"[MQTT PUBLISHED] Message ID: {mid}")
    
    def search_vehicle(self):
        """Send search request via MQTT"""
        license_plate = self.license_input.text().strip()
        
        if not license_plate:
            QMessageBox.warning(
                self,
                "Empty Input",
                "Please enter a license plate number"
            )
            return
        
        # Validate: license plate must be in active cars list
        if license_plate not in self.license_plates_cache:
            QMessageBox.warning(
                self,
                "Vehicle Not Found",
                f"Vehicle with license plate '{license_plate}' is not currently in the parking lot.\n\n"
                f"Please check the license plate or verify the vehicle is parked."
            )
            # Reset status
            self.status_label.setText("Ready")
            self.status_label.setStyleSheet("""
                color: #666;
                font-size: 13px;
                padding: 8px 10px;
                background: #F0F0F0;
                border-radius: 6px;
            """)
            return
        
        self.current_license = license_plate
        
        # Update status
        self.status_label.setText(f"🔄 Searching...")
        self.status_label.setStyleSheet("""
            color: #667eea;
            font-size: 13px;
            padding: 8px 10px;
            background: #E8EEFF;
            border-radius: 6px;
            font-weight: 600;
        """)
        
        try:
            # Publish search request
            result = self.mqtt_client.publish(self.mqtt_topic_search, license_plate, qos=1)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"[MQTT PUBLISH] Sent search request: {license_plate} to {self.mqtt_topic_search}")
                
                # Clear previous image
                self.image_label.clear()
                self.image_label.setText(f"⏳ Waiting for image of vehicle: {license_plate}...")
                self.image_info_label.setText(f"Search sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
            else:
                print(f"[MQTT ERROR] Failed to publish search: {result.rc}")
                self.status_label.setText(f"❌ Failed")
                self.status_label.setStyleSheet("""
                    color: #E74C3C;
                    font-size: 13px;
                    padding: 8px 10px;
                    background: #FFEBEE;
                    border-radius: 6px;
                """)
                QMessageBox.warning(
                    self,
                    "MQTT Error",
                    f"Failed to send search command. Error code: {result.rc}"
                )
        except Exception as e:
            print(f"[MQTT ERROR] Exception: {e}")
            self.status_label.setText(f"❌ Error")
            self.status_label.setStyleSheet("""
                color: #E74C3C;
                font-size: 13px;
                padding: 8px 10px;
                background: #FFEBEE;
                border-radius: 6px;
            """)
            QMessageBox.critical(
                self,
                "Connection Error",
                f"Failed to communicate with MQTT broker:\n{str(e)}"
            )
    
    def display_image(self, image_url):
        """Load and display image from URL"""
        print(f"[IMAGE] Loading image from: {image_url}")
        
        # Update status
        self.status_label.setText(f"✅ Found")
        self.status_label.setStyleSheet("""
            color: #27AE60;
            font-size: 14px;
            margin-top: 10px;
            padding: 8px 12px;
            background: #E8F8F5;
            border-radius: 6px;
            font-weight: 600;
        """)
        
        # Show loading text
        self.image_label.setText(f"📥 Loading image from Cloudinary...")
        
        # Load image from URL
        try:
            request = QNetworkRequest(QUrl(image_url))
            self.network_manager.get(request)
        except Exception as e:
            print(f"[IMAGE ERROR] Failed to load image: {e}")
            self.image_label.setText(f"❌ Error loading image\n\n{str(e)}")
            self.image_info_label.setText(f"Error: {str(e)}")
    
    def on_image_loaded(self, reply):
        """Callback when image is loaded from network"""
        if reply.error() == QNetworkReply.NoError:
            # Load image data
            image_data = reply.readAll()
            pixmap = QPixmap()
            pixmap.loadFromData(image_data)
            
            if not pixmap.isNull():
                # Scale ảnh vừa khung hiển thị
                scaled_pixmap = pixmap.scaled(
                    1024, 600,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                
                self.image_label.setPixmap(scaled_pixmap)
                
                # Update info
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.image_info_label.setText(
                    f"License Plate: {self.current_license} | "
                    f"Image Size: {pixmap.width()}x{pixmap.height()}px | "
                    f"Loaded at: {current_time}\n"
                    f"URL: {self.current_image_url}"
                )
                
                print(f"[IMAGE] Successfully loaded image: {pixmap.width()}x{pixmap.height()}px")
            else:
                self.image_label.setText("❌ Invalid image format")
                self.image_info_label.setText("Error: Could not decode image")
        else:
            error_msg = reply.errorString()
            print(f"[IMAGE ERROR] Network error: {error_msg}")
            self.image_label.setText(f"❌ Failed to load image\n\n{error_msg}")
            self.image_info_label.setText(f"Network Error: {error_msg}")
        
        reply.deleteLater()
    
    def closeEvent(self, event):
        """Clean up MQTT connection and timers when closing"""
        try:
            self.cache_timer.stop()
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            print("[MQTT] Disconnected")
        except:
            pass
        event.accept()
