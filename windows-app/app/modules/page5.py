from PyQt5.QtWidgets import QApplication, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QListWidget, QLabel
from PyQt5.QtCore import Qt
import sys
import cv2
import os
import glob
from PyQt5.QtGui import QImage, QPixmap, QFont
from app.resources.coordinates.coordinates_generator import CoordinatesGenerator
from app.modules.utils import *
from app.database.db_manager import get_parking_id, get_cloud_server_url
from app.modules.theme_colors import AppColors
import re

class CoordinatesSetup(QWidget):
    def __init__(self):
        super().__init__()
        
        # Lấy config từ .env
        self.PARKING_ID = get_parking_id()
        self.ClOUD_SERVER_URL = get_cloud_server_url()
        self.image = None
        self.camera_id = None
        self.curentCam = None
        self.setWindowTitle("Coordinates Setup")
        self.setGeometry(100, 100, 900, 600)

        # Main Layout
        main_layout = QVBoxLayout(self)

        # Top Layout with Left and Right sections
        top_layout = QHBoxLayout()

        # Left side: List of cameras (QListWidget)
        self.camera_list = QListWidget()
        self.camera_list.addItem("Camera 0")
        self.camera_list.addItem("Camera 1")
        self.camera_list.addItem("Camera 2")
        self.camera_list.addItem("Camera 3")
        self.camera_list.addItem("Camera 4")
        self.camera_list.addItem("Camera 5")
        self.camera_list.addItem("Camera 6")
        
        # Set fixed width cho camera list để text hiển thị đầy đủ
        self.camera_list.setMinimumWidth(200)
        self.camera_list.setMaximumWidth(250)

        # Set font for QListWidget items (increase font size)
        font = QFont()
        font.setPointSize(12)  # Increase font size here (14 is an example)
        self.camera_list.setFont(font)
        
        # Add the list widget to the left side
        top_layout.addWidget(self.camera_list)

        # Right side: Display camera content (QLabel)
        self.camera_display = QLabel("Select a camera from the list")
        self.camera_display.setAlignment(Qt.AlignCenter)
        self.camera_display.setFixedSize(1500, 750)  # Fixed size for displaying camera feed

        # Add the QLabel for camera feed to the right side
        top_layout.addWidget(self.camera_display)

        # Add top layout to the main layout
        main_layout.addLayout(top_layout)

        # Bottom: Control buttons - Màu gradient tím khớp navigation
        self.bottom_buttons_layout = QHBoxLayout()
        
        # Gradient style cho các nút
        button_style = f"""
            QPushButton {{
                background: {AppColors.get_gradient_style()};
                color: {AppColors.TEXT_WHITE};
                border: none;
                border-radius: 6px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {AppColors.get_hover_gradient_style()};
            }}
        """
        
        btn_Reload = QPushButton("Reload camera list")
        btn_Reload.setFixedHeight(40)
        font.setPointSize(10)
        btn_Reload.setFont(font)
        btn_Reload.setStyleSheet(button_style)

        btn_Update = QPushButton("Update parking spot positions")
        btn_Update.setFixedHeight(40)
        btn_Update.setFont(font)
        btn_Update.setStyleSheet(button_style)

        btn_UpdateREID = QPushButton("Update REID positions")
        btn_UpdateREID.setFixedHeight(40)
        btn_UpdateREID.setFont(font)
        btn_UpdateREID.setStyleSheet(button_style)

        self.bottom_buttons_layout.addWidget(btn_Reload)
        self.bottom_buttons_layout.addWidget(btn_Update)
        self.bottom_buttons_layout.addWidget(btn_UpdateREID)

        # Add bottom buttons layout to main layout
        main_layout.addLayout(self.bottom_buttons_layout)

        # Connect the camera list selection to show the camera feed
        self.camera_list.currentItemChanged.connect(self.display_camera)
        self.camera_list.itemClicked.connect(self.display_camera2)
        btn_Reload.clicked.connect(lambda: self.on_btnReload_click())
        btn_Update.clicked.connect(lambda: self.on_btnUpdate_click(self.image))
        btn_UpdateREID.clicked.connect(lambda: self.on_btnUpdateREID_click(self.image))
            
    def on_btnReload_click(self):
        url = f'{self.ClOUD_SERVER_URL+"coordinates/"+self.PARKING_ID}'
        response = requests.get(url)
        if response.status_code == 200:
            for file_path in glob.glob(os.path.join("app/resources/coordinates/data/frame", "*")):
                os.remove(file_path)
            print("Tải lại danh sách camera thành công")
            for i in response.json():
                img_url = i['image_url']
                response = requests.get(img_url, timeout=10, stream=True)
                if response.status_code == 200:
                    with open("app/resources/coordinates/data/frame/"+str(i['camera_id'])+".jpg", 'wb') as file:
                        file.write(response.content)
                else:
                    print(f'Error downloading image: {response.status_code} - {response.text}')
            
            

    def on_btnUpdate_click(self,image):
        if image is None:
            show_message(self,"Please select a camera to update positions!")
            return
        numbers = re.findall(r'\d+', self.curentCam)
        data_file = "app/resources/coordinates/data/"+self.camera_id+".yml"
            # Mở tệp để ghi tọa độ vào
        coordinates_data = read_yaml(data_file)
        print("Before generate:", coordinates_data)
        with open(data_file, "a+") as points:
            # Khởi tạo đối tượng CoordinatesGenerator với hình ảnh và màu sắc
            try:
                generator = CoordinatesGenerator(image, points, (0, 0, 255),numbers[0], coordinates_data)
            # Gọi phương thức generate để tạo tọa độ
                generator.generate()
                print("After generate:", coordinates_data)
                points.flush()
                os.fsync(points.fileno())

                show_message(self,"Update successful")
                # Gửi tọa độ lên server
                coordinates_data = read_yaml(data_file)
                if self.send_coordinates(self.camera_id, coordinates_data, "coordinates_list"):
                    print("Coordinates sent successfully")
                # cập nhật lại camerafeed
                self.update_video_feed(self.curentCam)

            except Exception as e:
                return 
            
    def on_btnUpdateREID_click(self,image):
        if image is None:
            show_message(self,"Please select a camera to update positions!")
            return
        numbers = re.findall(r'\d+', self.curentCam)
        data_file = "app/resources/coordinates/data/coors_reid/"+self.camera_id+".yml"
            # Mở tệp để ghi tọa độ vào
        coordinates_data = read_yaml(data_file)
        print("Before generate:", coordinates_data)
        with open(data_file, "a+") as points:
            # Khởi tạo đối tượng CoordinatesGenerator với hình ảnh và màu sắc
            try:
                generator = CoordinatesGenerator(image, points, (255, 0, 0),numbers[0], coordinates_data)
            # Gọi phương thức generate để tạo tọa độ
                generator.generate()
                print("After generate:", coordinates_data)
                points.flush()
                os.fsync(points.fileno())

                show_message(self,"Update successful")

                # Gửi tọa độ lên server
                coordinates_data = read_yaml(data_file)
                print("aaa",coordinates_data)
                if self.send_coordinates(self.camera_id, coordinates_data, "coordinates_reid_list"):
                    print("Coordinates sent successfully")
                # cập nhật lại camerafeed
                self.update_video_feed(self.curentCam)

            except Exception as e:
                return
            
    def send_coordinates(self, camera_id, coordinates_data, field_name):
        print(f"Sending {field_name} to server...")


        url = f"{self.ClOUD_SERVER_URL}coordinates/{self.PARKING_ID}/{camera_id}"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            data[0][field_name] = coordinates_data

            url = f"{self.ClOUD_SERVER_URL}coordinates/update/{self.PARKING_ID}/{camera_id}"
            response = requests.put(url, json=data[0])
            return response.status_code == 200

        return False


    def display_camera(self, current, previous):
        """ Simulate showing camera feed. In real app, replace with code that connects to actual cameras. """
        camera_name = current.text()  # Get the selected camera name from the list
        self.curentCam = camera_name
        self.update_video_feed(camera_name)

    def display_camera2(self, current):
        """ Simulate showing camera feed. In real app, replace with code that connects to actual cameras. """
        camera_name = current.text()  # Get the selected camera name from the list
        self.curentCam = camera_name
        self.update_video_feed(camera_name)

    def update_video_feed(self, camera_name):
        path = 'app/resources/coordinates/data/frame/'
        files = os.listdir(path)
        cam_id = int(re.search(r'\d+', camera_name).group(0))
        if cam_id < len(files):
            self.camera_id = os.path.splitext(files[cam_id])[0]
            frame = cv2.imread(path+files[cam_id])
            if frame is None:
                show_message(self,"Cannot read image")
                return
            self.image = frame.copy()
            # Resize the frame to fit the QLabel
            # frame = cv2.resize(frame, (1200, 700))

            frame = self.drawCoordinates(frame)
            height, width, channels = frame.shape
            bytes_per_line = 3 * width
            q_img = QImage(frame.data, width, height, bytes_per_line, QImage.Format_BGR888)
            pixmap = QPixmap.fromImage(q_img)
            self.camera_display.setPixmap(pixmap)
            
        else:   
                self.image = None
                self.camera_id = None
                self.camera_display.setText("No camera feed available")

    def drawCoordinates(self, frame):
        data_file = "app/resources/coordinates/data/" + self.camera_id + ".yml"
        coordinates_data = read_yaml(data_file)
        
        if coordinates_data is not None and isinstance(coordinates_data, list):
            for item in coordinates_data:
                coord = item['coordinate']
                x, y = coord
                cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)  
                cv2.putText(frame, str(item['id']), (x - 5, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)

        data_file_reid = "app/resources/coordinates/data/coors_reid/" + self.camera_id + ".yml"
        coordinates_reid_data = read_yaml(data_file_reid)

        if coordinates_reid_data is not None and isinstance(coordinates_reid_data, list):
            for item in coordinates_reid_data:
                coord = item['coordinate']
                x, y = coord
                cv2.circle(frame, (x, y), 5, (0, 0, 255), -1)  
                cv2.putText(frame, str(item['id']), (x - 5, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1) 

        return frame


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CoordinatesSetup()
    window.show()
    sys.exit(app.exec_())
