# Simple Parking System (Tương tự Arduino)

Phiên bản đơn giản hóa, chỉ giữ lại các chức năng cơ bản giống Arduino.

## 🎯 So sánh với Arduino

| Tính năng | Arduino | BGM220 |
|-----------|---------|--------|
| IR_IN | Pin 2 | PC0 |
| IR_OUT | Pin 3 | PC2 |
| SERVO_IN | Pin 4 | PC1 |
| SERVO_OUT | Pin 5 | PC3 |
| LCD 16x2 | I2C 0x27 | I2C 0x27 |
| OLED SSD1306 | I2C 0x3C | I2C 0x3C |
| Communication | Serial | Serial (UART) |
| Flame sensor | ❌ Removed | ❌ Removed |
| DHT11 | ❌ Removed | ❌ Removed |
| Light sensor | ❌ Removed | ❌ Removed |
| BLE | ❌ Not used | ❌ Not used |

## 📋 Chức năng

### 1. IR Sensors
- Phát hiện xe vào/ra
- Gửi qua Serial:
  - `car_in:1` - Xe phát hiện ở entrance
  - `car_in:0` - Xe cleared entrance
  - `car_out:1` - Xe phát hiện ở exit
  - `car_out:0` - Xe cleared exit

### 2. Servo Control
Nhận lệnh từ PC qua Serial:
- `1` - Mở servo entrance (0°)
- `0` - Đóng servo entrance sau 3s (90°)
- `3` - Mở servo exit (0°)
- `2` - Đóng servo exit sau 3s (90°)

### 3. LCD Display (16x2)
- Dòng 1: `<=====    =====>`
- Dòng 2: Text hướng dẫn (nhận từ PC)
- Ví dụ: `D0-C0    B0-A0`

### 4. OLED Display (128x64)
Hiển thị slot parking:
```
  AREA   OCCUPY/TOTAL
   A         2 / 5
   B         3 / 5
   C         1 / 5
   D         4 / 5
  TOTAL      10 / 20
```

Nhận dữ liệu từ PC: `2,3,1,4,10`

## 🔧 Build & Flash

### BGM220:
1. Thay `app.c` bằng `app_simple.c`:
   ```bash
   # Backup old
   mv app.c app_old.c
   mv app_simple.c app.c
   ```

2. Build trong Simplicity Studio

3. Flash lên board

### Python Controller:
```bash
cd python_receiver
pip install -r requirements_serial.txt
python serial_parking_receiver.py
```

## 🚀 Test

### 1. Monitor Mode (Chỉ lắng nghe)
```bash
python serial_parking_receiver.py
# Chọn option 2
```

Kết quả:
```
[10:30:15] 🚗 ENTRANCE: Car detected
  ➜ Action: Send '1' to open barrier
📤 Sent: 1
[10:30:18] 🚗 ENTRANCE: Car cleared
  ➜ Action: Send '0' to close barrier after 3s
📤 Sent: 0
```

### 2. Interactive Mode (Gửi lệnh thủ công)
```bash
python serial_parking_receiver.py
# Chọn option 3
```

Commands:
```
📤 Command: 1              # Open entrance
📤 Command: D0-C0    B0-A0 # Set LCD text
📤 Command: 2,3,1,4,10     # Update slots
```

### 3. Demo Mode (Test tự động)
```bash
python serial_parking_receiver.py
# Chọn option 1
```

## 📡 Serial Protocol

### BGM220 → PC (Events)
```
car_in:1\n    # Car detected at entrance (IR LOW)
car_in:0\n    # Car cleared entrance (IR HIGH)
car_out:1\n   # Car detected at exit (IR LOW)
car_out:0\n   # Car cleared exit (IR HIGH)
```

### PC → BGM220 (Commands)
```
0\n                 # Close servo_in after 3s
1\n                 # Open servo_in immediately
2\n                 # Close servo_out after 3s
3\n                 # Open servo_out immediately
2,3,1,4,10\n        # Update slot data
D0-C0    B0-A0\n    # LCD text
```

## 🎛️ Configuration

### COM Port (Windows)
```python
controller = ParkingSystemController('COM3')  # Manual
```

### Baud Rate
Default: `115200` (giống Simplicity Studio console)

### I2C Address
- LCD: `0x27`
- OLED: `0x3C`

## 🐛 Troubleshooting

**Không tìm thấy COM port:**
- Mở Device Manager → Ports (COM & LPT)
- Tìm "J-Link" hoặc "Silicon Labs"
- Dùng port đó trong code

**Không nhận được dữ liệu:**
- Kiểm tra baud rate (115200)
- Mở Simplicity Studio console xem có dữ liệu không
- Thử unplug/replug USB

**Servo không hoạt động:**
- Kiểm tra nối chân PC1, PC3
- Servo cần nguồn ngoài 5V
- Kiểm tra ground chung

## 📝 Notes

- Code đơn giản hơn, không dùng BLE
- Tương thích với workflow Arduino hiện có
- Có thể chạy song song với Python controller
- Serial là UART, không phải USB CDC (nhanh hơn)
