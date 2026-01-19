# REID ALGORITHM - Thuật toán Tracking và Đồng bộ ID giữa các Camera

## 📋 Tổng quan

Tài liệu này mô tả chi tiết cách hệ thống tracking xe và đồng bộ ID toàn cục (Re-Identification) giữa nhiều camera trong hệ thống quản lý bãi đỗ xe.

## 🎯 Mục đích

- **Tracking**: Theo dõi xe liên tục trong từng camera
- **Re-ID**: Đồng bộ ID của cùng một xe khi nó di chuyển qua nhiều camera
- **Global ID**: Tạo ID toàn cục duy nhất cho mỗi xe trong toàn hệ thống

---

## 🏗️ Kiến trúc Hệ thống

### 1. Cấu trúc Multi-Process

Hệ thống sử dụng **multiprocessing** để chạy song song nhiều camera:

```python
# Mỗi camera chạy trong một process riêng
for idx, (video_path, window_name, intersections_file, slot_file) in enumerate(camera_configs):
    p = Process(target=process_video, args=(...))
    p.start()
```

### 2. Shared Memory

Sử dụng `Manager` để chia sẻ dữ liệu giữa các process:

```python
manager = Manager()

# Shared dictionaries
coords_by_cam = [manager.dict() for _ in range(num_cams)]  # Tọa độ xe qua điểm giao
canonical_map = manager.dict()                              # Map local ID -> global ID
shared_bbox_by_cam = manager.dict()                         # Bounding boxes
shared_license_map = manager.dict()                         # Map global ID -> biển số

# Shared values
lock = manager.Lock()                                       # Lock cho thread-safe
next_canonical = manager.Value('i', 1)                      # Counter cho global ID
```

### 3. Barrier Synchronization

Đồng bộ để tất cả camera bắt đầu cùng lúc:

```python
start_barrier = Barrier(len(VIDEO_SOURCES))

# Trong mỗi process
start_barrier.wait()  # Chờ tất cả camera ready
```

---

## 🔍 Tracking trong từng Camera

### 1. Model và Tracker

Sử dụng **YOLO** + **BoT-SORT** tracker:

```python
model = YOLO(model_path, verbose=False).to("cuda")

# Tracking
results = model.track(
    frame,
    persist=True,          # Giữ ID giữa các frame
    conf=0.6,              # Confidence threshold
    verbose=False,
    tracker=TRACKER_PATH   # botsort.yaml
)
```

### 2. Trích xuất thông tin

Từ kết quả tracking, lấy:
- **ID cục bộ** (local ID): ID do tracker gán trong camera
- **Bounding box**: Tọa độ xe (x1, y1, x2, y2)

```python
if boxes.id is not None:
    ids = boxes.id.int().tolist()          # Local tracking IDs
    xyxy = boxes.xyxy.tolist()             # Bounding boxes
    
    for i, box in enumerate(xyxy):
        obj_id = ids[i]                    # Local ID
        x1, y1, x2, y2 = map(int, box)
```

---

## 🌐 Re-Identification (Đồng bộ ID toàn cục)

### 1. Điểm giao (Intersection Points)

Các điểm giao là **tọa độ được đánh dấu trước** trên các camera, nơi xe sẽ đi qua khi di chuyển giữa vùng nhìn của các camera.

#### Cấu trúc file YAML:

```yaml
# app/resources/coordinates/reid-data/0.yml
- coordinate:
  - 84
  - 382
  id: A0
- coordinate:
  - 42
  - 385
  id: A1
```

#### Công cụ đánh dấu điểm:

File `coordinates.py` cung cấp giao diện GUI để đánh dấu điểm giao:

```python
# Chạy tool
python app/resources/coordinates/reid-data/coordinates.py

# Thao tác:
# - Click chuột: Đánh dấu điểm
# - B, C, D: Đổi nhóm ID (A0, A1... -> B0, B1...)
# - BACKSPACE: Xóa điểm cuối
# - ESC: Xóa tất cả
# - ENTER: Lưu vào file .yml
```

### 2. Phát hiện xe qua điểm giao

Kiểm tra xem bounding box của xe có chứa điểm giao không:

```python
coords_trackids = {}  # Dict lưu {coord_id: (track_id, timestamp)}

for item in intersections_coords:
    cid = item['id']           # ID điểm giao (vd: "A0")
    x, y = item["coordinate"]  # Tọa độ điểm giao
    
    # Kiểm tra xe có đi qua điểm này không
    if x1 <= x <= x2 and y1 <= y <= y2:
        coords_trackids[cid] = (int(obj_id), time.time())

# Cập nhật vào shared memory
for k, v in coords_trackids.items():
    coords_by_cam[cam_id][k] = v
```

### 3. Thuật toán Merge ID

Hàm `update_mappings_atomic()` thực hiện merge ID:

#### **Bước 1: Thu thập dữ liệu**

```python
# Lấy snapshot từ tất cả camera
snapshots = {}
for cam in cams:
    raw = dict(coords_by_cam[cam])
    # Lọc dữ liệu cũ (stale > 1.0s)
    s = {k: v for k, v in raw.items() if (now - v[1]) <= stale}
    snapshots[cam] = s
```

#### **Bước 2: Gom nhóm observations**

```python
# Với mỗi điểm giao
for cid in coord_ids:
    obs = []
    # Gom tất cả (camera, track_id, timestamp) nhìn thấy điểm này
    for cam in cams:
        if cid in snapshots[cam]:
            tid, ts = snapshots[cam][cid]
            obs.append((cam, int(tid), ts))
```

#### **Bước 3: Lọc theo thời gian**

```python
# Chỉ merge nếu các camera thấy xe GẦN CÙNG THỜI ĐIỂM (tolerance = 0.5s)
times = [ts for (_, _, ts) in obs]
median_ts = sorted(times)[len(times)//2]

close = [(cam, tid, ts) for (cam, tid, ts) in obs 
         if abs(ts - median_ts) <= time_tol]
```

#### **Bước 4: Merge ID**

```python
with lock:
    # Kiểm tra đã có canonical ID chưa
    existing_canons = []
    for cam, tid, _ in close:
        key = f"c{cam}_{tid}"
        c = canonical_map.get(key)
        if c is not None:
            existing_canons.append(c)
    
    # Chọn canonical ID
    if existing_canons:
        chosen_canon = min(existing_canons)  # Ưu tiên ID nhỏ nhất
    else:
        chosen_canon = int(next_canonical.value)
        next_canonical.value += 1
    
    # Gán canonical ID cho tất cả track liên quan
    for cam, tid, _ in close:
        key = f"c{cam}_{tid}"
        canonical_map[key] = chosen_canon
```

### 4. Camera Anchor (Camera chính)

**Camera 0** được chỉ định là **anchor camera** - camera chính gán ID toàn cục ngay lập tức:

```python
if cam_id == 0:  # Camera 0 là ANCHOR
    key = f"c{cam_id}_{obj_id}"
    with lock:
        if key not in canonical_map:
            # Gán Global ID mới
            canonical_map[key] = int(next_canonical.value)
            next_canonical.value += 1
            
            global_id = canonical_map[key]
            
            # Gắn biển số nếu có
            new_license_plate = get_new_license_plate_from_file()
            if new_license_plate != "":
                license_shared[global_id] = new_license_plate
                
                # Tạo vehicle record
                parked_vehicles['list'].append({
                    'user_id': globals.new_user_id,
                    'customer_type': 'customer',
                    'time_in': time_in.isoformat(),
                    'license_plate': new_license_plate,
                    'slot_name': "",
                    'num_slot': 0
                })
```

---

## 📊 Hiển thị và Tracking Label

### 1. Lấy Global ID

```python
key = f"c{cam_id}_{obj_id}"
global_id = canonical_map.get(key)
```

### 2. Hiển thị label

```python
# Format: "ID:<local_id>/<global_id>"
label = f"ID:{obj_id}/{int(global_id)}" if global_id else f"ID {obj_id}/-"

cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)
cv2.putText(frame, label, (x1 + 3, y1 - 3),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
```

### 3. Ví dụ hiển thị:

```
Camera 1: ID:5/23  <- Local ID = 5, Global ID = 23
Camera 2: ID:12/23 <- Local ID = 12, Global ID = 23 (cùng xe)
```

---

## 🎛️ Tham số cấu hình

### 1. Trong code

```python
time_tol = 0.5   # Dung sai thời gian (giây) để merge ID
stale = 1.0      # Thời gian tối đa dữ liệu còn hợp lệ (giây)
conf = 0.6       # Confidence threshold cho detection
```

### 2. Trong .env

```env
TRACKING_CAMERA="['rtsp://camera1', 'rtsp://camera2']"
TRACKING_CAMERA_ID=0,1
PARKING_ID=parking_001
```

### 3. Tracker config

File `app/resources/tracker/botsort.yaml` chứa cấu hình BoT-SORT tracker.

---

## 🔄 Quy trình hoạt động

### Flowchart tổng quan:

```
┌─────────────────┐
│  Camera 0, 1, 2 │
│   (Processes)   │
└────────┬────────┘
         │
         ├─► YOLO Detection
         │
         ├─► BoT-SORT Tracking ──► Local ID (1, 2, 3...)
         │
         ├─► Phát hiện xe qua điểm giao
         │        │
         │        ├─► coords_by_cam[cam][coord_id] = (track_id, time)
         │        │
         │        └─► update_mappings_atomic()
         │                    │
         │                    ├─► Gom observations từ tất cả camera
         │                    │
         │                    ├─► Lọc theo thời gian (time_tol)
         │                    │
         │                    └─► Merge ID ──► canonical_map
         │
         └─► Hiển thị: ID:<local>/<global>
```

### Chi tiết từng bước:

1. **Frame đầu vào** từ mỗi camera
2. **YOLO** detect xe → bounding boxes
3. **BoT-SORT** tracking → gán Local ID
4. **Kiểm tra điểm giao**: Xe có đi qua điểm nào không?
5. **Lưu vào shared memory**: `coords_by_cam[cam_id][coord_id] = (track_id, timestamp)`
6. **Merge ID**: Hàm `update_mappings_atomic()` chạy và merge ID
7. **Lấy Global ID**: Từ `canonical_map[f"c{cam}_{local_id}"]`
8. **Hiển thị**: Vẽ bbox và label với Global ID

---

## 📝 Ví dụ cụ thể

### Tình huống: Xe di chuyển từ Camera 0 sang Camera 1

#### **Thời điểm T1** - Xe ở Camera 0:
```
Camera 0:
- Local ID: 5
- Bounding box chứa điểm A0 (84, 382)
- coords_by_cam[0]["A0"] = (5, T1)

Canonical Map:
- "c0_5" = 23  (Camera 0 là anchor, gán global ID = 23 ngay)
```

#### **Thời điểm T2** (sau 0.3s) - Xe xuất hiện ở Camera 1:
```
Camera 1:
- Local ID: 12 (tracker gán ID mới)
- Bounding box chứa điểm A0 (534, 373)  [cùng khu vực nhưng khác tọa độ]
- coords_by_cam[1]["A0"] = (12, T2)

Merge Algorithm:
- Phát hiện 2 camera cùng thấy điểm "A0" trong khoảng thời gian 0.3s < 0.5s
- Camera 0: (track_id=5, time=T1)
- Camera 1: (track_id=12, time=T2)
- Existing canon: "c0_5" = 23
- Merge: "c1_12" = 23

Canonical Map:
- "c0_5" = 23
- "c1_12" = 23  ← Xe được nhận diện là cùng 1 xe
```

#### **Hiển thị:**
```
Camera 0: ID:5/23
Camera 1: ID:12/23  ← Cùng Global ID = 23
```

---

## 🔧 Cách thiết lập hệ thống

### Bước 1: Chuẩn bị điểm giao

```bash
# Chạy tool đánh dấu cho từng camera
python app/resources/coordinates/reid-data/coordinates.py
```

**Lưu ý quan trọng:**
- Các điểm giao phải nằm ở **vị trí trùng nhau giữa các camera** (cùng khu vực vật lý)
- Đặt tên ID giống nhau giữa các camera (vd: A0, A1, A2)
- Nên đặt điểm ở **lối đi chính** mà xe thường xuyên đi qua

### Bước 2: Cấu hình camera

```env
# .env
TRACKING_CAMERA="['rtsp://192.168.1.100', 'rtsp://192.168.1.101']"
TRACKING_CAMERA_ID=0,1
```

### Bước 3: Chạy hệ thống

```bash
python app/modules/tracking_car.py
```

### Bước 4: Kiểm tra và điều chỉnh

- Quan sát xem các ID có được merge đúng không
- Điều chỉnh `time_tol` nếu merge không chính xác:
  - Tăng lên nếu xe di chuyển chậm (0.7 - 1.0s)
  - Giảm xuống nếu có nhiều xe cùng lúc (0.3 - 0.5s)
- Thêm/bớt điểm giao nếu cần

---

## ⚠️ Lưu ý và Best Practices

### 1. Đặt điểm giao hiệu quả

✅ **NÊN:**
- Đặt ở lối đi chính, nơi xe chắc chắn đi qua
- Đặt nhiều điểm (3-5 điểm) trên mỗi lối đi
- ID điểm phải giống nhau giữa các camera

❌ **KHÔNG NÊN:**
- Đặt ở vùng bị che khuất
- Đặt điểm quá gần nhau (< 50px)
- Đặt ở chỗ xe có thể đi vòng tránh

### 2. Tham số merge

```python
time_tol = 0.5   # Tối ưu cho xe chạy vừa phải
stale = 1.0      # Xóa dữ liệu cũ hơn 1s
```

**Điều chỉnh theo tình huống:**
- Xe chạy nhanh: `time_tol = 0.3`
- Xe chạy chậm: `time_tol = 0.8`
- Nhiều xe cùng lúc: giảm `time_tol`, tăng số điểm giao

### 3. Camera Anchor

- Camera 0 nên là camera ở **lối vào chính**
- Đảm bảo camera anchor hoạt động ổn định
- Nếu camera anchor lỗi, toàn hệ thống sẽ bị ảnh hưởng

### 4. Performance

```python
# Sử dụng GPU
model = YOLO(model_path).to("cuda")

# Giảm resolution nếu cần
frame = cv2.resize(frame, (640, 640))

# Tăng confidence threshold nếu quá nhiều false positives
conf = 0.7  # thay vì 0.6
```

---

## 🐛 Troubleshooting

### Vấn đề 1: ID không được merge

**Nguyên nhân:**
- Điểm giao không trùng khớp giữa các camera
- `time_tol` quá nhỏ

**Giải pháp:**
```python
# Tăng time_tol
time_tol = 0.8

# Kiểm tra điểm giao
print(snapshots)  # Debug trong update_mappings_atomic()
```

### Vấn đề 2: ID bị merge nhầm

**Nguyên nhân:**
- Nhiều xe đi qua cùng lúc
- `time_tol` quá lớn

**Giải pháp:**
```python
# Giảm time_tol
time_tol = 0.3

# Thêm nhiều điểm giao hơn để phân biệt
```

### Vấn đề 3: Camera không sync

**Nguyên nhân:**
- Barrier timeout

**Giải pháp:**
```python
# Kiểm tra log
print(f"Camera {cam_id} ready. Waiting for others...")

# Tăng timeout
start_barrier.wait(timeout=30)
```

---

## 📈 Monitoring và Debug

### 1. Log merge events

```python
# Trong update_mappings_atomic()
mapped = ", ".join([f"(cam{cam}:{tid})" for cam, tid, _ in close])
print(f"[MERGE] coord {cid}: {mapped} -> canon {chosen_canon}")
```

### 2. Visualize điểm giao

```python
# Vẽ điểm giao lên frame
for item in intersections_coords:
    cv2.circle(frame, (item['coordinate']), 5, (0, 0, 255), -1)
    cv2.putText(frame, item['id'], item['coordinate'], 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
```

### 3. Export canonical map

```python
# Debug: In ra mapping
for key, value in canonical_map.items():
    print(f"{key} -> {value}")
```

---

## 📚 Tham khảo

### Models và Trackers

- **YOLO**: [Ultralytics YOLOv11](https://github.com/ultralytics/ultralytics)
- **BoT-SORT**: [ByteTrack+SORT+OCSORT](https://github.com/NirAharon/BoT-SORT)

### Thuật toán

- **Re-ID**: Re-Identification based on spatial-temporal matching
- **Multi-camera tracking**: Merge IDs across camera views

---

## 📞 Liên hệ

Nếu có vấn đề về thuật toán Re-ID, vui lòng:
1. Kiểm tra log và debug output
2. Xem lại cấu hình điểm giao
3. Điều chỉnh tham số `time_tol` và `stale`

---

**Cập nhật:** December 4, 2025  
**Version:** 1.0
