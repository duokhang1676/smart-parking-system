from PIL import Image
import cv2
import torch
import math 
import resources.license_plate_recognition.function.utils_rotate as utils_rotate
from IPython.display import display
import os
import time
import argparse
import resources.license_plate_recognition.function.helper as helper
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

def detectLicense(id):
    # Load model YOLO tùy chỉnh để phát hiện biển số xe
    yolo_LP_detect = torch.hub.load('resources/license_plate_recognition/yolov5', 'custom', path='resources/license_plate_recognition/model/LP_detector_nano_61.pt', force_reload=True, source='local')

    # Load model YOLO tùy chỉnh để nhận diện chữ trên biển số xe
    yolo_license_plate = torch.hub.load('resources/license_plate_recognition/yolov5', 'custom', path='resources/license_plate_recognition/model/LP_ocr_nano_62.pt', force_reload=True, source='local')

    # Đặt ngưỡng độ tự tin (confidence threshold) để nhận diện biển số xe
    yolo_license_plate.conf = 0.60
    
    lp_temp = ""

    # Mở camera để đọc khung hình (1 là camera mặc định, 0 là camera ngoài)
    vid = cv2.VideoCapture(id)

    start_time = time.time() 
    # Vòng lặp để xử lý từng khung hình từ camera
    while(True):
        if time.time() - start_time > 15:
            vid.release()
            return None
        # Đọc khung hình từ camera
        ret, frame = vid.read()
        if frame is None:
            return False

        # Sử dụng mô hình YOLO để phát hiện biển số xe trong khung hình
        plates = yolo_LP_detect(frame, size=640)

        # Lấy danh sách các biển số xe được phát hiện (tọa độ bounding box)
        list_plates = plates.pandas().xyxy[0].values.tolist()

        # Tạo một tập hợp để lưu các biển số xe đã đọc
        list_read_plates = set()

        # Lặp qua tất cả các biển số xe được phát hiện
        for plate in list_plates:
            flag = 0  # Cờ để kiểm tra xem biển số đã được nhận diện chưa
            x = int(plate[0]) # Lấy tọa độ xmin của bounding box
            y = int(plate[1]) # Lấy tọa độ ymin của bounding box
            w = int(plate[2] - plate[0]) # Tính toán chiều rộng của bounding box
            h = int(plate[3] - plate[1]) # Tính toán chiều cao của bounding box

            # Cắt hình ảnh của biển số xe từ khung hình
            crop_img = frame[y:y+h, x:x+w]

            lp = ""  # Biến để lưu biển số xe đã nhận diện
                
            # Thử deskew (cân chỉnh góc) biển số xe theo nhiều góc khác nhau để nhận diện
            for cc in range(0, 2):  # Vòng lặp theo trục X
                for ct in range(0, 2):  # Vòng lặp theo trục Y
                    # Đọc biển số xe từ hình ảnh đã cân chỉnh góc
                    lp = helper.read_plate(yolo_license_plate, utils_rotate.deskew(crop_img, cc, ct))
                    # Nếu biển số được nhận diện không phải "unknown"
                    if lp != "unknown":
                        # Thêm biển số đã nhận diện vào danh sách
                        list_read_plates.add(lp)
                        
                        # 
                        if lp_temp != lp:
                            lp_temp = lp
                            print(lp)
                            vid.release()
                            return lp
                        # Đặt cờ để dừng việc tiếp tục nhận diện
                        flag = 1
                        break
                if flag == 1:
                    break