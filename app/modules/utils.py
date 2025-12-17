import yaml
import cv2 
import os
import vlc
import time
from gtts import gTTS
import numpy as np
import json
from app.modules import globals
import datetime

def tracking_objects2(tracker, image, detections):
    if len(detections) == 0:
        return [], []

    # Kiểm tra cấu trúc của `detections`
    for det in detections:
        if len(det) != 5:
            print(f"Dữ liệu không hợp lệ: {det}")
            return [], []
##        
    tracked_objects = tracker.update(np.array(detections))
    detected_boxes = []
    track_ids = []
    for x1, y1, x2, y2, track_id in tracked_objects:
        x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
        detected_boxes.append([x1, y1, x2, y2])
        track_ids.append(int(track_id))
    return detected_boxes[::-1], track_ids[::-1] # Trả về  danh sách bounding boxes và track id 

def tracking_objects(tracker, model, image, confidence_threshold=0.5, device='cuda'):
    results = model(image,  device=device)[0]
    detections = []
    for r in results.boxes.data.tolist():
        x1, y1, x2, y2, conf, cls = r
        if int(cls) == 0 and conf >= confidence_threshold: 
            detections.append([x1, y1, x2, y2, conf])
##
    if len(detections) == 0:
        return [], []

    # Kiểm tra cấu trúc của `detections`
    for det in detections:
        if len(det) != 5:
            print(f"Dữ liệu không hợp lệ: {det}")
            return [], []
##        
    tracked_objects = tracker.update(np.array(detections))
    detected_boxes = []
    track_ids = []
    for x1, y1, x2, y2, track_id in tracked_objects:
        x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
        detected_boxes.append([x1, y1, x2, y2])
        track_ids.append(int(track_id))
    return detected_boxes[::-1], track_ids[::-1] # Trả về  danh sách bounding boxes và track id 


def read_yaml(file_path):
    # Kiểm tra xem file có tồn tại không
    if not os.path.exists(file_path):
        # Tạo file mới nếu không tồn tại
        with open(file_path, 'w') as file:
            yaml.dump({}, file)  # Lưu một dictionary rỗng vào file YAML

    # Đọc dữ liệu từ file
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file) or {}  # Nếu file rỗng, trả về dict rỗng
    return data

def write_yaml_file(file_path, data):
    # Ghi đè dữ liệu vào file YAML
    with open(file_path, 'w') as file:
        yaml.dump(data, file)
    print(f'YAML file {file_path} written successfully.')
    
# Kiểm tra xem điểm (x, y) có nằm trong bounding box không
def is_point_in_box(x, y, box):
    x_min, y_min, x_max, y_max = box
    return x_min <= x <= x_max and y_min <= y <= y_max

# Hàm vẽ dấu chấm và ID tại tọa độ
def draw_points_and_ids(frame, coordinates_data, hidden_ids, track_ids, detected_boxes, track_licenses, fps, hidden_ids_map_track_licenses):
    cv2.putText(frame, f"FPS: {fps:.0f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    for item in coordinates_data:
        coord = item['coordinate']
        x, y = coord
        license = ""
        # Kiểm tra xem điểm có bị che khuất hay không
        if item['id'] in hidden_ids:
            position = hidden_ids.index(item['id'])
            license = str(hidden_ids_map_track_licenses[position])
            # Vẽ dấu chấm màu đỏ nếu tọa độ bị che khuất
            cv2.circle(frame, (x, y), 5, (0, 0, 255), -1)  # Dấu chấm màu đỏ
        else:
            # Vẽ dấu chấm màu xanh lá nếu không bị che khuất
            cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)  # Dấu chấm màu xanh lá
        # # Vẽ ID gần dấu chấm
        # if license == "":
        cv2.putText(frame, str(item['id']), (x - 5, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)  # ID màu đỏ
        # else:
        #     cv2.putText(frame, str(item['id'])+" - " + license, (x - 5, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)  # ID màu đỏ
        #     license = ""

    for i, track_id in enumerate(track_ids):
            x1, y1, x2, y2 = detected_boxes[i]
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)
            if len(track_licenses) == len(track_ids):
                cv2.putText(frame, f"ID: {track_licenses[i]}", (x1, y1-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            else:
                cv2.putText(frame, f"ID: {int(track_id)}", (x1, y1-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            
            

# Hàm kiểm tra các điểm bị che khuất
def check_occlusion(coordinates_data, detected_boxes, track_licenses):
    hidden_ids = []  # Danh sách chứa các ID bị che khuất
    visible_ids = []  # Danh sách chứa các ID không bị che khuất
    hidden_ids_map_track_licenses = [] # Danh sách chứa các id được tracking tương ứng với các vị trí bị che khuất
    for item in coordinates_data:
        coord = item['coordinate']
        x, y = coord
        is_hidden = False
        
        # Kiểm tra xem điểm có nằm trong bất kỳ bounding box nào không
        for i, box in enumerate(detected_boxes):
            if is_point_in_box(x, y, box):
                is_hidden = True
                hidden_ids_map_track_licenses.append(track_licenses[i])
                break
        
        if is_hidden:
            hidden_ids.append(item['id'])

        else:
            visible_ids.append(item['id'])
    
    return hidden_ids, visible_ids, hidden_ids_map_track_licenses

def speech_text(text):
    # Tạo tts
    tts = gTTS(text=text, lang='vi', slow=False)
    path = "app/resources/mp3/temp.mp3"
    tts.save(path)
    player = vlc.MediaPlayer(path)
    player.play()

def play_sound(file_name):
    player = vlc.MediaPlayer("app/resources/mp3/" + file_name)
    player.play()

def get_parked_vehicles_from_file():
    with open("app/resources/database/parked_vehicles.json", "r", encoding="utf-8") as f:
        parked_vehicles = json.load(f)
    return parked_vehicles

def get_parked_vehicles_by_license_plate(license_plate):
    parked_vehicles = get_parked_vehicles_from_file()
    for vehicle in parked_vehicles['list']:
        if vehicle['license_plate'] == license_plate:
            return vehicle
    return None

def save_parked_vehicles_to_file(parked_vehicles):
    with open("app/resources/database/parked_vehicles.json", "w", encoding="utf-8") as f:
        json.dump(parked_vehicles, f, ensure_ascii=False, indent=4)

def get_new_license_plate_from_file():
    with open("app/resources/database/new_license.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["new_license"], data["user_id"]

def save_new_license_plate_to_file(new_license_plate, user_id=""):
    with open("app/resources/database/new_license.json", "w", encoding="utf-8") as f:
        json.dump({
            "new_license": new_license_plate,
            "user_id": user_id
        }, f, ensure_ascii=False, indent=4)

def update_screen_display(occupied_list, available_list):
    """
    Cập nhật thông tin hiển thị màn hình:
    - slot_recommend: Chuỗi các vị trí có số lớn nhất mỗi dãy (ví dụ: "A5 - B6 - C3")
    - parking_num_slot: Mảng số lượng ô đã có xe của từng dãy
    
    Args:
        occupied_list: Danh sách các vị trí đã có xe (ví dụ: ["A1", "A2", "B3", "C1"])
        available_list: Danh sách các vị trí còn trống (ví dụ: ["A3", "A4", "A5", "B1", "B2"])
    """
    
    # 1. Tạo dictionary đếm số xe đã đỗ theo từng dãy
    row_occupied_count = {}  # {'A': 2, 'B': 1, 'C': 1}
    
    for slot in occupied_list:
        if slot and len(slot) > 0:
            row = slot[0]  # Lấy ký tự đầu tiên (A, B, C, ...)
            row_occupied_count[row] = row_occupied_count.get(row, 0) + 1
    
    # 2. Tìm vị trí có số lớn nhất trong mỗi dãy từ available_list
    row_max_slots = {}  # {'A': 'A5', 'B': 'B6', 'C': 'C3'}
    
    for slot in available_list:
        if slot and len(slot) > 1:
            row = slot[0]  # Ký tự đầu (A, B, C, ...)
            try:
                slot_number = int(slot[1:])  # Số phía sau (5, 6, 3, ...)
                
                # Nếu chưa có hoặc số mới lớn hơn số cũ
                if row not in row_max_slots:
                    row_max_slots[row] = slot
                else:
                    current_max = int(row_max_slots[row][1:])
                    if slot_number > current_max:
                        row_max_slots[row] = slot
            except ValueError:
                # Bỏ qua nếu không parse được số
                continue
    
    # 3. Sắp xếp theo thứ tự alphabet và tạo chuỗi slot_recommend
    sorted_rows = sorted(row_max_slots.keys())
    recommend_slots = [row_max_slots[row] for row in sorted_rows]
    globals.slot_recommend = " - ".join(recommend_slots)
    
    # 4. Tạo mảng parking_num_slot (số xe đã đỗ theo từng dãy)
    # Sắp xếp theo thứ tự alphabet
    all_rows = sorted(set(list(row_occupied_count.keys()) + sorted_rows))
    globals.parking_num_slot = [row_occupied_count.get(row, 0) for row in all_rows]
    
    # print(f"[SCREEN] Slot recommend: {globals.slot_recommend}")
    # print(f"[SCREEN] Parking num slot: {globals.parking_num_slot}")
    globals.update_display = True

def save_regisstered_vehicles_to_file(registered_vehicles):
    globals.registered_vehicles = registered_vehicles
    with open("app/resources/database/registered_vehicles.json", "w", encoding="utf-8") as f:
        json.dump(registered_vehicles, f, ensure_ascii=False, indent=4)


def remove_vehicle_from_system(license_plate):
    """
    Xóa toàn bộ thông tin xe khỏi hệ thống khi xe ra khỏi bãi.
    Bao gồm:
    - Xóa xe khỏi parked_vehicles.json
    - Xóa global_id và license_plate mapping
    
    Args:
        license_plate: Biển số xe cần xóa
    
    Returns:
        dict: Thông tin về xe đã xóa và kết quả
        {
            'success': bool,
            'license_plate': str,
            'global_id': int|None,
            'vehicle_info': dict|None,
            'message': str
        }
    """
    result = {
        'success': False,
        'license_plate': license_plate,
        'global_id': None,
        'vehicle_info': None,
        'message': ''
    }
    
    # 1. Tìm global_id từ license_plate
    global_id_to_remove = None
    for global_id, plate in dict(globals.global_id_license_plate_map).items():
        if plate == license_plate:
            global_id_to_remove = global_id
            break
    
    if global_id_to_remove:
        result['global_id'] = global_id_to_remove
    
    # 2. Xóa khỏi parked_vehicles.json
    try:
        parked_vehicles = get_parked_vehicles_from_file()
        original_count = len(parked_vehicles['list'])
        
        # Tìm và lưu thông tin xe trước khi xóa
        vehicle_found = None
        new_list = []
        for vehicle in parked_vehicles['list']:
            if vehicle['license_plate'] == license_plate:
                vehicle_found = vehicle
                result['vehicle_info'] = vehicle
            else:
                new_list.append(vehicle)
        
        parked_vehicles['list'] = new_list
        save_parked_vehicles_to_file(parked_vehicles)
        
        removed_from_file = original_count > len(new_list)
        
        if removed_from_file:
            print(f"[REMOVE] Đã xóa xe {license_plate} khỏi parked_vehicles.json")
        else:
            print(f"[INFO] Xe {license_plate} không tồn tại trong parked_vehicles.json")
            
    except Exception as e:
        print(f"[ERROR] Lỗi khi xóa khỏi parked_vehicles.json: {e}")
        result['message'] = f"Lỗi xóa file: {e}"
        return result
    
    # 3. Xóa khỏi global_id_license_plate_map
    removed_from_map = False
    if global_id_to_remove is not None:
        try:
            if global_id_to_remove in globals.global_id_license_plate_map:
                del globals.global_id_license_plate_map[global_id_to_remove]
                removed_from_map = True
                print(f"[REMOVE] Đã xóa mapping: global_id {global_id_to_remove} -> {license_plate}")
            else:
                print(f"[INFO] Global ID {global_id_to_remove} không tồn tại trong map")
            
            # QUAN TRỌNG: Xóa TẤT CẢ keys trong canonical_map liên quan đến global_id này
            # Để tránh global_id bị tái sử dụng nhầm cho xe khác
            if globals.canonical_map is not None:
                keys_to_remove = []
                for key, gid in dict(globals.canonical_map).items():
                    if gid == global_id_to_remove:
                        keys_to_remove.append(key)
                
                for key in keys_to_remove:
                    try:
                        del globals.canonical_map[key]
                        print(f"[REMOVE] Đã xóa canonical_map key: {key} -> {global_id_to_remove}")
                    except Exception as e:
                        print(f"[ERROR] Không thể xóa key {key}: {e}")
                
                if keys_to_remove:
                    print(f"[REMOVE] Đã xóa {len(keys_to_remove)} keys từ canonical_map")
        except Exception as e:
            print(f"[ERROR] Lỗi khi xóa khỏi global_id_license_plate_map: {e}")
    else:
        print(f"[INFO] Xe {license_plate} chưa có global_id")
    
    # 4. Tổng kết kết quả
    if removed_from_file or removed_from_map:
        result['success'] = True
        result['message'] = f"Đã xóa xe {license_plate} khỏi hệ thống"
        print(f"[SUCCESS] {result['message']}")
    else:
        result['message'] = f"Xe {license_plate} không tồn tại trong hệ thống"
        print(f"[WARNING] {result['message']}")
    
    return result

from app.modules.tracking_car import is_vehicle_being_tracked
from app.modules.cloud_api import insert_history, update_parked_vehicle_list
from app.resources.print_bill.print_bill import printting, write_file_pdf
import datetime
def verify_car_out(license_plate):
    print(f"[VERIFY] Bắt đầu xác minh xe ra: {license_plate}")
    print(datetime.datetime.now())
    time.sleep(10)
    print(datetime.datetime.now())
    vehicle_info = get_parked_vehicles_by_license_plate(license_plate)
    if vehicle_info is None:
        print(f"[VERIFY] Xe {license_plate} không có trong danh sách xe đậu.")
        return False
    else:
        print(f"[VERIFY] Tìm thấy thông tin xe {license_plate}: {vehicle_info}")
    # Kiểm tra xem xe có còn được track không
        print(f"[VERIFY] Calling is_vehicle_being_tracked for {license_plate}...")
        is_tracked, gid, cameras = is_vehicle_being_tracked(license_plate)
        print(f"[VERIFY] Result: is_tracked={is_tracked}, global_id={gid}, cameras={cameras}")
        if is_tracked:
            print(f"[VERIFY] Xe {license_plate} vẫn đang được theo dõi, không xóa khỏi hệ thống.")
            return False
        else:
            print(f"[VERIFY] Xe {license_plate} không còn được theo dõi, tiến hành xóa khỏi hệ thống.")
            
            # Xóa thông tin xe khỏi danh sách xe trong bãi
            remove_vehicle_from_system(license_plate)

            # Tạo history khi xe ra
            # Chuyển time_in từ string sang datetime
            time_in_str = vehicle_info.get('time_in', '')
            time_in = datetime.datetime.fromisoformat(time_in_str)

            # Tính thời gian đậu xe
            time_out = datetime.datetime.utcnow() + datetime.timedelta(hours=7)
            parking_time_delta = time_out - time_in
    
            # Chuyển sang giờ (hours)
            parking_time_hours = parking_time_delta.total_seconds() / 3600
            # Tính tiền
            total_price = 0.0
            if parking_time_hours < 1:
                total_price = float(os.getenv('PRICE_PER_HOUR', '0'))
            else:
                total_price = parking_time_hours * float(os.getenv('PRICE_PER_HOUR', '0'))
            parking_time_hours = round(parking_time_hours, 2)
            total_price = round(total_price, 2)
            insert_history({
                'parking_id': os.getenv('PARKING_ID'),
                'user_id': vehicle_info.get('user_id', ''),
                'license_plate': license_plate,
                'time_in': time_in.isoformat(),
                'time_out': time_out.isoformat(),
                'parking_time': parking_time_hours,
                'total_price': total_price
            })
            print(f"[VERIFY] Đã tạo history cho xe {license_plate}: {parking_time_hours}h, {total_price} VNĐ")
            # Update parked_vehicles.json
            parked_vehicles = get_parked_vehicles_from_file()
            new_list = [v for v in parked_vehicles['list'] if v['license_plate'] != license_plate]
            parked_vehicles['list'] = new_list
            save_parked_vehicles_to_file(parked_vehicles)
            update_parked_vehicle_list(parked_vehicles)
            print(f"[VERIFY] Đã cập nhật parked_vehicles.json sau khi xe {license_plate} ra khỏi bãi.")
            # Print bill
            write_file_pdf(
                date=time_out.strftime("%d/%m/%Y-%H:%M:%S"),
                license=license_plate,
                time_in=time_in,
                time_out=time_out,
                parking_time=parking_time_hours,
                total_price=total_price
            )
            printting()
            return True
