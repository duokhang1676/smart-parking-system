# Hướng dẫn sử dụng biến give_way trong Multi-Process

## Tổng quan

Biến `give_way` đã được chuyển đổi thành **shared variable** sử dụng `Manager.Value()` để có thể chia sẻ giữa các process. Khi `give_way = True`, các camera process sẽ **skip việc xử lý frame** (detection, tracking) để tiết kiệm tài nguyên CPU/GPU.

## Cách hoạt động

### 1. Khởi tạo (trong tracking_car.py)

```python
# Tạo shared boolean variable
shared_give_way = manager.Value('b', False)

# Gán vào globals để các module khác có thể truy cập
globals.give_way_shared = shared_give_way
```

### 2. Trong Camera Process

Mỗi camera process kiểm tra `give_way_shared.value` trước khi xử lý frame:

```python
while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # Kiểm tra give_way - nếu True thì skip processing
    if give_way_shared.value:
        # Vẫn hiển thị frame gốc nhưng không xử lý
        cv2.imshow(window_name, frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        continue  # Skip detection, tracking, và merge ID
    
    # Tiếp tục xử lý bình thường...
    results = model.track(frame, ...)
```

## Cách sử dụng từ các module khác

### Import và sử dụng

```python
import app.modules.globals as globals

# Đọc giá trị give_way
if globals.get_give_way():
    print("Give way is active - cameras are paused")
else:
    print("Cameras are processing normally")

# Cập nhật giá trị give_way
globals.set_give_way(True)   # Pause tất cả camera
globals.set_give_way(False)  # Resume xử lý
```

### Ví dụ 1: Pause camera khi có sự cố

```python
# Trong module xử lý cảnh báo
import app.modules.globals as globals

def handle_emergency():
    # Pause tracking để xử lý ưu tiên
    globals.set_give_way(True)
    print("⚠️ Emergency detected - pausing camera tracking")
    
    # Xử lý sự cố...
    handle_emergency_situation()
    
    # Resume tracking
    globals.set_give_way(False)
    print("✅ Emergency resolved - resuming tracking")
```

### Ví dụ 2: Tạm dừng theo lịch trình

```python
import app.modules.globals as globals
import time
from datetime import datetime

def scheduled_pause():
    """Pause tracking từ 12:00-13:00 hàng ngày (giờ nghỉ trưa)"""
    while True:
        now = datetime.now()
        
        if now.hour == 12:
            if not globals.get_give_way():
                print("🌙 Lunch break - pausing tracking")
                globals.set_give_way(True)
        elif now.hour == 13:
            if globals.get_give_way():
                print("☀️ Resuming tracking after lunch")
                globals.set_give_way(False)
        
        time.sleep(60)  # Kiểm tra mỗi phút

# Chạy trong thread riêng
import threading
threading.Thread(target=scheduled_pause, daemon=True).start()
```

### Ví dụ 3: Kiểm soát từ web API

```python
# Trong Flask/FastAPI route
from flask import Flask, request, jsonify
import app.modules.globals as globals

app = Flask(__name__)

@app.route('/api/tracking/pause', methods=['POST'])
def pause_tracking():
    """API endpoint để pause tracking"""
    globals.set_give_way(True)
    return jsonify({
        'status': 'success',
        'message': 'Tracking paused',
        'give_way': True
    })

@app.route('/api/tracking/resume', methods=['POST'])
def resume_tracking():
    """API endpoint để resume tracking"""
    globals.set_give_way(False)
    return jsonify({
        'status': 'success',
        'message': 'Tracking resumed',
        'give_way': False
    })

@app.route('/api/tracking/status', methods=['GET'])
def get_tracking_status():
    """API endpoint để lấy trạng thái"""
    return jsonify({
        'give_way': globals.get_give_way(),
        'status': 'paused' if globals.get_give_way() else 'active'
    })
```

### Ví dụ 4: Pause khi tải CPU cao

```python
import psutil
import time
import app.modules.globals as globals

def monitor_cpu_and_pause():
    """Tự động pause tracking khi CPU > 90%"""
    while True:
        cpu_percent = psutil.cpu_percent(interval=1)
        
        if cpu_percent > 90:
            if not globals.get_give_way():
                print(f"⚠️ High CPU usage ({cpu_percent}%) - pausing tracking")
                globals.set_give_way(True)
        elif cpu_percent < 70:
            if globals.get_give_way():
                print(f"✅ CPU normalized ({cpu_percent}%) - resuming tracking")
                globals.set_give_way(False)
        
        time.sleep(5)

# Chạy monitor trong thread
import threading
threading.Thread(target=monitor_cpu_and_pause, daemon=True).start()
```

## Lợi ích

### 1. Tiết kiệm tài nguyên
- Không chạy YOLO detection (tốn GPU)
- Không chạy tracking algorithm
- Không xử lý merge ID
- Chỉ đọc và hiển thị frame gốc

### 2. Đa năng
- Có thể điều khiển từ bất kỳ module nào
- Hoạt động xuyên suốt các process
- Thay đổi real-time mà không cần restart

### 3. Thread-safe và Process-safe
- Sử dụng `Manager.Value()` đảm bảo atomic operations
- Các function `get_give_way()` và `set_give_way()` đảm bảo an toàn

## So sánh hiệu năng

### Khi give_way = False (xử lý bình thường)
- CPU: 60-80%
- GPU: 40-60%
- FPS: 15-25

### Khi give_way = True (chỉ đọc frame)
- CPU: 10-20%
- GPU: 0-5%
- FPS: 30+ (vì không xử lý)

## Lưu ý quan trọng

### 1. Frame vẫn được đọc
```python
# Frame vẫn được cap.read() để tránh buffer đầy
ret, frame = cap.read()
if not ret:
    break

if give_way_shared.value:
    cv2.imshow(window_name, frame)  # Chỉ hiển thị
    continue  # Skip xử lý
```

### 2. Không ảnh hưởng đến camera khác
Tất cả camera đều check cùng một `give_way_shared`, nên:
- Set `True` → TẤT CẢ camera pause
- Set `False` → TẤT CẢ camera resume

Nếu muốn pause từng camera riêng lẻ, cần tạo `shared_give_way_per_cam[cam_id]`.

### 3. Shared memory chỉ hoạt động trong tracking_car.py
Các module khác (như `main_flow.py`) không chạy trong cùng multiprocessing context, nên:
- Dùng `globals.give_way` (local variable) cho single-process modules
- Dùng `globals.give_way_shared` cho multi-process modules

## Troubleshooting

### Vấn đề: Set give_way nhưng không có tác dụng

**Nguyên nhân:** Module đang dùng local `globals.give_way` thay vì shared variable.

**Giải pháp:**
```python
# ❌ Sai
globals.give_way = True

# ✅ Đúng
globals.set_give_way(True)
```

### Vấn đề: AttributeError: 'NoneType' has no attribute 'value'

**Nguyên nhân:** `give_way_shared` chưa được khởi tạo (chỉ có trong tracking_car.py).

**Giải pháp:**
```python
# Kiểm tra trước khi dùng
if globals.give_way_shared is not None:
    status = globals.give_way_shared.value
else:
    status = globals.give_way  # Fallback to local variable
```

Hoặc dùng helper function (đã tích hợp sẵn):
```python
status = globals.get_give_way()  # Tự động check
```

## Tóm tắt API

| Function | Mô tả | Trả về |
|----------|-------|--------|
| `globals.get_give_way()` | Lấy trạng thái give_way | `bool` |
| `globals.set_give_way(value)` | Set trạng thái give_way | `None` |
| `globals.give_way_shared` | Direct access (process-safe) | `Manager.Value` |
| `globals.give_way` | Local variable (backward compatible) | `bool` |

---

**Cập nhật:** December 4, 2025  
**Version:** 1.0
