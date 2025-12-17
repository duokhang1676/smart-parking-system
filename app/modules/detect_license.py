
import os
import cv2
import torch
import time
import threading
from dotenv import load_dotenv
from app.modules import globals
from app.modules.utils import play_sound, save_new_license_plate_to_file, get_parked_vehicles_from_file
import app.resources.license_plate_recognition.function.helper as helper
import app.resources.license_plate_recognition.function.utils_rotate as utils_rotate
load_dotenv()
def start_detect_license():
    # Load model YOLO tùy chỉnh để phát hiện biển số xe
    yolov5_path = "app/resources/license_plate_recognition/yolov5"
    license_plate_detection_path = "app/resources/license_plate_recognition/model/LP_detector_nano_61.pt"
    license_plate_ocr_path ="app/resources/license_plate_recognition/model/LP_ocr_nano_62.pt"

    yolo_LP_detect = torch.hub.load(yolov5_path, 'custom', path=license_plate_detection_path, force_reload=True, source='local')
    # Load model YOLO tùy chỉnh để nhận diện chữ trên biển số xe
    yolo_license_plate = torch.hub.load(yolov5_path, 'custom', path=license_plate_ocr_path, force_reload=True, source='local')
    # Đặt ngưỡng độ tự tin (confidence threshold) để nhận diện biển số xe
    yolo_license_plate.conf = 0.4
    cap = cv2.VideoCapture(int(os.getenv("LICENSE_CAMERA")), cv2.CAP_DSHOW)
    lp_temp = ""
    delay = 0
    authen_threshold = 5
    qr_decoder = cv2.QRCodeDetector()
    while(True):
        if not globals.start_detect_license:
            time.sleep(1)
            continue
        else:
            if globals.qr_code == "":
                ret, frame = cap.read()
                if not ret or frame is None:
                    print("[WARNING] Failed to read QR frame")
                    time.sleep(0.1)
                    continue
                
                print("[DEBUG] QR Detecting...")
                try:
                    qr_code, points, _ = qr_decoder.detectAndDecode(frame)
                except cv2.error as e:
                    print(f"[ERROR] QR decode error: {e}")
                    time.sleep(0.1)
                    continue
                    
                if points is not None:
                    if qr_code:
                        threading.Thread(target=play_sound, args=('scan.mp3',)).start()
                        print("Detected QR Code:", qr_code)
                        # Nếu xe vào kiểm tra có đang ký không
                        if globals.car_in:
                            exists = any(item["user_id"] == qr_code for item in globals.registered_vehicles)
                            if exists:
                                globals.qr_code = qr_code
                            else:
                                print("QR Code not registered:", qr_code)
                                threading.Thread(target=play_sound, args=('qr-not-registered.mp3',)).start()
                                time.sleep(3)
                        # Nếu xe ra kiểm tra xe đã có trong bãi không
                        elif globals.car_out:
                            exists = any(item["user_id"] == qr_code for item in get_parked_vehicles_from_file()["list"])
                            if exists:
                                globals.qr_code = qr_code
                            else:
                                print("QR Code not in parked vehicles:", qr_code)
                                threading.Thread(target=play_sound, args=('qr-not-registered.mp3',)).start()
                                time.sleep(3)
            elif globals.license_plate == "":
                ret, frame = cap.read()
                if frame is None:
                    print("License frame is none!")
                    time.sleep(1)
                    continue
                print("License Detecting...")
                plates = yolo_LP_detect(frame, size=640)
                # Lấy danh sách các biển số xe được phát hiện (tọa độ bounding box)
                list_plates = plates.pandas().xyxy[0].values.tolist()
                # Tạo một tập hợp để lưu các biển số xe đã đọc
                list_read_plates = []
                # Lặp qua tất cả các biển số xe được phát hiện
                for plate in list_plates:
                    x = int(plate[0]) # Lấy tọa độ xmin của bounding box
                    y = int(plate[1]) # Lấy tọa độ ymin của bounding box
                    w = int(plate[2] - plate[0]) # Tính toán chiều rộng của bounding box
                    h = int(plate[3] - plate[1]) # Tính toán chiều cao của bounding box
                    # Cắt hình ảnh của biển số xe từ khung hình
                    crop_img = frame[y:y+h, x:x+w]
                    lp = helper.read_plate(yolo_license_plate, utils_rotate.deskew(crop_img, 0, 0))
                    # Nếu biển số được nhận diện không phải "unknown"
                    if lp != "unknown":
                        # Thêm biển số đã nhận diện vào danh sách
                        list_read_plates.append(lp)
                # Xác nhận biển số xe có chính xác không bằng cách kiểm tra giá trị trong 3 lần detect có giống nhau không
                if len(list_read_plates) == 1: # chỉ lấy 1 biển số xe, trường hợp có nhiều hơn 1 biến số xe hoặc không có cái nào thì bỏ qua
                    if list_read_plates[0] == lp_temp:
                        delay += 1
                    else:
                        delay = 0
                        lp_temp = list_read_plates[0]
                    if delay >= authen_threshold:   
                        delay = 0
                        print("Detected License Plate:", lp_temp)
                        threading.Thread(target=play_sound, args=('scan.mp3',)).start()
                        # Nếu xe vào kiểm tra biển số có đăng ký không và xe đã có trong bãi chưa
                        if globals.car_in:
                            # Kiểm tra biển số có trong danh sách đăng ký và user_id trùng với qr_code không
                            condition_1 = False
                            condition_2 = False
                            for item in globals.registered_vehicles:
                                if item["license_plate"] == lp_temp and item["user_id"] == globals.qr_code:
                                    condition_1 = True
                                    break
                            condition_2 = any(item["license_plate"] == lp_temp for item in get_parked_vehicles_from_file()["list"])
                            if condition_1 and not condition_2:
                                globals.license_plate = lp_temp
                                save_new_license_plate_to_file(lp_temp, globals.qr_code)
                                globals.start_detect_license = False
                                if globals.car_in:
                                    globals.open_in = True
                                    globals.car_in = False
                                if globals.car_out:
                                    globals.open_out = True
                                    globals.car_out = False
                            else:
                                print("License Plate not registered:", lp_temp)
                                threading.Thread(target=play_sound, args=('bien-so-khong-dung.mp3',)).start()
                                time.sleep(3)
                        # Nếu xe ra kiểm tra biển số có trong bãi không
                        elif globals.car_out:
                            exists = any(item["license_plate"] == lp_temp for item in get_parked_vehicles_from_file()["list"])
                            if exists:
                                globals.license_plate = lp_temp
                                globals.start_detect_license = False
                                if globals.car_in:
                                    globals.open_in = True
                                    globals.car_in = False
                                if globals.car_out:
                                    globals.open_out = True
                                    globals.car_out = False
                            else:
                                print("License Plate not in parked vehicles:", lp_temp)
                                threading.Thread(target=play_sound, args=('bien-so-khong-dung.mp3',)).start()
                                time.sleep(3)
            else:
                time.sleep(1)