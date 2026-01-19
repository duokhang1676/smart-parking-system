# BLE IR Sensor Receiver - Python

Chương trình Python nhận dữ liệu trạng thái cảm biến IR từ BGM220 qua BLE.

## Cài đặt

```bash
pip install -r requirements.txt
```

## Cấu hình

1. **Tìm UUID của characteristic:**
   - Chạy script lần đầu để xem danh sách UUID
   - Hoặc dùng app **nRF Connect** để scan và xem services
   - Tìm characteristic có property **Notify**

2. **Cập nhật trong code:**
   ```python
   DEVICE_NAME = "Smart Parking"  # Tên device BLE của bạn
   IR_SENSOR_CHAR_UUID = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"  # UUID từ GATT
   ```

## Chạy chương trình

```bash
python ble_ir_receiver.py
```

## Mã trạng thái

Khi cảm biến IR thay đổi, BGM220 sẽ gửi 1 byte:

| Code | Ý nghĩa | Mô tả |
|------|---------|-------|
| `0` | car_in_detected = false | Cảm biến lối vào không phát hiện xe |
| `1` | car_in_detected = true | Cảm biến lối vào phát hiện xe |
| `2` | car_out_detected = false | Cảm biến lối ra không phát hiện xe |
| `3` | car_out_detected = true | Cảm biến lối ra phát hiện xe |

## Luồng hoạt động

```
Xe vào:
  1 → Xe phát hiện ở entrance → Barrier mở (0°)
  0 → Xe đi qua → 3 giây sau barrier đóng (90°)

Xe ra:
  3 → Xe phát hiện ở exit → Barrier mở (0°)
  2 → Xe đi qua → 3 giây sau barrier đóng (90°)
```

## Kết quả mẫu

```
🔍 Scanning for BLE devices...
  Found: Smart Parking (AA:BB:CC:DD:EE:FF)
✅ Found target device: Smart Parking

🔗 Connecting to AA:BB:CC:DD:EE:FF...
✅ Connected!

🔔 Subscribing to notifications...
✅ Listening for IR sensor state changes...

[10:30:15.123] Code 1: 🚗 ENTRANCE: Car detected (sensor triggered)
  ➜ Action: Car entering, barrier should open
[10:30:18.456] Code 0: 🚗 ENTRANCE: Car cleared (sensor released)
  ➜ Action: Car passed entrance, barrier will auto-close
[10:31:22.789] Code 3: 🚗 EXIT: Car detected (sensor triggered)
  ➜ Action: Car exiting, barrier should open
[10:31:25.012] Code 2: 🚗 EXIT: Car cleared (sensor released)
  ➜ Action: Car passed exit, barrier will auto-close
```

## Lưu ý

- Windows cần Bluetooth adapter hỗ trợ BLE 4.0+
- Có thể cần chạy với quyền Administrator
- Khoảng cách tối đa ~10m (phụ thuộc môi trường)
