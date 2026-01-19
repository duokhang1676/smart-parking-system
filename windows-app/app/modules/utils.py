import yaml
import cv2 
import requests
import time
import vlc
import keyboard
from PyQt5.QtWidgets import QMessageBox
import os

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

def show_message(self,txt):
        """Hàm hiển thị thông báo"""
        # Tạo QMessageBox
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Thông báo")
        msg_box.setText(txt)
        msg_box.setIcon(QMessageBox.Information)  # Loại biểu tượng (Thông tin, Cảnh báo, Lỗi, v.v.)
        msg_box.setStandardButtons(QMessageBox.Ok)  # Thêm các nút

        # Hiển thị hộp thoại và xử lý phản hồi
        response = msg_box.exec_()

# Kiểm tra xem điểm (x, y) có nằm trong bounding box không
def is_point_in_box(x, y, box):
    x_min, y_min, x_max, y_max = box
    return x_min <= x <= x_max and y_min <= y <= y_max

# Chạy YOLOv8 để phát hiện các đối tượng
def detect_objects(model, image, confidence_threshold=0.5, device='cuda'):
    results = model(image,  device=device) 

    # Lấy các bounding boxes, độ tin cậy, và class_id từ kết quả
    boxes = results[0].boxes.xyxy  # Lấy bounding boxes từ kết quả phát hiện
    confidences = results[0].boxes.conf  # Lấy độ tin cậy của các bounding box
    class_ids = results[0].boxes.cls  # Lấy các class_id

    # Lấy tên lớp (class names) từ class_ids
    class_names = [results[0].names[int(class_id)] for class_id in class_ids]

    # Lọc các đối tượng có độ tin cậy >= confidence_threshold
    filtered_boxes = []
    filtered_confidences = []
    filtered_classes = []

    for box, conf, class_id, class_name in zip(boxes, confidences, class_ids, class_names):
        if conf >= confidence_threshold:  # Kiểm tra nếu độ tin cậy vượt qua ngưỡng
            filtered_boxes.append(box)
            filtered_confidences.append(conf)
            filtered_classes.append(class_name)

    return filtered_boxes, filtered_confidences, filtered_classes  # Trả về bounding boxes, độ tin cậy và lớp đối tượng đã lọc


# Hàm vẽ dấu chấm và ID tại tọa độ
def draw_points_and_ids(image, coordinates_data, hidden_ids):
    for item in coordinates_data:
        coord = item['coordinate']
        x, y = coord
        # Kiểm tra xem điểm có bị che khuất hay không
        if item['id'] in hidden_ids:
            # Vẽ dấu chấm màu đỏ nếu tọa độ bị che khuất
            cv2.circle(image, (x, y), 5, (0, 0, 255), -1)  # Dấu chấm màu đỏ
        else:
            # Vẽ dấu chấm màu xanh lá nếu không bị che khuất
            cv2.circle(image, (x, y), 5, (0, 255, 0), -1)  # Dấu chấm màu xanh lá
        # Vẽ ID gần dấu chấm
        cv2.putText(image, str(item['id']), (x - 5, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)  # ID màu đỏ

# Hàm kiểm tra các điểm bị che khuất
def check_occlusion(coordinates_data, detected_boxes):
    hidden_ids = []  # Danh sách chứa các ID bị che khuất
    visible_ids = []  # Danh sách chứa các ID không bị che khuất
    
    for item in coordinates_data:
        coord = item['coordinate']
        x, y = coord
        is_hidden = False
        
        # Kiểm tra xem điểm có nằm trong bất kỳ bounding box nào không
        for box in detected_boxes:
            if is_point_in_box(x, y, box):
                is_hidden = True
                break
        
        if is_hidden:
            hidden_ids.append(item['id'])
        else:
            visible_ids.append(item['id'])
    
    return hidden_ids, visible_ids

# Hàm vẽ bounding boxes và độ tin cậy trên ảnh
def draw_bounding_boxes_with_confidence(image, boxes, confidences, classes):
    for i, box in enumerate(boxes):
        x_min, y_min, x_max, y_max = box
        confidence = confidences[i]
        
        # Vẽ bounding box
        cv2.rectangle(image, (int(x_min), int(y_min)), (int(x_max), int(y_max)), (0, 255, 0), 2)
        
        # Vẽ độ tin cậy gần bounding box
        cv2.putText(image,str(classes[i]) +": "+str(f'{confidence:.2f}'), (int(x_min), int(y_min) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)