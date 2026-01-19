import ast
import cv2
import time
import requests
from app.modules.cloud_api import get_coordinates, update_coordinates, insert_coordinates
from app.modules.utils import write_yaml_file
import os
import dotenv
dotenv.load_dotenv()
# Load camera image to cloudserver
CAMS = ast.literal_eval(os.getenv("TRACKING_CAMERA"))
PARKING_ID = os.getenv("PARKING_ID")
CLOUDINARY_UPLOAD_PRESET = os.getenv("UPLOAD_PRESET")
CLOUDINARY_UPLOAD_URL = os.getenv("CLOUDINARY_UPLOAD_URL")
SLOT_COORDS_PATH = "app/resources/coordinates/slot-data/"
REID_COORDS_PATH = "app/resources/coordinates/reid-data/"
for i,cam_id in enumerate(CAMS):
    print(f"Xử lý camera {i} với cam_id: {cam_id}")
    cap = None
    # CSI CAMERA (IMX219)
    if cam_id == "0":
        gst_pipeline = (
            "nvarguscamerasrc sensor-id=0 ! "
            "video/x-raw(memory:NVMM), width=1280, height=720, format=NV12, framerate=30/1 ! "
            "nvvidconv flip-method=0 ! "
            "video/x-raw, format=BGRx ! "
            "videoconvert ! "
            "video/x-raw, format=BGR ! appsink drop=true"
        )
        cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
    # USB CAMERA
    else:
        device_id = int(cam_id)
        cap = cv2.VideoCapture(device_id, cv2.CAP_V4L2)

        # USB camera settings
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
    time.sleep(1)
    ret, frame = cap.read()
    time.sleep(1)
    ret, frame = cap.read()
    if ret:
        _, buffer = cv2.imencode('.jpg', frame)
        img_bytes = buffer.tobytes()
        # Upload image to Cloudinary
        response = requests.post(
            CLOUDINARY_UPLOAD_URL,
            files={"file": img_bytes},
            data={"upload_preset": CLOUDINARY_UPLOAD_PRESET}
        )
        if response.status_code == 200:
            print("Đã tải hình ảnh lên Cloudinary")
            image_url = response.json()["secure_url"]
            print("Image URL:", image_url)
            cam = get_coordinates(PARKING_ID, str(i))
            if cam is not None:
                cam['image_url'] = image_url
                if update_coordinates(PARKING_ID, str(i), cam):
                    print(f"Đã cập nhật image_url từ cam {i} lên Cloud Server")
                else:
                    print(f"Lỗi khi cập nhật iamge_url từ cam {i} lên Cloud Server")
                # Download coordinates from cloud server
                if cam.get('coordinates_list') is not None:
                    coordinates_data = cam.get('coordinates_list')
                    write_yaml_file(SLOT_COORDS_PATH + str(i) + '.yml', coordinates_data)
                    print(f"Đã tải tọa độ từ cam {i} lên Cloud Server\n")
                else:
                    print("Không có tọa độ nào trên Cloud Server")
                if cam.get('coordinates_reid_list') is not None:
                    reid_coordinates_data = cam.get('coordinates_reid_list')
                    write_yaml_file(REID_COORDS_PATH + str(i) + '.yml', reid_coordinates_data)
                    print(f"Đã tải tọa độ ReID từ cam {i} lên Cloud Server\n")   
        else:
            print("Lỗi khi tải hình ảnh lên Cloudinary:", response.status_code)