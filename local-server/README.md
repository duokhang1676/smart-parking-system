# 🚗 Hệ Thống Bãi Đỗ Xe Thông Minh (Smart Parking System)

> **Edge Computing Solution** - Hệ thống quản lý bãi đỗ xe thông minh sử dụng Computer Vision và YOLO trên Jetson Nano

[![Python](https://img.shields.io/badge/Python-3.10-blue.svg)](https://www.python.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.12-green.svg)](https://opencv.org/)
[![YOLO](https://img.shields.io/badge/YOLO-v8-red.svg)](https://github.com/ultralytics/ultralytics)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📋 Mục Lục
- [Giới Thiệu](#-giới-thiệu)
- [Tính Năng](#-tính-năng)
- [Kiến Trúc Hệ Thống](#-kiến-trúc-hệ-thống)
- [Yêu Cầu](#-yêu-cầu)
- [Cài Đặt](#-cài-đặt)
- [Cấu Hình](#-cấu-hình)
- [Sử Dụng](#-sử-dụng)
- [Cấu Trúc Dự Án](#-cấu-trúc-dự-án)
- [API Documentation](#-api-documentation)
- [Hiệu Suất](#-hiệu-suất)

---

## 🎯 Giới Thiệu

Trong bối cảnh nhu cầu đỗ xe ô tô ngày càng gia tăng nhưng quỹ đất đô thị hạn chế, việc quản lý hiệu quả không gian bãi đỗ trở thành một yêu cầu cấp thiết. Hệ thống này sử dụng **Computer Vision** kết hợp **YOLO Deep Learning** để:

- ✅ Phát hiện trạng thái chiếm dụng chỗ đỗ real-time
- ✅ Nhận dạng biển số xe tự động (License Plate Recognition)
- ✅ Tracking xe đa camera với Re-Identification
- ✅ Quản lý ra/vào tự động với QR code
- ✅ Giảm 80% chi phí so với cảm biến truyền thống

### 🔬 Kết Quả Nghiên Cứu
- **mAP@0.5**: 72.4%
- **mAP@0.5:0.95**: 48.9%
- **Latency**: < 300ms trên Jetson Nano
- **Dataset**: 1,000+ ảnh xe thực tế + 300 ảnh mô hình

---

## ✨ Tính Năng

### 🎥 Computer Vision
- **Multi-Camera Tracking**: Theo dõi xe qua nhiều camera với Re-ID
- **License Plate Recognition**: OCR biển số xe Việt Nam
- **Parking Slot Detection**: Phát hiện trạng thái trống/đầy
- **QR Code Scanner**: Quét mã QR để xác thực

### 🚦 Quản Lý Tự Động
- **Auto Barrier Control**: Điều khiển barie vào/ra tự động
- **Smart Lighting**: Tự động bật/tắt đèn theo ánh sáng môi trường
- **Vehicle Verification**: Xác thực biển số với user_id
- **Wrong Parking Detection**: Phát hiện đỗ sai vị trí

### 📊 Giám Sát & Báo Cáo
- **Real-time Dashboard**: Hiển thị trạng thái bãi đỗ
- **History Tracking**: Lưu lịch sử ra/vào
- **Parking Time Calculation**: Tính toán thời gian đỗ
- **Slot Recommendation**: Gợi ý vị trí đỗ tối ưu

### 🔗 IoT Integration
- **MQTT Protocol**: Điều khiển từ xa qua MQTT
- **Cloud Sync**: Đồng bộ dữ liệu với cloud server
- **RESTful API**: Tích hợp với mobile app

---

## 🏗 Kiến Trúc Hệ Thống

```
┌─────────────────────────────────────────────────────────────┐
│                    Edge Device (Jetson Nano)                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐              │
│  │ Camera 0  │  │ Camera 1  │  │ Camera 2  │              │
│  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘              │
│        │              │              │                      │
│        └──────────────┴──────────────┘                      │
│                       │                                     │
│         ┌─────────────▼──────────────┐                     │
│         │   YOLO Object Detection    │                     │
│         │   + BoT-SORT Tracking      │                     │
│         └─────────────┬──────────────┘                     │
│                       │                                     │
│         ┌─────────────▼──────────────┐                     │
│         │   Re-ID Synchronization    │                     │
│         │   (Multi-Camera Merge)     │                     │
│         └─────────────┬──────────────┘                     │
│                       │                                     │
│    ┌──────────────────┼──────────────────┐                │
│    │                  │                  │                │
│    ▼                  ▼                  ▼                │
│ ┌─────────┐    ┌─────────┐      ┌─────────┐              │
│ │License  │    │Slot     │      │QR Code  │              │
│ │Plate    │    │Monitor  │      │Scanner  │              │
│ │OCR      │    │         │      │         │              │
│ └────┬────┘    └────┬────┘      └────┬────┘              │
│      │              │                 │                   │
│      └──────────────┴─────────────────┘                   │
│                     │                                      │
│       ┌─────────────▼──────────────┐                      │
│       │   Global State Manager     │                      │
│       │   (Multiprocess Shared)    │                      │
│       └─────────────┬──────────────┘                      │
│                     │                                      │
├─────────────────────┼──────────────────────────────────────┤
│                     │                                      │
│  ┌──────────────────▼───────────────────┐                 │
│  │       Hardware Controllers           │                 │
│  ├──────────────────────────────────────┤                 │
│  │  UART (BGM220)  │  MQTT  │  GPIO    │                 │
│  │  - Barrier      │  Light │  Sensors │                 │
│  │  - Sensors      │  Servo │          │                 │
│  └──────────────────┬───────────────────┘                 │
│                     │                                      │
└─────────────────────┼──────────────────────────────────────┘
                      │
        ┌─────────────▼──────────────┐
        │      Cloud Server API      │
        │  - User Management         │
        │  - History Storage         │
        │  - Real-time Updates       │
        └────────────────────────────┘
```

---

## 💻 Yêu Cầu

### Hardware
- **Jetson Nano B01** (4GB RAM recommended)
- **USB Cameras**: 2-3 cameras (640x480 @ 15fps)
- **BGM220 Module**: UART communication
- **Servo Motors**: Barrier control
- **Light Sensors**: Auto lighting control

### Software
- **Python**: 3.10+
- **CUDA**: 10.2+ (cho Jetson)
- **OpenCV**: 4.11+
- **PyTorch**: 1.8+

---

## 📦 Cài Đặt

### 1. Clone Repository
```bash
git clone https://github.com/duokhang1676/parking-edge-device.git
cd parking-edge-device
```

### 2. Tạo Virtual Environment
```bash
python -m venv parking-env
source parking-env/bin/activate  # Linux/Mac
# hoặc
parking-env\Scripts\activate  # Windows
```

### 3. Cài Đặt Dependencies
```bash
pip install -r requirements.txt
```

**Requirements chính:**
```
opencv-python==4.12.0.88
ultralytics==8.0.0
torch>=1.8.0
numpy==1.24.4
PyYAML
paho-mqtt
python-dotenv
pyserial
gTTS
python-vlc
requests
```

### 4. Tải Models
```bash
# YOLO models sẽ được tải tự động khi chạy lần đầu
# Hoặc download thủ công:
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt
```

---

## ⚙️ Cấu Hình

### 1. File `.env`
Tạo file `.env` trong thư mục gốc:

```env
# Parking Configuration
PARKING_ID=parking_001

# Camera Sources
TRACKING_CAMERA=[0, 1]
LICENSE_CAMERA=2

# UART Communication
UART_PORT=COM5
UART_BAUDRATE=115200

# Model Paths
DETECT_MODEL_PATH=app/resources/models/yolov8n-416.pt

# Cloud Server
CLOUD_SERVER_URL=https://parking-cloud-server.onrender.com/api/

# Pricing
PRICE_PER_HOUR=10000
```

### 2. Camera Coordinates
Cấu hình tọa độ ô đỗ và điểm Re-ID trong các file YAML:
```
app/resources/coordinates/
├── slot-data/
│   ├── 0.yml  # Camera 0 parking slots
│   └── 1.yml  # Camera 1 parking slots
└── reid-data/
    ├── 0.yml  # Camera 0 ReID points
    └── 1.yml  # Camera 1 ReID points
```

**Format YAML:**
```yaml
- id: A1
  coordinate: [320, 240]
- id: A2
  coordinate: [450, 250]
```

---

## 🚀 Sử Dụng

### Chạy Hệ Thống Đầy Đủ
```bash
python main.py
```

### Test Cameras
```bash
# Scan cameras
python scan_cameras.py

# Test hiển thị
python testcam.py
```

### Test Modules Riêng
```python
# Test tracking
from app.modules import tracking_car
tracking_car.start_tracking_car()

# Test license detection
from app.modules import detect_license
detect_license.start_detect_license()

# Test MQTT
from app.modules import turn_light_servo
turn_light_servo.start_turn_light_servo()
```

### MQTT Control
```python
import paho.mqtt.client as mqtt

client = mqtt.Client()
client.connect("broker.hivemq.com", 1883)

# Điều khiển đèn
client.publish("parking/light", "on")

# Điều khiển barie
client.publish("parking/barrier/in", "open")
client.publish("parking/barrier/out", "close")
```

---

## 📂 Cấu Trúc Dự Án

```
parking-edge-device/
├── main.py                      # Entry point
├── .env                         # Configuration
├── README.md                    # Documentation
│
├── app/
│   └── modules/
│       ├── globals.py           # Shared state management
│       ├── tracking_car.py      # Multi-camera tracking + Re-ID
│       ├── detect_license.py    # License plate OCR + QR
│       ├── connect_bgm220.py    # UART hardware control
│       ├── turn_light_servo.py  # MQTT control
│       ├── cloud_api.py         # Cloud server API
│       └── utils.py             # Helper functions
│
├── app/resources/
│   ├── coordinates/             # Parking layout configs
│   │   ├── slot-data/          # Slot positions
│   │   └── reid-data/          # ReID intersection points
│   │
│   ├── database/               # Local JSON storage
│   │   ├── parked_vehicles.json
│   │   ├── new_license.json
│   │   └── registered_vehicles.json
│   │
│   ├── models/                 # YOLO models
│   │   ├── yolov8n-416.pt
│   │   └── detect-car-yolov8n-v2.pt
│   │
│   ├── license_plate_recognition/
│   │   ├── detectLicense.py
│   │   ├── model/
│   │   │   ├── LP_detector_nano_61.pt
│   │   │   └── LP_ocr_nano_62.pt
│   │   └── yolov5/
│   │
│   ├── tracker/                # BoT-SORT configs
│   │   ├── botsort.yaml
│   │   └── bytetrack.yaml
│   │
│   └── mp3/                    # Voice notifications
│
└── docs/
    ├── REID_ALGORITHM.md       # Re-ID documentation
    ├── REID_METHODOLOGY.md     # Academic paper
    └── GIVE_WAY_USAGE.md       # Multi-process control guide
```

---

## 📡 API Documentation

### Cloud Server Endpoints

#### 1. Get Coordinates
```http
GET /coordinates/{parking_id}/{camera_id}
```
**Response:**
```json
{
  "coordinates_list": [...],
  "coordinates_reid_list": [...]
}
```

#### 2. Update Parking Lot
```http
POST /parking_slots/update_parking_slots
```
**Body:**
```json
{
  "parking_id": "parking_001",
  "available_list": ["A1", "A2"],
  "occupied_list": ["B1"],
  "occupied_license_list": ["30A-12345"]
}
```

#### 3. Insert History
```http
POST /histories/
```
**Body:**
```json
{
  "parking_id": "parking_001",
  "user_id": "user123",
  "license_plate": "30A-12345",
  "time_in": "2025-12-10T14:30:00",
  "time_out": "2025-12-10T16:45:00",
  "parking_time": 2.25,
  "total_price": 22500
}
```

---

## 📊 Hiệu Suất

### Benchmarks trên Jetson Nano B01

| Metric | Value |
|--------|-------|
| **Detection FPS** | 15-20 fps (640x480) |
| **Tracking Latency** | < 300ms |
| **OCR Accuracy** | 92%+ (Vietnamese plates) |
| **Re-ID Accuracy** | 85%+ |
| **RAM Usage** | ~2.5GB |
| **Power Consumption** | 10W |

### Multi-Camera Performance

| Cameras | Resolution | FPS | CPU Usage |
|---------|-----------|-----|-----------|
| 2 | 640x480 | 15 | 70% |
| 3 | 320x240 | 15 | 85% |

---

## 🔧 Troubleshooting

### Camera không hiển thị
```bash
# Scan available cameras
python scan_cameras.py

# Test từng camera
python testcam.py
```

### UART không kết nối
- Kiểm tra Device Manager (Windows) hoặc `ls /dev/tty*` (Linux)
- Đảm bảo baudrate đúng (115200)
- Kiểm tra quyền truy cập port

### MQTT không nhận message
- Kiểm tra broker: `broker.hivemq.com:1883`
- Đảm bảo topics khớp giữa pub/sub
- Test với MQTT Explorer tool

---

## 📖 Tài Liệu Thêm

- [Re-ID Algorithm](docs/REID_ALGORITHM.md)
- [Re-ID Methodology](docs/REID_METHODOLOGY.md)
- [Give Way Usage](docs/GIVE_WAY_USAGE.md)

---

## 👥 Đóng Góp

Chúng tôi hoan nghênh mọi đóng góp! Vui lòng:

1. Fork repository
2. Tạo branch mới (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Tạo Pull Request

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---

## 📞 Liên Hệ

**Project Maintainer**: Duo Khang  
**Email**: duokhang1676@gmail.com  
**Repository**: [github.com/duokhang1676/parking-edge-device](https://github.com/duokhang1676/parking-edge-device)

---

## 🙏 Acknowledgments

- [Ultralytics YOLO](https://github.com/ultralytics/ultralytics)
- [BoT-SORT](https://github.com/NirAharon/BoT-SORT)
- [OpenCV](https://opencv.org/)
- [Jetson Community](https://forums.developer.nvidia.com/c/agx-autonomous-machines/jetson-embedded-systems/)

---

<div align="center">
  Made with ❤️ for Smart Parking Solutions
</div>