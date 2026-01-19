# 🚗 Parking Cloud Server

REST API Backend cho hệ thống quản lý bãi đỗ xe thông minh (Smart Parking Management System).

## 📋 Mục lục

- [Tính năng](#-tính-năng)
- [Công nghệ sử dụng](#-công-nghệ-sử-dụng)
- [Cài đặt](#-cài-đặt)
- [Cấu hình](#️-cấu-hình)
- [Chạy ứng dụng](#-chạy-ứng-dụng)
- [API Endpoints](#-api-endpoints)
- [Cấu trúc dự án](#-cấu-trúc-dự-án)
- [Deploy](#-deploy)

## ✨ Tính năng

- 👥 **Quản lý người dùng**: Đăng ký, đăng nhập, cập nhật thông tin
- 🅿️ **Quản lý bãi đỗ xe**: CRUD các bãi đỗ xe, trạng thái hoạt động
- 📝 **Đăng ký xe**: Đăng ký biển số xe cho từng bãi đỗ
- 🚘 **Quản lý xe đậu**: Theo dõi xe đang đỗ trong bãi
- 📊 **Lịch sử giao dịch**: Lưu trữ và truy vấn lịch sử đậu xe
- 🗺️ **Tọa độ & Môi trường**: Quản lý vị trí và thông tin môi trường bãi xe
- 🔍 **Tìm kiếm theo ngày**: Lọc lịch sử giao dịch theo parking_id và ngày tháng

## 🛠 Công nghệ sử dụng

- **Backend Framework**: Flask (Python)
- **Database**: MongoDB Atlas
- **Server**: Gunicorn
- **Deployment**: Render.com
- **Libraries**:
  - `pymongo` - MongoDB driver
  - `python-dotenv` - Quản lý biến môi trường
  - `werkzeug` - Utilities cho Flask
  - `flask` - Web framework

## 📦 Cài đặt

### Yêu cầu hệ thống

- Python 3.8+
- MongoDB Atlas account
- pip (Python package manager)

### Các bước cài đặt

1. **Clone repository**
```bash
git clone https://github.com/duokhang1676/parking-cloud-server.git
cd parking-cloud-server
```

2. **Tạo virtual environment** (khuyến nghị)
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Cài đặt dependencies**
```bash
pip install -r requirements.txt
```

## ⚙️ Cấu hình

1. **Tạo file `.env`** trong thư mục gốc:
```env
MONGO_URI=mongodb+srv://<username>:<password>@cluster.mongodb.net/?retryWrites=true&w=majority
```

2. **Thay thế thông tin MongoDB**:
   - `<username>`: Tên người dùng MongoDB
   - `<password>`: Mật khẩu MongoDB
   - `cluster`: Tên cluster của bạn

## 🚀 Chạy ứng dụng

### Development (Local)

```bash
python app.py
```

Server sẽ chạy tại: `http://localhost:5000`

### Production

```bash
gunicorn app:app
```

## 📡 API Endpoints

### 🏠 Root
```
GET /
```
Kiểm tra server hoạt động

---

### 👥 Users (`/api/users`)

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/api/users/` | Lấy danh sách tất cả users |
| POST | `/api/users/` | Tạo user mới |
| GET | `/api/users/<user_id>` | Lấy thông tin user theo ID |
| PUT | `/api/users/<user_id>` | Cập nhật thông tin user |
| DELETE | `/api/users/<user_id>` | Xóa user |

---

### 🅿️ Parkings (`/api/parking`)

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/api/parking/` | Lấy danh sách tất cả bãi đỗ xe |
| POST | `/api/parking/` | Tạo bãi đỗ xe mới |
| GET | `/api/parking/<parking_id>` | Lấy thông tin bãi đỗ xe |
| PUT | `/api/parking/<parking_id>` | Cập nhật thông tin bãi đỗ xe |
| DELETE | `/api/parking/<parking_id>` | Xóa bãi đỗ xe |

---

### 📝 Registers (`/api/registers`)

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/api/registers/` | Lấy danh sách tất cả đăng ký |
| POST | `/api/registers/get_register_list` | Lấy danh sách đăng ký theo parking_id |
| POST | `/api/registers/add_register_parking` | Đăng ký xe vào bãi |
| PUT | `/api/registers/update_register_parking` | Cập nhật đăng ký (gia hạn 30 ngày) |
| POST | `/api/registers/get_registered_vehicles` | Lấy danh sách xe đã đăng ký của user |

**Ví dụ: Lấy danh sách đăng ký**
```bash
POST /api/registers/get_register_list
Content-Type: application/json

{
  "parking_id": "parking_001"
}
```

---

### 📊 Histories (`/api/histories`)

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | `/api/histories/` | Thêm lịch sử giao dịch mới |
| POST | `/api/histories/get_parking_histories` | Lấy lịch sử theo user_id |
| GET | `/api/histories/by_parking_date` | Lấy lịch sử theo parking_id và ngày |

**Ví dụ: Lấy lịch sử theo ngày**
```bash
# Cách 1: Dùng tham số date
GET /api/histories/by_parking_date?parking_id=park123&date=2025-12-10

# Cách 2: Dùng day, month, year
GET /api/histories/by_parking_date?parking_id=park123&day=10&month=12&year=2025
```

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "parking_name": "Bãi xe A",
      "license_plate": "29A-12345",
      "parking_time": 2.5,
      "total_price": 50000,
      "time_in": "2025-12-10T08:00:00",
      "time_out": "2025-12-10T10:30:00"
    }
  ]
}
```

---

### 🔧 Customers (`/api/customers`)
### 📍 Coordinates (`/api/coordinates`)
### 🌍 Environments (`/api/environments`)
### 🅿️ Parking Slots (`/api/parking_slots`)
### 🚘 Parked Vehicles (`/api/parked_vehicles`)

*Chi tiết các endpoints này có thể tìm thấy trong source code tương ứng.*

---

## 📂 Cấu trúc dự án

```
parking-cloud-server/
├── app.py                      # Entry point chính
├── db.py                       # Cấu hình kết nối MongoDB
├── requirements.txt            # Dependencies
├── .env                        # Biến môi trường (không commit)
├── README.md                   # Tài liệu dự án
├── routes/                     # API routes
│   ├── __init__.py
│   ├── users.py               # API quản lý users
│   ├── parking.py             # API quản lý bãi đỗ xe
│   ├── registers.py           # API đăng ký xe
│   ├── histories.py           # API lịch sử giao dịch
│   ├── customers.py           # API khách hàng
│   ├── coordinates.py         # API tọa độ
│   ├── environments.py        # API môi trường
│   ├── parking_slots.py       # API chỗ đỗ xe
│   └── parked_vehicles.py     # API xe đang đỗ
└── __pycache__/               # Python cache files
```

## 🌐 Deploy

### Deploy lên Render.com

1. **Tạo tài khoản** tại [Render.com](https://render.com)

2. **Tạo Web Service mới**:
   - Connect repository GitHub
   - Chọn branch: `main`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`

3. **Cấu hình Environment Variables**:
   - Key: `MONGO_URI`
   - Value: `mongodb+srv://...` (connection string của bạn)

4. **Deploy**: Render sẽ tự động build và deploy

**Live URL**: `https://parking-cloud-server.onrender.com`

---

## 🧪 Test API

### Sử dụng cURL (PowerShell)

```powershell
# Test server
curl -Uri "https://parking-cloud-server.onrender.com/"

# Lấy danh sách đăng ký
curl -Uri "https://parking-cloud-server.onrender.com/api/registers/get_register_list" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"parking_id":"parking_001"}'
```

### Sử dụng Python

```python
import requests

url = "https://parking-cloud-server.onrender.com/api/registers/get_register_list"
response = requests.post(url, json={"parking_id": "parking_001"})
print(response.json())
```

---

## 📝 Database Schema

### Collections

- **users**: Thông tin người dùng
- **parkings**: Thông tin bãi đỗ xe
- **registers**: Đăng ký xe vào bãi
- **histories**: Lịch sử giao dịch đậu xe
- **customers**: Thông tin khách hàng
- **coordinates**: Tọa độ bãi xe
- **environments**: Thông tin môi trường
- **parking_slots**: Chỗ đỗ xe
- **parked_vehicles**: Xe đang đỗ

---

## 🤝 Đóng góp

Mọi đóng góp đều được chào đón! Vui lòng:

1. Fork dự án
2. Tạo branch mới (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Mở Pull Request

---

## 📄 License

Dự án này thuộc về duokhang1676. Được sử dụng cho mục đích học tập và nghiên cứu.

---

## 📞 Liên hệ

- **Repository**: [parking-cloud-server](https://github.com/duokhang1676/parking-cloud-server)
- **Owner**: duokhang1676
- **Live Server**: [https://parking-cloud-server.onrender.com](https://parking-cloud-server.onrender.com)

---

## 📌 Ghi chú

- Database: MongoDB Atlas - Collection `Smart_Parking`
- Server tự động sleep sau 15 phút không hoạt động (Render free tier)
- Khởi động lại có thể mất 30-60 giây

---

**Made with ❤️ for KLTN Project - HK1 2025-2026**
