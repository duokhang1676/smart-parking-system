import cv2
from flask import json
from ultralytics import YOLO
from multiprocessing import Process, set_start_method, Value, Manager
import time
from app.modules.utils import read_yaml, write_yaml_file, speech_text, get_parked_vehicles_from_file, save_parked_vehicles_to_file, get_new_license_plate_from_file, save_new_license_plate_to_file, update_screen_display
from app.modules import globals
import threading
from multiprocessing import Barrier
from app.modules.cloud_api import get_coordinates, update_parked_vehicle_list, update_parking_lot
import os
import dotenv
import ast
import datetime
import requests
import paho.mqtt.client as mqtt
dotenv.load_dotenv()
# CONSTANTS
PARKING_ID = os.getenv("PARKING_ID")
VIDEO_SOURCES = ast.literal_eval(os.getenv("TRACKING_CAMERA"))
TRACKER_PATH = "app/resources/tracker/"+os.getenv("TRACKER_CONFIG")+".yaml"
DETECT_MODEL_PATH = os.getenv("DETECT_MODEL_PATH")
REID_COORDS_PATH = "app/resources/coordinates/reid-data/"
SLOT_COORDS_PATH = "app/resources/coordinates/slot-data/"
CLOUDINARY_UPLOAD_PRESET = os.getenv("UPLOAD_PRESET")
CLOUDINARY_UPLOAD_URL = os.getenv("CLOUDINARY_UPLOAD_URL")
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC_SHOW_VEHICLE = "parking/vehicle/show"

def publish_vehicle_image_url(image_url):
    """
    Publish image URL to MQTT topic parking/vehicle/show
    """
    try:
        client = mqtt.Client()
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        time.sleep(0.5)  # Đợi kết nối hoàn tất
        
        result = client.publish(MQTT_TOPIC_SHOW_VEHICLE, image_url, qos=1)
        result.wait_for_publish()
        
        client.loop_stop()
        client.disconnect()
        
        print(f"[MQTT] ✅ Published image URL to {MQTT_TOPIC_SHOW_VEHICLE}")
        print(f"[MQTT] URL: {image_url}")
        return True
    except Exception as e:
        print(f"[MQTT] ❌ Failed to publish: {e}")
        return False

def update_mappings_atomic(coords_by_cam, lock, canonical_map, next_canonical, time_tol=0.5, stale=1.0):
    """
    Hàm này dùng để MERGE ID giữa nhiều camera → tạo thành ID toàn cục (global canonical ID).
    (Giữ nguyên logic cũ)
    """
    now = time.time()

    # snapshot cleaned: chỉ giữ dữ liệu không bị quá hạn "stale"
    snapshots = {}
    latest_ts = {}

    cams = range(0, len(coords_by_cam))

    for cam in cams:
        raw = dict(coords_by_cam[cam])  # copy từ memory shared dict -> local dict

        # Lọc dữ liệu cũ (stale)
        s = {k: v for k, v in raw.items() if v and (now - v[1]) <= stale}
        snapshots[cam] = s

        # Lưu timestamp cuối cùng của từng track
        latest_ts[cam] = {}
        for _, (tid, ts) in s.items():
            if tid is not None:
                latest_ts[cam][tid] = max(latest_ts[cam].get(tid, 0.0), ts)

    # Lấy danh sách TẤT CẢ coord_id từng xuất hiện ở bất kỳ camera nào
    coord_ids = set()
    for cam in cams:
        coord_ids.update(snapshots[cam].keys())

    # Bắt đầu merge
    with lock:
        for cid in coord_ids:
            obs = []
            # Gom tất cả (camera, track_id, timestamp) nhìn thấy coord_id này
            for cam in cams:
                if cid in snapshots[cam]:
                    tid, ts = snapshots[cam][cid]
                    if tid is not None:
                        obs.append((cam, int(tid), ts))

            if len(obs) < 2:
                continue  # Chỉ 1 camera thấy → không merge được

            # Lọc theo thời gian (camera phải thấy gần cùng thời điểm)
            times = [ts for (_, _, ts) in obs]
            median_ts = sorted(times)[len(times)//2]

            close = [(cam, tid, ts) for (cam, tid, ts) in obs if abs(ts - median_ts) <= time_tol]
            if len(close) < 2:
                continue

            # Kiểm tra xem có camera nào đã có canonical_id chưa
            existing_canons = []
            for cam, tid, _ in close:
                key = f"c{cam}_{tid}"
                c = canonical_map.get(key)
                if c is not None:
                    existing_canons.append((cam, tid, int(c)))

            # Chọn canonical id
            if existing_canons:
                # Ưu tiên canonical id nhỏ nhất (để ổn định)
                chosen_canon = min(c for (_, _, c) in existing_canons)
            else:
                # Tạo canonical mới
                chosen_canon = int(next_canonical.value)
                next_canonical.value += 1

            # Gán chung canonical id cho tất cả track liên quan
            for cam, tid, _ in close:
                key = f"c{cam}_{tid}"
                canonical_map[key] = chosen_canon

            # Log merge cho dễ debug
            #mapped = ", ".join([f"(cam{cam}:{tid})" for cam, tid, _ in close])
            #print(f"[MERGE] coord {cid}: {mapped} -> canon {chosen_canon}")


def process_video(video_path, window_name, model_path, cam_id,
                  coords_by_cam, lock, canonical_map, next_canonical,
                  intersections_file, slot_file, start_barrier,
                  bbox_shared, license_shared, search_vehicle_shared, searched_vehicle_uploaded):
    """
    Hàm xử lý video cho từng camera (chạy song song bằng process).

    Thay đổi quan trọng:
    - Truyền explicit shared dict `bbox_shared`, `license_shared`, `search_vehicle_shared` (manager.dict) từ main process.
      Tránh việc child process cập nhật module `globals` cục bộ (không cùng memory với main khi dùng 'spawn').
    - searched_vehicle_uploaded: shared dict để đảm bảo chỉ upload 1 lần.
    """
    print(f"[Camera {cam_id}] Loading YOLO model...")
    try:
        # NOTE: nếu không muốn ép dùng cuda, có thể bỏ `.to("cuda")` nếu model không hỗ trợ
        model = YOLO(model_path, verbose=False).to("cuda")
        print(f"[Camera {cam_id}] Model loaded on CUDA")
    except Exception as e:
        # fallback nếu không có GPU / lỗi
        print(f"[Camera {cam_id}] CUDA not available, using CPU: {e}")
        model = YOLO(model_path, verbose=False)

    print(f"[Camera {cam_id}] Opening video source...")
    cap = cv2.VideoCapture(video_path, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print(f"[ERROR] Camera {cam_id} failed to open {video_path}")
        return

    # --- CHỜ TẤT CẢ CAMERA CÙNG SẴN SÀNG ---
    print(f"Camera {cam_id} ready. Waiting for others...")
    try:
        start_barrier.wait()
    except Exception as e:
        print(f"Camera {cam_id} barrier wait error: {e}")
    print(f"Camera {cam_id} started.")

    # Load điểm giao trên hình (các vị trí bạn đánh dấu)
    intersections_coords = read_yaml(intersections_file)
    
    # Lưu search_vehicle trước đó để detect thay đổi
    previous_search_vehicle = ""

    while True:
        coords_trackids = {}

        ret, frame = cap.read()
        if not ret:
            break

        # Kiểm tra nếu có yêu cầu tìm kiếm xe
        search_vehicle = search_vehicle_shared.get('value', '')
        
        # Nếu search_vehicle thay đổi, reset flag uploaded
        # Normalize to uppercase để so sánh case-insensitive với license plates
        search_vehicle = search_vehicle.upper() if search_vehicle else ""
        
        # Lưu frame gốc CHỈ KHI đang tìm kiếm (tiết kiệm tài nguyên)
        frame_original = frame.copy() if search_vehicle != "" else None
        
        if search_vehicle != previous_search_vehicle:
            if previous_search_vehicle != "":
                # Xóa flag của search cũ (dùng pop để tránh KeyError nếu đã bị xóa bởi process khác)
                if searched_vehicle_uploaded.pop(previous_search_vehicle, None) is not None:
                    print(f"[SEARCH] Reset search for: {previous_search_vehicle}")
            previous_search_vehicle = search_vehicle
            if search_vehicle != "":
                print(f"[SEARCH] 🔍 New search started for: {search_vehicle}")
        
        found_vehicle_in_this_camera = False
        found_vehicle_bbox = None
        found_vehicle_obj_id = None

        # YOLO + BoT-SORT tracking 
        results = model.track(
            frame,
            persist=True,
            conf=0.5,
            verbose=False,
            tracker=TRACKER_PATH
        )

        boxes = results[0].boxes

        if boxes.id is not None:
            ids = boxes.id.int().tolist()
            xyxy = boxes.xyxy.tolist()

            for i, box in enumerate(xyxy):
                obj_id = ids[i]
                x1, y1, x2, y2 = map(int, box)
                # ---------- Assign global ID immediately if cam is anchor ----------
                if cam_id == 0:  # Camera 1 là ANCHOR
                    key = f"c{cam_id}_{obj_id}"
                    # Use lock to avoid races when anchor assigns new canonical id
                    with lock:
                        if key not in canonical_map:

                            canonical_map[key] = int(next_canonical.value)
                            next_canonical.value += 1

                            global_id = canonical_map[key]

                            # Nếu có biển số mới từ OCR (lưu vào shared license map)
                            new_license_plate, user_id = get_new_license_plate_from_file()
                            if new_license_plate != "":
                                license_shared[global_id] = new_license_plate
                                #print(f"[ADD LP] global_id {global_id} -> {new_license_plate}")

                                # Tạo đối tượng vehicle mới cho bãi xe
                                time_in = datetime.datetime.utcnow()+ datetime.timedelta(hours=7) 
                                parked_vehicles = get_parked_vehicles_from_file()
                                parked_vehicles['list'].append({
                                    'user_id': user_id,
                                    'customer_type': 'customer',
                                    'time_in': time_in.isoformat(),
                                    'license_plate': new_license_plate,
                                    'slot_name': "",
                                    'num_slot': 0 # 0 làm đỗ đúng, 1 là đổ sai
                                })
                                save_parked_vehicles_to_file(parked_vehicles)
                                # POST
                                #print("debug 3")
                                #print(parked_vehicles)
                                threading.Thread(target=update_parked_vehicle_list, args=(parked_vehicles,)).start()
                                # Reset biến
                                save_new_license_plate_to_file("")
                # --------------------------------------------------------------------

                # Kiểm tra object có đi qua điểm giao nào không
                for item in intersections_coords:
                    cid = item['id']
                    x, y = item["coordinate"]
                    if x1 <= x <= x2 and y1 <= y <= y2:
                        coords_trackids[cid] = (int(obj_id), time.time())

                # Lấy canonical_id
                key = f"c{cam_id}_{obj_id}"
                global_id = canonical_map.get(key)
                
                # Kiểm tra nếu xe này đang được tìm kiếm
                if search_vehicle != "" and global_id is not None:
                    vehicle_license = license_shared.get(global_id, "")
                    # So sánh case-insensitive (đã normalize search_vehicle thành uppercase)
                    if vehicle_license == search_vehicle:
                        # Chỉ process nếu chưa upload (tránh spam log và upload trùng)
                        if not searched_vehicle_uploaded.get(search_vehicle, False):
                            found_vehicle_in_this_camera = True
                            found_vehicle_bbox = (x1, y1, x2, y2)
                            found_vehicle_obj_id = obj_id
                            print(f"[SEARCH] ✓ MATCHED! Cam {cam_id} found vehicle {search_vehicle} (obj_id={obj_id}, global_id={global_id})")
                
                label = f"ID:{obj_id}/{int(global_id)}" if global_id else f"ID {obj_id}/-"
                
                # Vẽ bbox bình thường (không highlight)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)
                cv2.putText(frame, label, (x1 + 3, y1 - 3),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                
            # CAMERA GỬI RẺ NHẤT – CHỈ GỬI ID và BOUNDING BOX
            # Update the SHARED bbox dict (manager dict) passed from main
            # Convert boxes to simple lists so manager proxy can serialize easily
            # Thêm timestamp để kiểm tra detection có còn mới không
            current_time = time.time()
            bbox_shared[cam_id] = [
                (int(ids[i]), [int(x) for x in xyxy[i]], current_time)
                for i in range(len(ids))
            ]
        else:
            bbox_shared[cam_id] = []

        # Nếu tìm thấy xe đang được search và chưa upload
        if found_vehicle_in_this_camera and search_vehicle != "":
            # Atomic test-and-set: chỉ camera đầu tiên được phép upload
            # setdefault returns EXISTING value if key exists, else sets and returns new value
            already_uploaded = searched_vehicle_uploaded.setdefault(search_vehicle, False)
            
            if not already_uploaded:
                # Đánh dấu là đã xử lý (lock cho các camera khác)
                searched_vehicle_uploaded[search_vehicle] = True
                
                print(f"[SEARCH] 🎯 Camera {cam_id} won the race! Uploading vehicle {search_vehicle}...")
                print(f"[SEARCH] Vehicle bbox: {found_vehicle_bbox}, obj_id: {found_vehicle_obj_id}")
                
                # Dùng frame gốc đã lưu (chưa vẽ gì) - chỉ vẽ xe đang tìm
                frame_for_mqtt = frame_original.copy()
                x1, y1, x2, y2 = found_vehicle_bbox
                
                # Vẽ bounding box và biển số màu xanh lá, thickness = 2
                cv2.rectangle(frame_for_mqtt, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame_for_mqtt, search_vehicle, (x1 + 3, y1 - 3),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Vẽ tên camera ở góc trên bên trái của frame
                cv2.putText(frame_for_mqtt, f"Camera {cam_id}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
                
                # Encode frame thành jpg
                _, buffer = cv2.imencode('.jpg', frame_for_mqtt)
                img_bytes = buffer.tobytes()
                
                # Upload image to Cloudinary
                upload_success = False
                try:
                    response = requests.post(
                        CLOUDINARY_UPLOAD_URL,
                        files={"file": img_bytes},
                        data={"upload_preset": CLOUDINARY_UPLOAD_PRESET}
                    )
                    if response.status_code == 200:
                        image_url = response.json()["secure_url"]
                        print(f"[SEARCH] ✅ Đã tải hình ảnh lên Cloudinary")
                        print(f"[SEARCH] Image URL: {image_url}")
                        upload_success = True
                        
                        # Publish image URL to MQTT (chỉ 1 lần)
                        threading.Thread(target=publish_vehicle_image_url, args=(image_url,)).start()
                        
                        # Reset search_vehicle_shared về "" sau khi xử lý xong
                        search_vehicle_shared['value'] = ""
                        print(f"[SEARCH] 🔄 Reset search_vehicle to empty")
                    else:
                        print(f"[SEARCH] ❌ Lỗi upload Cloudinary: {response.status_code}")
                        # Không reset nếu upload thất bại để có thể thử lại
                except Exception as e:
                    print(f"[SEARCH] ❌ Exception khi upload: {e}")
                
                # Nếu upload thất bại, bỏ lock để có thể thử lại
                if not upload_success:
                    searched_vehicle_uploaded[search_vehicle] = False

        # Cập nhật dữ liệu detection của camera vào shared dict (để merge giữa các camera)
        for k, v in coords_trackids.items():
            coords_by_cam[cam_id][k] = v

        # Merge ID giữa các camera
        update_mappings_atomic(
            coords_by_cam, lock, canonical_map, next_canonical,
            time_tol=0.5, stale=1.0
        )

        # Vẽ điểm giao
        for item in intersections_coords:
            cv2.circle(frame, (item['coordinate']), 5, (0, 0, 255), -1)
        for item in read_yaml(slot_file):
            cv2.circle(frame, (item['coordinate']), 5, (0, 255, 0), -1)

        cv2.imshow(window_name, frame)
        cv2.waitKey(1)

    cap.release()


def get_global_id_by_license_plate(license_plate):
    """
    Tìm global_id của xe dựa trên biển số.
    Trả về global_id nếu xe đang được detect, None nếu không tìm thấy.
    
    Có thể gọi từ bất kỳ module nào:
        from app.modules.tracking_car import get_global_id_by_license_plate
        global_id = get_global_id_by_license_plate("30A-12345")
    """
    # Tìm trong license map
    for global_id, plate in globals.global_id_license_plate_map.items():
        if plate == license_plate:
            return global_id
    return None


def is_vehicle_being_tracked(license_plate, canonical_map=None):
    """
    Kiểm tra xe có biển số này có đang được tracking không.
    Trả về (is_tracked, global_id, cameras_info)
    
    Có thể gọi từ bất kỳ module nào:
        from app.modules.tracking_car import is_vehicle_being_tracked
        is_tracked, gid, cameras = is_vehicle_being_tracked("30A-12345")
    
    Args:
        license_plate: Biển số xe cần kiểm tra
        canonical_map: (Optional) Nếu None sẽ dùng từ globals
    
    Returns:
        tuple: (is_tracked: bool, global_id: int|None, cameras_info: list)
    """
    # Lấy canonical_map từ globals nếu không truyền vào
    if canonical_map is None:
        canonical_map = globals.canonical_map
        if canonical_map is None:
            print("[WARNING] canonical_map not initialized yet")
            return (False, None, [])
    
    # QUAN TRỌNG: bbox_by_cam phải là manager.dict được share giữa processes
    bbox_by_cam = globals.bbox_by_cam
    if bbox_by_cam is None:
        print("[WARNING] bbox_by_cam not initialized yet")
        return (False, None, [])
    
    global_id = get_global_id_by_license_plate(license_plate)
    
    print(f"[DEBUG is_vehicle_being_tracked] License: {license_plate}")
    print(f"[DEBUG] Found global_id: {global_id}")
    print(f"[DEBUG] globals.global_id_license_plate_map: {dict(globals.global_id_license_plate_map)}")
    print(f"[DEBUG] bbox_by_cam type: {type(bbox_by_cam)}")
    
    if global_id is None:
        print(f"[DEBUG] global_id is None, returning (False, None, [])")
        return (False, None, [])
    
    # KIỂM TRA QUAN TRỌNG: Xác minh global_id này VẪN thuộc về license_plate này
    # (Tránh trường hợp global_id bị tái sử dụng cho xe khác)
    current_license_for_gid = globals.global_id_license_plate_map.get(global_id)
    if current_license_for_gid != license_plate:
        print(f"[DEBUG] global_id {global_id} hiện tại thuộc về '{current_license_for_gid}', không phải '{license_plate}'")
        print(f"[DEBUG] Xe {license_plate} không còn được track (global_id đã được tái sử dụng)")
        return (False, None, [])
    
    # Tìm xe đang được track ở camera nào
    cameras_tracking = []
    current_time = time.time()
    DETECTION_TIMEOUT = 2.0  # Chỉ coi là đang track nếu detect trong vòng 2 giây gần nhất
    
    print(f"[DEBUG] Checking {len(VIDEO_SOURCES)} cameras...")
    print(f"[DEBUG] bbox_by_cam keys: {list(bbox_by_cam.keys())}")
    for cam_idx in range(len(VIDEO_SOURCES)):
        bboxes = bbox_by_cam.get(cam_idx, [])
        print(f"[DEBUG] Camera {cam_idx}: {len(bboxes)} bboxes")
        for bbox_data in bboxes:
            # Xử lý cả format cũ (obj_id, box) và format mới (obj_id, box, timestamp)
            if len(bbox_data) == 2:
                obj_id, box = bbox_data
                timestamp = current_time  # Fallback: coi như mới nếu không có timestamp
            elif len(bbox_data) == 3:
                obj_id, box, timestamp = bbox_data
            else:
                continue
            
            # KIỂM TRA QUAN TRỌNG: Detection có còn mới không?
            time_diff = current_time - timestamp
            if time_diff > DETECTION_TIMEOUT:
                print(f"[DEBUG]   SKIP obj_id={obj_id}: detection quá cũ ({time_diff:.2f}s)")
                continue
            
            # Kiểm tra key trong canonical_map
            key = f"c{cam_idx}_{obj_id}"
            gid = canonical_map.get(key)
            print(f"[DEBUG]   Checking obj_id={obj_id}, key={key}, gid={gid}, target_global_id={global_id}, age={time_diff:.2f}s")
            if gid == global_id:
                # Double-check: global_id này có đúng license_plate đang tìm không?
                verified_license = globals.global_id_license_plate_map.get(gid)
                print(f"[DEBUG]   Double-check: gid {gid} -> license '{verified_license}' (looking for '{license_plate}')")
                if verified_license != license_plate:
                    print(f"[DEBUG]   SKIP: global_id {gid} không còn thuộc về {license_plate}")
                    continue
                print(f"[DEBUG] ✓ MATCH FOUND! Camera {cam_idx}, obj_id {obj_id}, bbox {box}, age={time_diff:.2f}s")
                cameras_tracking.append({
                    'camera_id': cam_idx,
                    'local_track_id': obj_id,
                    'bbox': box,
                    'detection_age': time_diff
                })
                break
    
    # Trả về tuple đầy đủ: (is_tracked, global_id, cameras_info)
    is_tracked = len(cameras_tracking) > 0
    print(f"[DEBUG] Final result: is_tracked={is_tracked}, cameras_tracking={cameras_tracking}")
    print(f"[DEBUG] " + "="*60)
    return (is_tracked, global_id, cameras_tracking)


def print_tracking_status(license_plate, canonical_map=None):
    """
    In ra thông tin chi tiết về trạng thái tracking của xe.
    Dùng để debug.
    
    Có thể gọi từ bất kỳ module nào:
        from app.modules.tracking_car import print_tracking_status
        print_tracking_status("30A-12345")
    
    Args:
        license_plate: Biển số xe cần kiểm tra
        canonical_map: (Optional) Nếu None sẽ dùng từ globals
    """
    # Lấy canonical_map từ globals nếu không truyền vào
    if canonical_map is None:
        canonical_map = globals.canonical_map
        if canonical_map is None:
            print("[ERROR] Tracking system not initialized yet!")
            return
    
    is_tracked, global_id, cameras = is_vehicle_being_tracked(license_plate, canonical_map)
    
    # print(f"\n{'='*60}")
    # print(f"TRACKING STATUS: {license_plate}")
    # print(f"{'='*60}")
    
    if not is_tracked:
        print(f"❌ Xe KHÔNG được detect/track hiện tại")
        if global_id:
            print(f"   - Có Global ID: {global_id} (đã track trước đó)")
        else:
            print(f"   - Chưa từng được track trong hệ thống")
    else:
        print(f"✅ Xe ĐANG được track")
        print(f"   - Global ID: {global_id}")
        print(f"   - Số camera detect: {len(cameras)}")
        for cam_info in cameras:
            print(f"   - Camera {cam_info['camera_id']}: "
                  f"Local Track ID={cam_info['local_track_id']}, "
                  f"BBox={cam_info['bbox']}")
    
    print(f"{'='*60}\n")


def check_parking_vehicle_valid():
    """
    Hàm này dùng để kiểm tra các phương tiện có đang đỗ xe không đúng vị trí (trường hợp 2) hay không.
    """
    # Bộ đếm số lần slot_name bị rỗng liên tiếp
    empty_slot_count = {}
    while True:
        parked_vehicles = get_parked_vehicles_from_file()
        if parked_vehicles['list'] is None:
            time. sleep(10)
            continue
        wrong_slot = False
        #print("checking vehicle slot.....................")
        for vehicle in parked_vehicles['list']:
            license_plate = vehicle['license_plate']
            slot_name = vehicle.get('slot_name', "")

            # Nếu slot_name rỗng
            if slot_name == "" or slot_name is None:
                empty_slot_count[license_plate] = empty_slot_count.get(license_plate, 0) + 1

                # Nếu phát hiện 3 lần liên tiếp
                if empty_slot_count[license_plate] == 3:#% 3 == 0: # cảnh báo được lặp lại sau mỗi chu kỳ
                    print(f"⚠️ CẢNH BÁO: Xe {license_plate} chưa được gán vị trí đỗ trong 20 giây!") #20s-30s
                    threading.Thread(target=speech_text, args=(f"Cảnh báo! Xe biển số {license_plate} đỗ sai vị trí!",)).start()
                    if empty_slot_count[license_plate] == 3:
                        # Cập nhật num_slot = 1 (đỗ sai vị trí)
                        vehicle.update({'num_slot': 1})
                        wrong_slot = True
            else:
                # Nếu đã có slot_name → reset counter
                if license_plate in empty_slot_count:
                    empty_slot_count[license_plate] = 0
        if wrong_slot:
            # POST cập nhật danh sách xe đậu
            #print("debug 1")
            save_parked_vehicles_to_file(parked_vehicles)
            threading.Thread(target=update_parked_vehicle_list, args=(parked_vehicles,)).start()
        time.sleep(10)  # Kiểm tra mỗi 10 giây

def update_parked_vehicle_info(occupied_list, occupied_license_list):
    """
    Hàm này dùng để kiểm tra trạng thái các slot đỗ xe và cập nhật lên cloud server.
    """
    # -------------------------------
    # 1. Tạo bảng mapping license -> danh sách các vị trí bị chiếm
    # -------------------------------
    license_to_slots = {}

    for slot, lic in zip(occupied_list, occupied_license_list):
        if lic not in license_to_slots:
            license_to_slots[lic] = []
        license_to_slots[lic].append(slot)

    # -------------------------------
    # 2. Cập nhật parked_vehicles
    # -------------------------------
    parked_vehicles = get_parked_vehicles_from_file()
    for vehicle in parked_vehicles['list']:
        lic = vehicle['license_plate']
        if lic in license_to_slots:
            slots = license_to_slots[lic]

            vehicle['slot_name'] = ", ".join(slots)  
            if len(slots) < 2:           
                vehicle['num_slot'] = 0
            else:
                vehicle['num_slot'] = 1
                # WARNING: xe đỗ sai vị trí (trường hợp 1)
                print(f"⚠️ CẢNH BÁO: Xe {lic} đỗ sai vị trí tại các slot {vehicle['slot_name']}!")
                threading.Thread(target=speech_text, args=(f"Cảnh báo! Xe biển số {lic} đỗ sai vị trí!",)).start()
        else:
            vehicle['slot_name'] = ""
            vehicle['num_slot'] = 0
    # POST
    #print("debug 2")
    save_parked_vehicles_to_file(parked_vehicles)
    update_parked_vehicle_list(parked_vehicles)


def check_occupied_slots(canonical_map):
    CHECK_INTERVAL = 2       # kiểm tra mỗi 2s
    DELAY_TIME = 6          # yêu cầu ổn định 6s

    last_check_time = 0
    delay_counter = 0

    candidate_state = None
    confirmed_state = None

    while True:
        time. sleep(1)
        now = time.time()
        if now - last_check_time < CHECK_INTERVAL:
            continue

        last_check_time = now
        # =============================================================
        # 1.  TÍNH DANH SÁCH SLOT TỪ HAI CAMERA MỖI 2s
        # =============================================================
        occupied_set = set()              # ID slot bị che
        license_map = {}                  # map slot_id → license

        # Đọc toàn bộ slot (để biết tổng số slot)
        all_slot_ids = set()

        # KIỂM TRA MỖI CAMERA VỚI SLOT CỦA CHÍNH NÓ
        for cam_idx in range(len(VIDEO_SOURCES)):     
            slots = read_yaml(SLOT_COORDS_PATH+str(cam_idx)+'.yml')
            
            # Lưu tất cả slot IDs
            for s in slots:
                all_slot_ids.add(s["id"])
            
            # Lấy bbox từ camera tương ứng
            bboxes = globals.bbox_by_cam. get(cam_idx, [])
            
            # Kiểm tra từng slot của camera này
            for s in slots:
                slot_id = s["id"]
                sx, sy = s["coordinate"]
                
                # Chỉ kiểm tra với bbox từ camera này
                for bbox_data in bboxes:
                    # Xử lý cả format cũ (obj_id, box) và format mới (obj_id, box, timestamp)
                    if len(bbox_data) == 2:
                        obj_id, box = bbox_data
                    elif len(bbox_data) == 3:
                        obj_id, box, timestamp = bbox_data
                    else:
                        continue
                    
                    x1, y1, x2, y2 = map(int, box)
                    
                    if x1 <= sx <= x2 and y1 <= sy <= y2:
                        occupied_set.add(slot_id)
                        
                        key = f"c{cam_idx}_{obj_id}"
                        gid = canonical_map.get(key)
                        
                        if gid is not None:
                            plate = globals.global_id_license_plate_map.get(gid, "UNKNOWN")
                        else:
                            plate = "UNKNOWN"
                        
                        license_map[slot_id] = plate
                        break  # slot này đã bị chiếm, không cần check bbox khác
        
        # print("Occupied slots:", occupied_set)
        # print("Available slots:", all_slot_ids - occupied_set)
        # print("License map:", license_map)
        
        # Danh sách
        globals.occupied_list = sorted(list(occupied_set))
        globals.available_list = sorted(list(all_slot_ids - occupied_set))

        # Danh sách biển số theo đúng thứ tự slot trong occupied_list
        globals.license_occupied_list = [license_map.get(sid, "UNKNOWN") for sid in globals.occupied_list]
        
        # Đây là state mới
        new_state = {
            "occupied_list": globals.occupied_list,
            "available_list": globals. available_list,
            "license_occupied_list": globals.license_occupied_list
        }

        # =============================================================
        # 2.  DELAY WINDOW – PHẢI ỔN ĐỊNH TRONG 6s
        # =============================================================
        if candidate_state is None:
            candidate_state = new_state
            delay_counter = 1
            continue

        if new_state == candidate_state:
            delay_counter += 1
        else:
            candidate_state = new_state
            delay_counter = 1

        # Chưa đủ delay → bỏ qua
        if delay_counter * CHECK_INTERVAL < DELAY_TIME:
            continue

        # =============================================================
        # 3. KẾT QUẢ ỔN ĐỊNH → IN NẾU CÓ THAY ĐỔI
        # =============================================================
        if confirmed_state != new_state:
            # print("===== SLOT STATUS CHANGED =====")
            # print("OCCUPIED:", new_state["occupied_list"])
            # print("AVAILABLE:", new_state["available_list"])
            # print("LICENSE_OCCUPIED:", new_state["license_occupied_list"])
            # print("================================")
            confirmed_state = new_state
            # Gửi dữ liệu thay đổi lên cloud server 
            parking_slot_data = {
                'parking_id': PARKING_ID,
                'available_list': new_state["available_list"],
                'occupied_list': new_state["occupied_list"],
                'occupied_license_list': new_state["license_occupied_list"]
            }
            # POST
            threading.Thread(target=update_parked_vehicle_info, args=(new_state["occupied_list"], new_state["license_occupied_list"])).start()
            threading.Thread(target=update_parking_lot, args=(parking_slot_data,)).start()
            # Update Screen
            threading.Thread(target=update_screen_display, args=(new_state["occupied_list"], new_state["available_list"])).start()

def start_tracking_car():
    manager = Manager()
    parked_vehicles = {
        'parking_id': PARKING_ID,
        'list': []
    }
    save_new_license_plate_to_file("", "")
    save_parked_vehicles_to_file(parked_vehicles)
    # barrier count = number of camera processes
    start_barrier = Barrier(len(VIDEO_SOURCES))

    # Khởi tạo shared memory cho bbox và slot
    # Use explicit shared objects and pass them to child processes (important for 'spawn' start method)
    shared_bbox_by_cam = manager.dict()
    shared_license_map = manager.dict()
    
    # Khởi tạo hoặc lấy search_vehicle_shared từ main
    if globals.search_vehicle_shared is None:
        shared_search_vehicle = manager.dict()
        shared_search_vehicle['value'] = ""
        globals.search_vehicle_shared = shared_search_vehicle
        print("[INFO] Created new search_vehicle_shared in tracking_car")
    else:
        shared_search_vehicle = globals.search_vehicle_shared
        print("[INFO] Using existing search_vehicle_shared from main")
    
    # Shared dict để đảm bảo chỉ upload 1 lần cho mỗi search_vehicle
    searched_vehicle_uploaded = manager.dict()

    globals.bbox_by_cam = shared_bbox_by_cam
    globals.global_id_license_plate_map = shared_license_map

    camera_configs = []
    print("[INFO] Loading camera coordinates from cloud server...")
    
    # Tải tọa độ song song bằng threads để nhanh hơn
    def load_camera_coords(cam_idx):
        try:
            cam = get_coordinates(PARKING_ID, str(cam_idx))
            if cam is not None:
                slot_coordinates_data = cam.get('coordinates_list')
                reid_coordinates_data = cam.get('coordinates_reid_list')
                write_yaml_file(f"{SLOT_COORDS_PATH}{cam_idx}.yml", slot_coordinates_data)
                write_yaml_file(f"{REID_COORDS_PATH}{cam_idx}.yml", reid_coordinates_data)
                print(f"[INFO] Camera {cam_idx} coordinates loaded")
        except Exception as e:
            print(f"[WARNING] Failed to load camera {cam_idx} coordinates: {e}")
    
    # Load tất cả camera coordinates song song
    coord_threads = []
    for i, cam_source in enumerate(VIDEO_SOURCES):
        camera_configs.append((VIDEO_SOURCES[i], f"Camera {i}", REID_COORDS_PATH+str(i)+'.yml', SLOT_COORDS_PATH+str(i)+'.yml'))
        globals.bbox_by_cam[i] = []
        t = threading.Thread(target=load_camera_coords, args=(i,))
        t.start()
        coord_threads.append(t)
    
    # Chờ tất cả threads load xong
    for t in coord_threads:
        t.join()
    
    print("[INFO] All camera coordinates loaded")

    num_cams = len(camera_configs)

    # 1-indexed: index 0 bỏ trống
    coords_by_cam = [manager.dict() for _ in range(num_cams)]
    lock = manager.Lock()

    # Map ID toàn cục: key = "c{cam}_{track}" → canonicalID
    canonical_map = manager.dict()
    
    # Lưu canonical_map vào globals để có thể truy cập từ bên ngoài
    globals.canonical_map = canonical_map

    # Counter cho canonical ID 
    next_canonical = manager.Value('i', 1)

    set_start_method("spawn", force=True)

    procs = []

    # Khởi tạo mỗi camera thành 1 process riêng
    for idx, (video_path, window_name, intersections_file, slot_file) in enumerate(camera_configs, start=0):
        p = Process(target=process_video, args=(
            video_path, window_name, DETECT_MODEL_PATH, idx,
            coords_by_cam, lock, canonical_map, next_canonical, intersections_file, slot_file, start_barrier,
            shared_bbox_by_cam, shared_license_map, shared_search_vehicle, searched_vehicle_uploaded
        ))
        p.start()
        procs.append(p)

    # Bắt đầu kiểm tra slot (thread chạy trong main process, dùng shared dicts)
    threading.Thread(target=check_occupied_slots, args=(canonical_map,), daemon=True).start()
    threading.Thread(target=check_parking_vehicle_valid, daemon=True).start()
    for p in procs:
        p.join()

    cv2.destroyAllWindows()