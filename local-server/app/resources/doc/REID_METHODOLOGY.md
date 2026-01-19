# PHƯƠNG PHÁP RE-IDENTIFICATION CHO HỆ THỐNG TRACKING ĐA CAMERA

## TÓM TẮT

Trong hệ thống giám sát bãi đỗ xe thông minh, việc theo dõi phương tiện qua nhiều camera là một thách thức quan trọng. Mỗi camera có vùng quan sát riêng biệt, dẫn đến việc cùng một phương tiện có thể được gán các ID khác nhau khi di chuyển giữa các camera. Bài viết này trình bày phương pháp Re-Identification (Re-ID) dựa trên spatial-temporal matching để đồng bộ hóa ID toàn cục cho phương tiện qua nhiều camera, kết hợp với thuật toán tracking BoT-SORT và mô hình phát hiện YOLO.

---

## 1. GIỚI THIỆU

### 1.1. Bài toán

Trong hệ thống giám sát đa camera, một phương tiện khi di chuyển từ vùng quan sát của camera này sang camera khác sẽ bị tracker gán ID mới, gây mất tính liên tục trong việc theo dõi. Điều này dẫn đến khó khăn trong việc quản lý phương tiện, xác định lịch sử di chuyển và tính toán thời gian đỗ xe.

### 1.2. Mục tiêu

Xây dựng hệ thống Re-ID cho phép:
- Duy trì ID toàn cục duy nhất cho mỗi phương tiện trong toàn bộ hệ thống
- Tự động nhận diện khi phương tiện di chuyển giữa các camera
- Hoạt động real-time với độ trễ thấp
- Đảm bảo tính chính xác cao, giảm thiểu false positive

---

## 2. PHƯƠNG PHÁP TIẾP CẬN

### 2.1. Tổng quan kiến trúc

Hệ thống được thiết kế theo mô hình multi-process với shared memory, trong đó mỗi camera hoạt động độc lập trong một process riêng biệt nhưng chia sẻ thông tin thông qua các cấu trúc dữ liệu chung (Manager.dict). Kiến trúc này đảm bảo hiệu năng cao khi xử lý song song nhiều luồng video đồng thời.

### 2.2. Thành phần cốt lõi

**Tracking cục bộ:** Mỗi camera sử dụng mô hình YOLO kết hợp thuật toán BoT-SORT để phát hiện và theo dõi phương tiện, tạo ra Local ID duy nhất trong phạm vi camera đó.

**Điểm giao (Intersection Points):** Các tọa độ được định nghĩa trước trên từng camera, đại diện cho vị trí vật lý mà phương tiện có thể đi qua khi di chuyển giữa các vùng quan sát. Điểm giao là yếu tố then chốt để hệ thống nhận biết cùng một phương tiện xuất hiện trên nhiều camera.

**Canonical Map:** Cấu trúc ánh xạ từ Local ID (camera_id, track_id) sang Global ID, được chia sẻ giữa tất cả các process thông qua Manager.dict.

---

## 3. THUẬT TOÁN RE-IDENTIFICATION

### 3.1. Nguyên lý hoạt động

Thuật toán Re-ID dựa trên giả thuyết: nếu hai camera khác nhau cùng phát hiện có phương tiện đi qua cùng một điểm giao trong khoảng thời gian ngắn (time tolerance), thì đó là cùng một phương tiện.

### 3.2. Quy trình merge ID

**Bước 1 - Thu thập observations:** Hệ thống liên tục ghi nhận thông tin (camera_id, track_id, timestamp) mỗi khi phương tiện đi qua điểm giao. Dữ liệu này được lưu trong shared dictionary với cấu trúc: `coords_by_cam[camera_id][coord_id] = (track_id, timestamp)`.

**Bước 2 - Lọc dữ liệu stale:** Để tránh merge nhầm với dữ liệu cũ, hệ thống chỉ xét các observation có timestamp trong khoảng 1 giây gần nhất (stale threshold).

**Bước 3 - Gom nhóm theo điểm giao:** Với mỗi điểm giao, hệ thống gom tất cả các observation từ các camera khác nhau.

**Bước 4 - Kiểm tra temporal proximity:** Tính median timestamp của các observation và chỉ giữ lại những observation có timestamp gần với median (trong khoảng time_tolerance = 0.5 giây). Điều này đảm bảo chỉ merge các phương tiện thực sự đi qua gần cùng thời điểm.

**Bước 5 - Merge ID:** Nếu có ít nhất 2 camera cùng quan sát được phương tiện tại điểm giao trong khoảng thời gian cho phép, hệ thống thực hiện merge:
- Nếu đã tồn tại Global ID, sử dụng ID nhỏ nhất để đảm bảo tính ổn định
- Nếu chưa có, tạo Global ID mới từ counter duy nhất
- Cập nhật Canonical Map cho tất cả các (camera_id, track_id) liên quan

### 3.3. Cơ chế Camera Anchor

Camera đầu tiên (camera_id = 0) được chỉ định là anchor camera, có quyền gán Global ID ngay lập tức khi phát hiện phương tiện mới mà không cần chờ merge. Cơ chế này đảm bảo mọi phương tiện đều có Global ID ngay từ đầu, đặc biệt quan trọng cho camera ở lối vào chính của bãi đỗ.

---

## 4. TRIỂN KHAI KỸ THUẬT

### 4.1. Đồng bộ hóa multi-process

**Shared Memory:** Sử dụng `multiprocessing.Manager` để tạo các cấu trúc dữ liệu được chia sẻ giữa các process:
- `Manager.dict()`: Lưu trữ observations, canonical map, bounding boxes
- `Manager.Lock()`: Đảm bảo thread-safe khi cập nhật shared data
- `Manager.Value()`: Counter cho Global ID
- `Barrier()`: Đồng bộ thời điểm bắt đầu của tất cả camera

**Process Communication:** Mỗi camera process liên tục cập nhật observations vào shared dictionary, không cần IPC phức tạp. Thuật toán merge chạy độc lập trong mỗi process, đảm bảo tính phân tán.

### 4.2. Xử lý real-time

Hệ thống được tối ưu cho xử lý real-time:
- Detection và tracking chạy trên GPU (CUDA)
- Thuật toán merge có độ phức tạp O(n*m) với n là số camera, m là số điểm giao
- Timeout cho stale data ngăn shared memory tăng trưởng vô hạn
- Frame processing độc lập giữa các camera, không có bottleneck tập trung

### 4.3. Xử lý biển số xe

Khi camera anchor phát hiện phương tiện mới và hệ thống OCR nhận diện được biển số, Global ID sẽ được liên kết với biển số thông qua shared license map: `license_map[global_id] = license_plate`. Thông tin này được sử dụng để quản lý danh sách xe đỗ và hiển thị trên giao diện giám sát.

---

## 5. ĐÁNH GIÁ VÀ HẠN CHẾ

### 5.1. Ưu điểm

**Đơn giản và hiệu quả:** Phương pháp không yêu cầu mô hình deep learning phức tạp cho feature extraction, chỉ dựa vào spatial-temporal matching, giúp giảm tải tính toán.

**Real-time:** Độ trễ thấp, phù hợp cho ứng dụng giám sát trực tiếp.

**Khả năng mở rộng:** Dễ dàng thêm camera mới bằng cách bổ sung process và định nghĩa điểm giao tương ứng.

### 5.2. Hạn chế

**Phụ thuộc vào điểm giao:** Chất lượng Re-ID phụ thuộc nhiều vào vị trí và số lượng điểm giao. Nếu phương tiện không đi qua điểm giao hoặc điểm giao không chính xác, hệ thống có thể gán nhầm ID.

**Tình huống đông xe:** Khi nhiều phương tiện cùng đi qua điểm giao đồng thời, thuật toán có thể merge nhầm nếu time_tolerance không được điều chỉnh phù hợp.

**Không có appearance feature:** Hệ thống không sử dụng đặc trưng ngoại hình (màu sắc, kiểu xe) để phân biệt phương tiện, chỉ dựa vào thời gian và vị trí.

### 5.3. Hướng cải tiến

Tích hợp thêm appearance-based Re-ID model (ví dụ: ResNet + Triplet Loss) để trích xuất feature vector cho mỗi phương tiện. Khi merge ID, ngoài kiểm tra temporal proximity, hệ thống có thể so sánh cosine similarity giữa các feature vector để tăng độ chính xác, đặc biệt trong trường hợp nhiều xe cùng đi qua điểm giao.

---

## 6. KẾT LUẬN

Phương pháp Re-Identification dựa trên spatial-temporal matching cung cấp giải pháp hiệu quả cho bài toán tracking đa camera trong hệ thống quản lý bãi đỗ xe. Với kiến trúc multi-process và shared memory, hệ thống đạt được hiệu năng real-time cao. Mặc dù có những hạn chế về phụ thuộc vào điểm giao và khả năng xử lý tình huống đông xe, phương pháp này vẫn phù hợp cho môi trường bãi đỗ có cấu trúc rõ ràng và mật độ xe vừa phải. Hướng phát triển tương lai có thể tích hợp thêm appearance features để nâng cao độ chính xác và khả năng xử lý các tình huống phức tạp.

---

**Tài liệu tham khảo:**
- Bewley, A., et al. (2016). Simple Online and Realtime Tracking. ICIP.
- Aharon, N., et al. (2022). BoT-SORT: Robust Associations Multi-Pedestrian Tracking. arXiv.
- Ristani, E., & Tomasi, C. (2018). Features for Multi-Target Multi-Camera Tracking and Re-Identification. CVPR.
