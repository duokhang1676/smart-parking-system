import threading
import time
import cv2
import torch
from ultralytics import YOLO
from app.modules.utils import *
import requests
import app.modules.globals as globals
from app.modules.cloud_api import *
from dotenv import load_dotenv
load_dotenv()

# KEEPING THINGS SIMPLE

start_detect_qr = False
start_detect_license = False
customer_type = ""
new_car = ""
car_in = False
car_out = False
id_code_in = ""
id_code_out = ""
license_car_in = ""
license_car_out = ""
parking_id = 'parking_001'

# Danh sách Dictionary chứa các xe đã đỗ trong bãi (Hiện tại lưu trữ tạm thời trong RAM, cần lưu vào DB sqlite)
parked_vehicles = []
available_list = []
occupied_list = []
occupied_license_list = []
arduino_update = False
direction = []
slot_table = []
wrong_slot = [] 
qr_thread = True
license_thread = True
update_coordinate_arduino = False

qr_first = True
# Danh sách Dictionary các biển số xe đã được đăng ký
# sài tạm
registered_vehicles = [{
    "parking_id": parking_id,
    "user_id": "00",
    "license_plate":  "30K-55055",
},
{
    "parking_id": parking_id,
    "user_id": "01",
    "license_plate":  "30G-49344",
},
{    
    "parking_id": parking_id,
    "user_id": "01",
    "license_plate":  "30G-53507",
}
]

CLOUD_NAME = os.getenv('CLOUD_NAME')
UPLOAD_PRESET = os.getenv('UPLOAD_PRESET')
TRACKING_CAMERA_ID = os.getenv("TRACKING_CAMERA_ID")
QR_CAMERA_ID = os.getenv("QR_CAMERA_ID")
LICENSE_CAMERA_ID = os.getenv("LICENSE_CAMERA_ID")

def start_main_flow():
    # Load slot_coordinates và reid_coordinates từ cloud server
    cam = get_coordinates(parking_id, str(TRACKING_CAMERA_ID))
    if cam is not None:
        globals.slot_coordinates_data = cam.get('coordinates_list')
        globals.reid_coordinates_data = cam.get('reid_coordinates_list')
        
######################################
    track_licenses = [] # danh sách biển số xe đang ở trong bãi xe đang được theo dõi
    track_ids_full = [] # danh sách tất cả ids track được 
    license_ids_full = [] # danh sách license id đã được theo dõi tương ứng với track_ids_full
    pre_hidden_ids = [] # danh sách vị trí có xe ở vòng lặp trước
    last_id = 0 # id được trackq gần nhất
    
    occoccupied_delay = 0
    hidden_ids_map_track_licenses = [] # Danh sách chứa các id được tracking tương ứng với các vị trí bị che khuất

    while True:
        # Danh sách các tọa độ và id của xe đã track được
        detected_boxes, track_ids = tracking_objects(tracker, model, frame, confidence_threshold = 0.6, device=device)
# xe đi vào
        if len(track_ids) != 0:
            # Phát hiện xe mới vào
            if track_ids[-1] > last_id:
                # danh sách các id mới được track
                new_car_list = [x for x in track_ids if x > last_id]
                for i in new_car_list:
                    last_id = i
                    # xe vào thật có license
                    if new_car != "":   
                        if last_id not in track_ids_full:
                            track_ids_full.append(last_id)
                            license_ids_full.append(new_car)
                        new_car = ""
                    # xe vào do đặt vào hoặc detect sai gán license là id track được
                    else:
                        if last_id not in track_ids_full:
                            track_ids_full.append(last_id)
                            license_ids_full.append(last_id)
            
# xe đi ra
        track_licenses = [license_ids_full[track_ids_full.index(track_id)] for track_id in track_ids]
      
# so khớp vị trí đỗ
        # danh sách vị trí có xe, không có xe và tracking id tại các vị trí đỗ có xe
        hidden_ids, visible_ids, hidden_ids_map_track_licenses = check_occlusion(coordinates_data, detected_boxes, track_licenses)
        
        # tạo delay cho xe tại vị trí đỗ để xác nhận chắc chắn xe đã đỗ hoặc rời đi tránh trường hợp chỉ chạy qua
        if hidden_ids != pre_hidden_ids:
            occoccupied_delay += 1
        else:
            pre_hidden_ids = hidden_ids
            occoccupied_delay = 0

# Xác định có thay đổi vị trí đỗ xe trong ds khi danh sách tọa độ đã không thay đổi trong 100 frame và kích thước biển số và id map với nhau
        if occoccupied_delay >= 100: 
            print("Có sự thay đổi vị trí đỗ xe")
            pre_hidden_ids = hidden_ids
            occoccupied_delay = 0

            available_list = visible_ids
            occupied_list = hidden_ids
            occupied_license_list = hidden_ids_map_track_licenses

            #gửi đến arduino 
            update_coordinate_arduino = True
            arduino_update = True
            # gợi ý hướng vào (làm tạm) fix
            direction = find_min_slots(available_list)
            print("derection", direction)
            # tính toán số lượng  ô đỗ
            slot_table = count_groups(occupied_list)
            print("slot table",slot_table)

            # Tạo parked-vehicles
            
            print("occupied",hidden_ids)
            print("license occupied",hidden_ids_map_track_licenses)
            print("")

            # Gán slot name và num slot cho parked vehicle
            temp = False
            for i, parked_vehicle in enumerate(parked_vehicles):
                numslot = 0
                for j, license in enumerate(occupied_license_list):
                    if parked_vehicle["license_plate"] == license:
                        numslot += 1
                        parked_vehicles[i]["slot_name"] = occupied_list[j] # fix
                        parked_vehicles[i]["num_slot"] = numslot
                        temp = True
            # cập nhật parked_vehicle
            if temp:
                data = {
                    'parking_id': parking_id,
                    'list': parked_vehicles
                }
                if update_parked_vehicle_list(data):
                    print("câp nhật parked vehicles thành công")
                else:
                    print("cập nhật parked vehicles thất bại")
            # cập nhật parking lot server
            data = {
                'parking_id': parking_id,
                'available_list': available_list,
                'occupied_list': occupied_list,
                'occupied_license_list': occupied_license_list
            }
            if update_parking_lot(data):
                print("cập nhật parkingslot thành công")
            else:
                print("cập nhật parkingslot thất bại")

            # cảnh báo đỗ sai vị trí
            wrong_slot = []
            for parked_vehicle in parked_vehicles:
                if parked_vehicle["num_slot"] > 1:
                    wrong_slot.append(parked_vehicle['license_plate'])
            #print("wrong slot", wrong_slot)
            if wrong_slot != []:
                text = "Xe có biển kiểm xoát, "+ str(wrong_slot) + ", đậu xe không đúng vị trí vui lòng di chuyển, xin cảm ơn!"
                threading.Thread(target=speech_text, args=(text,)).start()

            


# trực quan
    ##########
        if count % 200 == 0:
            #print("IDs:", track_ids_full)
            #print("Tất biển số xe đã vào:", license_ids_full)
            print("-------")
            print("license:", track_licenses)
            #print("ID hiện tại:",track_ids)
            #print("Tọa độ:",detected_boxes)
            print("Các vị trí đã có xe đỗ: ", hidden_ids)
            print("Các xe đã đỗ tương ứng: ", hidden_ids_map_track_licenses)
            #print("Số lần thay đổi vị trí đỗ xe: ", change_count)
            print("-------")

        #draw_points_and_ids(frame, coordinates_data, hidden_ids, track_ids, detected_boxes, track_licenses, fps, hidden_ids_map_track_licenses)
       
        # Hiển thị
        # cv2.imshow("Tracking camera", frame)
        # if cv2.waitKey(1) == ord('q'):
        #     break
        ###########


    # cap.release()
    # cv2.destroyAllWindows()

# def count_groups(a):
#     group_counts = {'A': 0, 'B': 0, 'C': 0, 'D': 0}

#     for slot in a:
#         letter = slot[0]
#         if letter in group_counts:
#             group_counts[letter] += 1

#     return [group_counts[k] for k in ['A', 'B', 'C', 'D']]

# def find_min_slots(a):
#     groups = {'A': float('inf'), 'B': float('inf'), 'C': float('inf'), 'D': float('inf')}

#     for slot in a:
#         letter = slot[0]
#         number = int(slot[1:])

#         if letter in groups:
#             groups[letter] = min(groups[letter], number)

#     # Convert to desired format as a list with empty strings for missing values
#     result = [f"{k}{groups[k]}" if groups[k] != float('inf') else "" for k in ['A', 'B', 'C', 'D']]

#     return result