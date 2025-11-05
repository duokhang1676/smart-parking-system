from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QGridLayout
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QPalette, QFont
import requests
import random

class ParkingSlotPage(QWidget):
    def __init__(self):
        super().__init__()
        self.slot_names = ['A0', 'B0', 'C0', 'D0', 'A1', 'B1', 'C1', 'D1', 'A2', 'B2', 'C2', 'D2', 'A3', 'B3', 'C3', 'D3', 'A4', 'B4', 'C4', 'D4']
        self.slots = {}
        self.init_ui()

        # Timer for data update
        self.timer = QTimer()
        self.timer.timeout.connect(self.fetch_and_update_data)
        self.timer.start(1000)

    def init_ui(self):
        layout = QGridLayout()
        for i, slot_name in enumerate(self.slot_names):
            slot_widget = self.create_slot_widget(slot_name, "")
            layout.addWidget(slot_widget, i // 4, i % 4)
            self.slots[slot_name] = slot_widget
        self.setLayout(layout)

    def create_slot_widget(self, slot_name, license_value):
        slot_widget = QWidget()
        slot_layout = QVBoxLayout()
        slot_layout.setContentsMargins(5, 5, 5, 5)
        slot_widget.setLayout(slot_layout)
        slot_widget.setFixedSize(120, 100)

        slot_label = QLabel(slot_name)
        slot_label.setFont(QFont("Arial", 14, QFont.Bold))
        slot_label.setAlignment(Qt.AlignCenter)

        license_label = QLabel(license_value)
        license_label.setFont(QFont("Arial", 12))
        license_label.setAlignment(Qt.AlignCenter)
        slot_layout.addWidget(slot_label)
        slot_layout.addWidget(license_label)

        self.update_slot_color(slot_widget, license_value)
        return slot_widget

    def update_slot_color(self, widget, text):
        color = "#00FF00" if not text else "#FF0000"
        palette = widget.palette()
        palette.setColor(QPalette.Window, QColor(color))
        widget.setAutoFillBackground(True)
        widget.setPalette(palette)

    def fetch_and_update_data(self):
        # Example URL (replace with the actual API URL)
        # api_url = "http://127.0.0.1:5000/api/parking_slots/get_parking_slots"
        api_url = "https://parking-cloud-server.onrender.com/api/parking_slots/get_parking_slots"
        try:
            # Simulate data (use requests.get(api_url).json() in actual use)
            # Example response: {'occupied_list': ['A0', 'B1', 'C2'], 'occupied_license_list': ['71C3-12345', '56C4-7890', '88D1-4567']}
            # response = {
            #     'occupied_list': random.sample(self.slot_names, 5),
            #     'occupied_license_list': [f"{random.randint(10, 99)}C{random.randint(1000, 9999)}" for _ in range(5)]
            # }
            data = {
                "parking_id": "parking_001"
            }
            response = requests.post(api_url, json=data)
            if response.status_code != 200:
                print("lỗi khi load occupied license list")
                print(response.status_codek)
                return
            
            data = response.json()["data"]

            occupied_list = data['occupied_list']
            occupied_license_list = data['occupied_license_list']
            occupied_data = dict(zip(occupied_list, occupied_license_list))

            for slot_name, widget in self.slots.items():
                license_value = occupied_data.get(slot_name, "")
                license_label = widget.layout().itemAt(1).widget()
                license_label.setText(str(license_value))
                self.update_slot_color(widget, license_value)

        except Exception as e:
            print(f"Error fetching data: {e}")
