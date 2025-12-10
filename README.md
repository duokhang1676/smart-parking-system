# 🅿️ Smart Parking Management System

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![PyQt5](https://img.shields.io/badge/PyQt5-5.15-green.svg)](https://www.riverbankcomputing.com/software/pyqt/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Hệ thống quản lý bãi đỗ xe thông minh với giao diện desktop hiện đại, tích hợp AI phát hiện xe, nhận diện biển số, và điều khiển IoT (đèn, barrier) qua MQTT.

---

## 📋 Mục lục

- [Tính năng](#-tính-năng)
- [Kiến trúc hệ thống](#-kiến-trúc-hệ-thống)
- [Cài đặt](#-cài-đặt)
- [Cấu hình](#-cấu-hình)
- [Sử dụng](#-sử-dụng)
- [Cấu trúc dự án](#-cấu-trúc-dự-án)
- [API Endpoints](#-api-endpoints)
- [MQTT Topics](#-mqtt-topics)
- [Screenshots](#-screenshots)
- [Troubleshooting](#-troubleshooting)
- [License](#-license)

---

## ✨ Tính năng

### 🎯 Chức năng chính

#### 1. **Dashboard (Page 1)**
- 📊 Hiển thị real-time 15 slot đỗ xe (3 khu: A, B, C)
- 🎨 Trạng thái màu sắc: Trống (xanh), Có xe (đỏ), Trùng biển (vàng)
- 🔄 Auto-refresh mỗi 10 giây qua API
- 📈 Thống kê: Tổng slot, trống, đã dùng, tỷ lệ sử dụng

#### 2. **History (Page 2)**
- 📜 Lịch sử ra/vào theo ngày
- 🔍 Tìm kiếm theo biển số xe (autocomplete)
- 📅 Lọc theo khoảng thời gian
- 💾 Export dữ liệu

#### 3. **Active Cars (Page 3)**
- 🚗 Danh sách xe hiện đang trong bãi
- ⏱️ Tính thời gian đỗ real-time
- 🔍 Tìm kiếm nhanh
- 📊 Bảng thông tin chi tiết

#### 4. **Customers (Page 4)**
- 👥 Quản lý khách hàng đăng ký
- 📝 Thông tin: Họ tên, SĐT, biển số, ngày đăng ký
- 🔍 Tìm kiếm và lọc
- ✏️ CRUD operations

#### 5. **Settings (Page 5)**
- 📷 Setup camera và tọa độ slot
- 🎯 3 chế độ: Manual, Auto (YOLO), First-time
- 🖼️ Preview frame từ camera
- ☁️ Đồng bộ lên cloud server

#### 6. **Parking Info (Page 6)**
- ℹ️ Thông tin bãi xe
- 🆔 Parking ID, Server URL
- 📦 Sức chứa và tính năng

#### 7. **Environment Control (Page 7)**
- 🌡️ Monitoring môi trường: Nhiệt độ, độ ẩm, ánh sáng
- 💡 Điều khiển đèn (ON/OFF)
- 🚧 Điều khiển Barrier IN/OUT (Open/Close)
- 📡 MQTT real-time control

### 🛠️ Công nghệ

- **GUI Framework:** PyQt5 + qt-material (Material Design)
- **Computer Vision:** YOLOv8 (Ultralytics) + OpenCV
- **Database:** MongoDB (API-first architecture)
- **IoT Protocol:** MQTT (HiveMQ broker)
- **AI Models:** License Plate Recognition
- **HTTP Client:** requests library

---

## 🏗️ Kiến trúc hệ thống

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENT APPLICATION                        │
│              (PyQt5 Desktop - Windows)                       │
├─────────────────────────────────────────────────────────────┤
│  Page 1: Dashboard          │  Page 5: Camera Setup         │
│  Page 2: History            │  Page 6: Parking Info         │
│  Page 3: Active Cars        │  Page 7: Environment + IoT    │
│  Page 4: Customers          │                                │
└──────────────┬──────────────────────────┬───────────────────┘
               │                          │
       ┌───────▼────────┐        ┌────────▼────────┐
       │  REST API       │        │  MQTT Broker    │
       │  (Flask)        │        │  (HiveMQ)       │
       └───────┬────────┘        └────────┬────────┘
               │                          │
       ┌───────▼────────┐        ┌────────▼────────┐
       │   MongoDB       │        │  IoT Devices    │
       │   Database      │        │  (ESP32/Arduino)│
       └─────────────────┘        └─────────────────┘
```

### 🔄 Data Flow

1. **Startup:** App connect MQTT → Load config → Fetch initial data
2. **Dashboard:** Timer (10s) → API call → Update UI
3. **IoT Control:** User click button → MQTT publish → Device receive
4. **Environment:** User click refresh → API call → Display metrics

---

## 📦 Cài đặt

### Yêu cầu hệ thống

- **OS:** Windows 10/11 (64-bit)
- **Python:** 3.10 hoặc cao hơn
- **RAM:** 4GB minimum (8GB recommended)
- **GPU:** CUDA-compatible (optional, for faster AI inference)

### Bước 1: Clone repository

```bash
git clone https://github.com/duokhang1676/parking-management-windows-app.git
cd parking-management-windows-app
```

### Bước 2: Tạo virtual environment

```bash
# Tạo venv
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate
```

### Bước 3: Cài đặt dependencies

```bash
pip install -r requirements.txt
```

**Lưu ý:** Nếu dùng GPU CUDA:

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### Bước 4: Setup MongoDB (Optional)

**Cách 1: MongoDB Local**
```bash
# Download MongoDB Community: https://www.mongodb.com/try/download/community
# Hoặc sử dụng Docker:
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

**Cách 2: MongoDB Atlas (Cloud)**
- Tạo free cluster tại [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
- Copy connection string

---

## ⚙️ Cấu hình

### 1. File `.env`

Tạo file `.env` trong thư mục gốc:

```bash
# Parking Configuration
PARKING_ID=parking_001

# Cloud Server API
CLOUD_SERVER_URL=https://your-api-server.com/api/

# MongoDB (Optional - chỉ cần nếu dùng local DB)
MONGODB_URI=mongodb://localhost:27017/
DATABASE_NAME=server_local
```

### 2. MQTT Configuration

Mặc định sử dụng HiveMQ public broker:
- **Broker:** `broker.hivemq.com`
- **Port:** `1883`
- **Topics:**
  - `parking/sensor/turn_light` (đèn)
  - `parking/sensor/barrier_in` (barrier vào)
  - `parking/sensor/barrier_out` (barrier ra)

**Thay đổi broker:** Sửa trong `modules/page7.py`:

```python
self.mqtt_broker = "your-mqtt-broker.com"
self.mqtt_port = 1883
```

### 3. AI Models

Models được lưu trong `resources/models/`:
- `detect-car-yolov8n-v2.pt` - Phát hiện xe
- `detect-parking-space-yolov8n.pt` - Phát hiện slot
- `LP_detector_nano_61.pt` - Phát hiện biển số
- `LP_ocr_nano_62.pt` - OCR biển số

**Download models:** (Nếu chưa có)
```bash
# Link download: [Thêm link Google Drive/OneDrive của bạn]
```

---

## 🚀 Sử dụng

### Khởi chạy ứng dụng

```bash
# Đảm bảo đã activate venv
python main.py
```

### Chức năng chính

#### 🔄 **Refresh Dashboard**
- Tự động: Mỗi 10 giây
- Thủ công: Click vào card "Total Slots"

#### 🔍 **Tìm kiếm History**
1. Chọn ngày trong DatePicker
2. Nhập biển số (có autocomplete)
3. Click "Search"

#### 💡 **Điều khiển đèn**
1. Vào trang "Environment" (sidebar)
2. Click button "💡 Light ON/OFF"
3. Đèn sẽ đổi màu (xám = tắt, vàng = bật)

#### 🚧 **Mở/Đóng Barrier**
1. Trang "Environment"
2. Click "🚧 Barrier IN" hoặc "🚧 Barrier OUT"
3. Màu: Đỏ = đóng, Xanh = mở

#### 📷 **Setup Camera**
1. Vào "Settings" → Chọn camera
2. Chọn chế độ:
   - **Manual:** Click để đánh dấu slot
   - **Auto:** YOLO tự động detect
   - **First-time:** Setup lần đầu
3. Click "Send to Server" để lưu

---

## 📁 Cấu trúc dự án

```
parking-management-windows-app/
│
├── main.py                          # Entry point
├── requirements.txt                 # Dependencies
├── .env                             # Config (tạo mới)
├── dockerfile                       # Docker config
│
├── database/
│   ├── __init__.py
│   └── db_manager.py               # MongoDB manager
│
├── modules/
│   ├── page1.py                    # Dashboard
│   ├── page2.py                    # History
│   ├── page3.py                    # Active cars
│   ├── page4.py                    # Customers
│   ├── page5.py                    # Settings
│   ├── page6.py                    # Parking info
│   ├── page7.py                    # Environment + IoT
│   ├── theme_colors.py             # Theme config
│   └── utils.py                    # Helper functions
│
├── resources/
│   ├── icons/                      # UI icons
│   ├── models/                     # AI models (.pt)
│   │   ├── detect-car-yolov8n-v2.pt
│   │   ├── detect-parking-space-yolov8n.pt
│   │   ├── LP_detector_nano_61.pt
│   │   └── LP_ocr_nano_62.pt
│   │
│   ├── coordinates/                # Coordinate generators
│   │   ├── coordinates_generator.py
│   │   ├── coordinates_generator_auto.py
│   │   ├── coordinates_generator_forFirst.py
│   │   └── colors.py
│   │
│   ├── license_plate_recognition/  # LPR module
│   │   ├── detectLicense.py
│   │   └── function/
│   │       ├── helper.py
│   │       └── utils_rotate.py
│   │
│   ├── print_bill/                 # Bill printing
│   │   └── print_bill.py
│   │
│   └── mp3/                        # Audio files
│
└── test_data/                      # Test images/videos
    ├── img/
    └── video/
```

---

## 🌐 API Endpoints

### Base URL
```
https://your-api-server.com/api/
```

### Endpoints sử dụng

#### 1. **Parking Slots**
```http
GET /parking_slots/get_parking_slots?parking_id={id}
```
Response:
```json
{
  "status": "success",
  "data": [
    {
      "slot_id": "A0",
      "status": "occupied",
      "license_plate": "29A12345",
      "entry_time": "2025-12-10T10:30:00"
    }
  ]
}
```

#### 2. **History by Date**
```http
GET /histories/by_parking_date?parking_id={id}&date=YYYY-MM-DD
```

#### 3. **Parked Vehicles**
```http
POST /parked_vehicles/get_parked_vehicles
Body: {"parking_id": "parking_001"}
```

#### 4. **Registered Customers**
```http
POST /registers/get_register_list
Body: {"parking_id": "parking_001"}
```

#### 5. **Environment**
```http
POST /environments/get_environment
Body: {"parking_id": "parking_001"}
```
Response:
```json
{
  "status": "success",
  "data": {
    "temperature": 28.5,
    "humidity": 65,
    "light": 450,
    "updated_at": "2025-12-10T14:20:00"
  }
}
```

---

## 📡 MQTT Topics

### Subscribe (Client nhận từ device)
```
parking/sensor/status          # Trạng thái thiết bị
parking/environment/data       # Dữ liệu môi trường
```

### Publish (Client gửi đến device)

#### 1. **Light Control**
```
Topic: parking/sensor/turn_light
Payload: "on" | "off"
```

#### 2. **Barrier IN**
```
Topic: parking/sensor/barrier_in
Payload: "open" | "close"
```

#### 3. **Barrier OUT**
```
Topic: parking/sensor/barrier_out
Payload: "open" | "close"
```

### Example code (Arduino/ESP32)

```cpp
#include <WiFi.h>
#include <PubSubClient.h>

const char* mqtt_server = "broker.hivemq.com";

void callback(char* topic, byte* payload, unsigned int length) {
  String message = "";
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  
  if (String(topic) == "parking/sensor/turn_light") {
    if (message == "on") {
      digitalWrite(LED_PIN, HIGH);
    } else {
      digitalWrite(LED_PIN, LOW);
    }
  }
}
```

---

## 📸 Screenshots

### Dashboard
![Dashboard](docs/screenshots/dashboard.png)

### History Page
![History](docs/screenshots/history.png)

### Environment Control
![Environment](docs/screenshots/environment.png)

---

## 🔧 Troubleshooting

### ❌ Lỗi: `ModuleNotFoundError: No module named 'PyQt5'`
**Giải pháp:**
```bash
pip install PyQt5
```

### ❌ Lỗi: `MQTT connection failed`
**Giải pháp:**
- Kiểm tra internet connection
- Thử broker khác: `test.mosquitto.org`
- Check firewall/antivirus

### ❌ Lỗi: `API timeout`
**Giải pháp:**
- Kiểm tra `CLOUD_SERVER_URL` trong `.env`
- Tăng timeout trong code:
```python
response = requests.post(api_url, json=data, timeout=30)
```

### ❌ Lỗi: `MongoDB connection refused`
**Giải pháp:**
- Đảm bảo MongoDB đang chạy: `mongod --version`
- Check port 27017: `netstat -an | findstr 27017`
- Hoặc disable MongoDB (app vẫn chạy với API-only)

### ❌ Ứng dụng khởi động chậm
**Giải pháp:**
- Đã tối ưu với delay 2s cho first fetch
- Disable MQTT nếu không dùng IoT
- Sử dụng SSD thay vì HDD

### ❌ Theme không load
**Giải pháp:**
```bash
pip uninstall qt-material
pip install qt-material==2.14
```

---

## 🎨 Customization

### Thay đổi theme

File: `main.py`
```python
# Dark theme (mặc định)
apply_stylesheet(app, theme='dark_teal.xml')

# Light theme
apply_stylesheet(app, theme='light_blue.xml')

# Các theme khác: dark_amber, light_cyan, dark_pink...
```

### Thêm slot mới

File: `modules/page1.py`
```python
# Thêm slot D0-D4
self.slot_names = ['A0', 'B0', 'C0', 'D0', 
                   'A1', 'B1', 'C1', 'D1', ...]
```

### Custom API endpoint

File: `.env`
```bash
CLOUD_SERVER_URL=https://your-new-api.com/v2/
```

---

## 🐳 Docker Deployment

### Build image

```bash
docker build -t parking-app:latest .
```

### Run container

```bash
docker run -d \
  -p 5900:5900 \
  -e PARKING_ID=parking_001 \
  -e CLOUD_SERVER_URL=https://api.example.com/api/ \
  --name parking-app \
  parking-app:latest
```

### Docker Compose

```yaml
version: '3.8'
services:
  parking-app:
    image: parking-app:latest
    ports:
      - "5900:5900"
    environment:
      - PARKING_ID=parking_001
      - CLOUD_SERVER_URL=https://api.example.com/api/
    restart: unless-stopped
```

---

## 🤝 Contributing

1. Fork repository
2. Tạo feature branch: `git checkout -b feature/AmazingFeature`
3. Commit changes: `git commit -m 'Add AmazingFeature'`
4. Push to branch: `git push origin feature/AmazingFeature`
5. Open Pull Request

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---

## 👥 Team

- **Developer:** duokhang1676
- **Email:** [your-email@example.com]
- **GitHub:** [@duokhang1676](https://github.com/duokhang1676)

---

## 🙏 Acknowledgments

- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/)
- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics)
- [MongoDB](https://www.mongodb.com/)
- [HiveMQ](https://www.hivemq.com/)
- [qt-material](https://github.com/UN-GCPDS/qt-material)

---

## 📞 Support

Nếu gặp vấn đề:
1. Check [Troubleshooting](#-troubleshooting)
2. Search [Issues](https://github.com/duokhang1676/parking-management-windows-app/issues)
3. Create new issue với:
   - Error message
   - Steps to reproduce
   - Python version
   - OS version

---

**⭐ Nếu project hữu ích, đừng quên star repository!**


