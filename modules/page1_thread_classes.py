
# import cv2
# import time
# import vlc
# import requests
# import json
# import torch
# from ultralytics import YOLO
# from datetime import datetime
# from threading import Thread
# from pynput import keyboard
# from PyQt5.QtCore import QThread, pyqtSignal
# from pymongo import MongoClient
# from PyQt5.QtCore import QThread, pyqtSignal
# from resources.print_bill.print_bill import *
# from resources.license_plate_recognition.detectLicense import detectLicense
# from modules.utils import read_yaml, draw_bounding_boxes_with_confidence, detect_objects, draw_points_and_ids, check_occlusion, show_message


# # Luồng cam detect chổ trống
# class CameraThread(QThread): 
#     frame_captured = pyqtSignal(object)
#     message_signal = pyqtSignal(str)  # Tín hiệu truyền thông báo dạng chuỗi

#     def __init__(self, camera_page):
#         super().__init__()
#         print("Khởi tạo Thread camera 1")
#         self.running = False
#         self.cap = []
#         self.cameraP = camera_page
#         self.warning_active = False  # Cờ để theo dõi trạng thái cảnh báo
#         self.occupieds = None
#         self.coordinates_url = 'resources/coordinates/data/coordinates_'
#         # test
#         self.model_yolo_detect_car_url = 'resources/models/yolov8n.pt'
#         #test
#         #self.model_yolo_detect_car_url = 'resources/models/detect-car-yolov8n-v2.pt' #uncmt
#         self.model_yolo_detect_fire_url = 'resources/models/detect-fire-yolov8n-v2.pt'
#         # URL của server Flask
#         self.server_url = " http://192.168.1.81:5001/update"
#         self.server_url = " http://172.20.10.2:5001/update"

#     def run(self):
#         """Start capturing frames from the camera."""
#         self.running = True
#         print("Thread camera 1 started")
#         # Load dữ liệu tọa độ
#         coordinates_datas = []
#         for i in self.cameraP.ids:
#             coordinates_data = read_yaml(self.coordinates_url+str(i)+'.yml')
#             if coordinates_data is None or (isinstance(coordinates_data, (dict, list)) and len(coordinates_data) == 0):
#                 coordinates_datas.append(None)
#             coordinates_datas.append(coordinates_data)
        
#         # Load model YOLOv8
#         model = YOLO(self.model_yolo_detect_car_url)
#         model2 = YOLO(self.model_yolo_detect_fire_url) 

#         device = "cuda" if torch.cuda.is_available() else "cpu"
#         print(f"Đang chạy trên: {device}")
        
#         # import cam detect
#         self.cap.clear()
#         for i in self.cameraP.ids:
#             #### test
#             self.cap.append(cv2.VideoCapture("test_data/video/test.mp4"))
#             #### test
#             # self.cap.append(cv2.VideoCapture(i, cv2.CAP_MSMF)) # uncmt
#         while self.running and not self.warning_active:
#             time.sleep(1)
#             frames = []
#             empties = []
#             occupieds = []
#             fire = False 
#             flag = True
#             # Vòng for chính cho các cam
#             for stt, cap in enumerate(self.cap):#stt tương ứng với stt trong ids
#                 # test
#                 current_frame = cap.get(cv2.CAP_PROP_POS_FRAMES)
#                 cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame + 30)
#                 # test
#                 ret, frame = cap.read()
#                 if frame is None: # Có camera bị mất kết nối
#                     flag = False    
#                     self.message_signal.emit("Camera "+str(self.cameraP.ids[stt])+" bị mất kết nối, hãy kiểm tra và chạy lại chương trình!")  # Phát tín hiệu
#                     break
#                 detected_boxes2, confidences2, classes2 = detect_objects(model2, frame,0.4, device=device)
#                 detected_boxes, confidences, classes = detect_objects(model, frame, device=device)
                
#                 fire_boxes = []
#                 fire_confidences = []
#                 for i in range(len(classes2)):
#                     fire_boxes.append(detected_boxes2[i])
#                     fire_confidences.append(confidences2[i])
#                 draw_bounding_boxes_with_confidence(frame, fire_boxes, fire_confidences, classes2)
#                 car_boxes = []
#                 car_confidences = []
#                 for i in range(len(classes)):
#                     car_boxes.append(detected_boxes[i])
#                     car_confidences.append(confidences[i])

#                 # Kiểm tra các tọa độ bị che khuất và không bị che
#                 if coordinates_datas[stt] is not None:
#                     hidden_ids, visible_ids = check_occlusion(coordinates_datas[stt], car_boxes)

#                     for i in hidden_ids:
#                         occupieds.append(i)
#                     for i in visible_ids:
#                         empties.append(i)

#                     # Vẽ dấu chấm và ID tại các tọa độ trong file YAML
#                     draw_points_and_ids(frame, coordinates_datas[stt], hidden_ids)

#                 # Vẽ các bounding box và độ tin cậy trên ảnh cho ô tô
#                 draw_bounding_boxes_with_confidence(frame, car_boxes, car_confidences, classes) 

#                 if len(classes2) > 0: # đánh dấu cho luồng báo động
#                     fire = True
#                 frames.append(frame) # ds các frame từ nhiều cam

#             # tiếp tục chương trình nếu không có cam nào bị lỗi
#             if flag:
#                 currentFrame = self.cameraP.currentCamShow # đánh dấu frame của cam hiển thị ở trang chính giao diện
#                 for i,id in enumerate(self.cameraP.ids):# map stt của frame trong ds tương ứng với stt của ids trong ds
#                     if id == currentFrame:
#                         currentFrame = i
#                 self.frame_captured.emit(frames[currentFrame])
#                 if fire:
#                     self.warning()
                
#                 if self.occupieds != occupieds:# chỉ cập nhật vị trí ô trống khi có sự thay đổi
#                     self.occupieds = occupieds
#                     list1 = self.convertResult(occupieds)
#                     list2 = self.convertResult(empties)
#                     content = self.showResult(list1,list2)# post api area
#                     print(self.direction(list2))
#                     # Post data cho 2 trang web hiển thị (thay thế cho bảng led)
#                     # Dữ liệu gửi lên server
#                     data = {
#                         "page_a": self.direction(list2),
#                         "page_b": content
#                     }
#                     try:
#                         # Gửi POST request để cập nhật dữ liệu cho các trang
#                         response = requests.post(self.server_url, json=data)
#                         if response.status_code == 200:
#                             print("Cập nhật dữ liệu bảng led thành công.")
#                         else:
#                             print(f"Lỗi khi cập nhật dữ liệu cho bảng led: {response.status_code} - {response.text}")
#                     except requests.exceptions.ConnectionError:
#                         # Xử lý khi không thể kết nối đến server
#                         print("Không thể kết nối tới server. Đã bỏ qua yêu cầu cập nhật dữ liệu cho bảng led.")
#                     except requests.exceptions.RequestException as e:
#                         # Xử lý các lỗi khác liên quan đến request
#                         print(f"Lỗi khi gửi yêu cầu: {e}")
#             else:
#                 self.running = False

#         # Đóng cam
#         for cap in self.cap:
#             cap.release()

#     # Convert dữ liệu chỉ hướng
#     def direction(self,list):
#         left = ""
#         right = ""
#         for i in list:
#             if left == "" and (i[0][0] == "C" or i[0][0] == "D"):
#                 left = "⬅️ "+i[0]
#             if right == "" and (i[0][0] == "A" or i[0][0] == "B"):
#                 right = i[0]+ " ➡️"

#         return left+" | "+right

#     def showResult(self,list1,list2):
#         # Hợp hai danh sách
#         combined = list1 + list2
#         # Phân loại các phần tử vào nhóm
#         groups = {}
#         for sublist in combined:
#             for item in sublist:
#                 key = item[0]  # Lấy ký tự đầu tiên ('A', 'B', ...)
#                 if key not in groups:
#                     groups[key] = []  # Tạo nhóm mới nếu chưa có
#                 groups[key].append(item)

#         # Tính số lượng phần tử của từng nhóm
#         total_group_counts = {key: len(items) for key, items in groups.items()}  # Tổng số trong cả 2 danh sách
#         list1_group_counts = {}  # Số lượng trong list1
#         for sublist in list1:
#             for item in sublist:
#                 key = item[0]
#                 list1_group_counts[key] = list1_group_counts.get(key, 0) + 1

#         # Tính số lượng phần tử có sẵn trong mỗi nhóm trong list1
#         results = {}
#         for key in groups:
#             available = list1_group_counts.get(key, 0)  # Số phần tử có sẵn trong list1
#             total = total_group_counts[key]  # Tổng số phần tử trong nhóm từ cả 2 danh sách
#             results[key] = (available, total)

#         # Xuất kết quả theo định dạng yêu cầu
#         print(f"{'Area':<10}{'Ocoordinate/Total':<20}{'Available':<10}")
#         total_occupied = 0
#         content = ""
#         for key in results:
#             occupied, total = results[key]
#             total_occupied += occupied
#             content += f"{key:<10}"+"\n"+f"{occupied}/{total:<20}"+"\n"+f"{total-occupied:<10}"+"\n"
#             print(f"{key:<10}{occupied}/{total:<20}{total-occupied:<10}")

#             # post api parking-area
#             url = self.cameraP.url_cloud_server+"/api/parking_areas/" # tên api giống với tên collection
#             # Dữ liệu cần gửi
#             data = {
#                 "parking_id": self.cameraP.parking_id,
#                 "area_name": key,
#                 "available": total-occupied,
#                 "occupied": occupied,
#                 "total": total
#             }
#             try:
#                 # Gửi yêu cầu POST với dữ liệu JSON
#                 response = requests.post(url, json=data)
#                 if response.status_code == 200:
#                     print("Gửi dữ liệu parking area thành công.")
#                 else:
#                     print(f"Lỗi khi gửi dữ liệu parking area: {response.status_code} - {response.text}")
#             except requests.exceptions.ConnectionError:
#                 # Xử lý khi không thể kết nối đến server
#                 print("Không thể kết nối tới server. Đã bỏ qua yêu cầu gửi parking area.")
#             except requests.exceptions.RequestException as e:
#                 # Xử lý các lỗi khác liên quan đến request
#                 print(f"Lỗi khi gửi yêu cầu gửi dữ liệu parking area: {e}")

#         # Tổng cộng
#         total_all = sum(total for _, total in results.values())
#         content += f"{'All':<10}"+"\n"+f"{total_occupied}/{total_all:<20}"+"\n"+f"{total_all-total_occupied:<10}"
#         print(f"{'All':<10}{total_occupied}/{total_all:<20}{total_all-total_occupied:<10}")

#         self.cameraP.total_available = total_all-total_occupied # total_available
#         return content


#     def convertResult(self, arr):
#         # Xóa trùng và chuyển str
#         arr = list(set(arr))
#         # Tạo từ điển để lưu các nhóm
#         groups = {}

#         # Phân loại các phần tử dựa trên ký tự đầu tiên
#         for item in arr:
#             key = item[0]  # Lấy ký tự đầu tiên
#             if key not in groups:
#                 groups[key] = []  # Tạo nhóm mới nếu chưa tồn tại
#             groups[key].append(item)  # Thêm phần tử vào nhóm

#         # Sắp xếp từng nhóm
#         for key in groups:
#             groups[key] = sorted(groups[key])

#         # Sắp xếp các nhóm theo thứ tự chữ cái của ký tự đầu tiên ('A', 'B', 'C', ...)
#         sorted_groups = sorted(groups.items(), key=lambda x: x[0])  # Sắp xếp theo key (ký tự đầu tiên)
#         # Chuyển từ từ điển sang danh sách các nhóm đã sắp xếp
#         result = [group for _, group in sorted_groups]

#         return result


#     def warning(self):
#         """Chạy báo động âm thanh và chờ phím Space để tiếp tục."""
#         self.warning_active = True  # Tạm dừng camera
#         player = vlc.MediaPlayer('resources/mp3/security-alarm-63578.mp3')
#         player.play()

#         def on_press(key):
#             if key == keyboard.Key.space:
#                 player.stop()  # Dừng âm thanh
#                 return False  # Kết thúc lắng nghe phím

#         # Sử dụng pynput để lắng nghe phím Space
#         listener = keyboard.Listener(on_press=on_press)
#         listener.start()
#         listener.join()  # Chờ người dùng nhấn phím Space

#         self.warning_active = False  # Kích hoạt lại camera

#     def stop(self):
#         """Dừng camera."""
#         self.running = False
#         self.warning_active = False  # Reset trạng thái cảnh báo
#         self.quit()
#         self.wait()
#         print("Thread camrea 1 stopped.")



# # Luồng xử lý xe ra vào, máy đọc thẻ từ và cam độc QR, biển số
# class CameraThread2(QThread):# cần chú ý có nhiều luồng ngoại lệ đến từ việc đống mở cam và nhận dữ liệu từ máy đọc...
# # nếu bị lag hãy dùng timer 
#     def __init__(self, camera_page):
#         super().__init__()
#         print("Khởi tạo Thread camera 2")
#         self.running = False
#         self.cameraP = camera_page
#         self.listener = None
#         self.card_data = ""
#         self.last_time = time.time()
#         self.cam_in = self.cameraP.combobox1.currentIndex()
#         self.cam_out = self.cameraP.combobox2.currentIndex()
#         # # Kết nối tới MongoDB cục bộ
#         self.client = MongoClient("mongodb://localhost:27017/")
#         # Cơ sở dữ liệu local
#         self.db = self.client["server_local"]
#         self.mp3_url = 'resources/mp3'

#     def run(self):
#         print("Thread camera2 started")
#         # Khởi tạo listener để lắng nghe sự kiện phím
#         self.listener = keyboard.Listener(on_press=self.on_press)
#         self.listener.start()
#         self.listener.join()  # Chờ luồng kết thúc

#     def on_press(self, key):
#         key_name = str(key).replace("'", "")  # Chuyển phím về dạng chuỗi
#         try:# trường hợp xe đi vào
#             if key_name == "Key.f1":# truong hop khach hang dang ky thang co ma qr
#                 # kiem tra bai do con slot khong
#                 if self.cameraP.total_available == 0:# het cho
#                     Thread(target=self.play_sound, args=(self.mp3_url+'/het-slot.mp3',)).start()
#                 else: # Còn chỗ
#                     # đảm bảo trường hợp có cùng user_id và nhiều license
#                     # mở camera chụp mã qr
#                     Thread(target=self.play_sound, args=(self.mp3_url+'/quet-ma.mp3',)).start()
#                     vid = cv2.VideoCapture(self.cam_in,cv2.CAP_MSMF)
#                     user_id = None
#                     start_time = time.time() 

#                     # Vòng lặp chờ quét mã QR trong 15s
#                     while(True):
#                         # tự đóng camera sau 15s
#                         if time.time() - start_time > 15:
#                             break
#                         ret, frame = vid.read()
#                         if frame is None:
#                             break
#                         # Khởi tạo QRCodeDetector
#                         qr_decoder = cv2.QRCodeDetector()
#                         # Giải mã mã QR
#                         data, points, _ = qr_decoder.detectAndDecode(frame)
#                         if data:
#                             vid.release()
#                             user_id = data
#                             print(user_id)
#                             break

#                     if user_id is not None:# da quet duoc ma qr
#                         Thread(target=self.play_sound, args=(self.mp3_url+'/scan.mp3',)).start()
#                         collection_cus = self.db["Customer"]
#                         # tim khach hang voi ma
#                         result = collection_cus.find_one({"user_id": user_id})
#                         if result is None:# mã không hợp lệ
#                             Thread(target=self.play_sound, args=(self.mp3_url+'/ma-khong-hop-le.mp3',)).start()
#                         else:# ma hop le
#                             license = detectLicense(self.cam_in)
#                             if license is False:# cam mất kết nối
#                                 Thread(target=self.play_sound, args=(self.mp3_url+'/cam-mat-ket-noi.mp3',)).start()
#                                 return
#                             if license is None: # không nhận dạng được biển số
#                                 Thread(target=self.play_sound, args=(self.mp3_url+'/khong-nhan-dang-duoc-bien-so.mp3',)).start()
#                                 return
#                             else:
#                                 register_list = result["register_list"]
#                                 register = None
#                                 expired_date = None
#                                 temp = False
#                                 # Duyệt qua danh sách để tìm license khớp
#                                 for register in register_list:
#                                     if register["license_plate"] == license:
#                                         temp = True
#                                         expired_date = register.get("expired")
#                                         break
#                                 if not temp:
#                                     # thong bao bien so xe chua duoc dang ky
#                                     Thread(target=self.play_sound, args=(self.mp3_url+'/bien-so-xe-chua-dk.mp3',)).start()
#                                 else:# bien so xe da duoc dang ky
#                                     # Lấy ngày hiện tại
#                                     current_date = datetime.now()
#                                     # So sánh expired với ngày hiện tại
#                                     date1 = datetime.fromisoformat(expired_date['$date'].replace('Z', '+00:00'))

#                                     # Parse Python datetime (offset-naive)
#                                     date2 = datetime.fromisoformat(str(current_date))

#                                     # Convert both to offset-naive for comparison
#                                     date1_naive = date1.replace(tzinfo=None)
#                                     date2_naive = date2  # Already naive
#                                     if date1_naive >= date2_naive:# con han
#                                         data = {
#                                             "id_card": user_id,
#                                             "license": license,
#                                             "customer_type": "guest",
#                                             "time_in": datetime.now()
#                                         }
#                                         collection_pro = self.db["Provisional_List"]
#                                         collection_pro.insert_one(data)
#                                         Thread(target=self.play_sound, args=(self.mp3_url+'/xe-di-vao.mp3',)).start()  
#                                     else: # thong bao het han
#                                         Thread(target=self.play_sound, args=(self.mp3_url+'/gia-han.mp3',)).start()                         


#             elif key_name == "Key.f2":# truong hop xe ra
#                 Thread(target=self.play_sound, args=(self.mp3_url+'/quet-ma.mp3',)).start()
#                 vid = cv2.VideoCapture(self.cam_out, cv2.CAP_MSMF)
#                 user_id = None
#                 start_time = time.time() 

#                 # Vòng lặp chờ quét mã QR trong 15s
#                 while(True):
#                     # tự đóng camera sau 15s
#                     if time.time() - start_time > 15:
#                         vid.release()
#                         break
#                     ret, frame = vid.read()
#                     if frame is None:
#                         break
#                     # Khởi tạo QRCodeDetector
#                     qr_decoder = cv2.QRCodeDetector()
#                     # Giải mã mã QR
#                     data, points, _ = qr_decoder.detectAndDecode(frame)
#                     if data:
#                         vid.release()
#                         user_id = data
#                         print(user_id)
#                         break

#                 if user_id is not None:# da quet duoc ma qr
#                     Thread(target=self.play_sound, args=(self.mp3_url+'/scan.mp3',)).start()
#                     collection_pro = self.db["Provisional_List"]
#                     result = collection_pro.find_one({"id_card":user_id})
#                     if result is None:# mã không hợp lệ
#                         Thread(target=self.play_sound, args=(self.mp3_url+'/ma-khong-hop-le.mp3',)).start()
#                     else:
#                         license = detectLicense(self.cam_out)
#                         if license is False:
#                                 Thread(target=self.play_sound, args=(self.mp3_url+'/cam-mat-ket-noi.mp3',)).start()
#                                 return
#                         if license is None:
#                             Thread(target=self.play_sound, args=(self.mp3_url+'/khong-nhan-dang-duoc-bien-so.mp3',)).start()
#                             return
#                         elif result["license"] == license:
#                             # post api history
#                             url = self.cameraP.url_cloud_server+"/api/histories/" # tên api giống với tên collection
#                             # Dữ liệu cần gửi
#                             time_out = datetime.now()
#                             time_in = result["time_in"]

#                             # Tính thời gian gửi xe
#                             parking_time = (time_out - time_in).total_seconds() / 3600
#                             parking_time = f"{parking_time:.2f}"

#                             collection_history = self.db["History"]
#                             data = {
#                                     "license": license,
#                                     "time_in": time_in,
#                                     "time_out": time_out,
#                                     "parking_time": parking_time,
#                                     "customer_type": "guest"
#                                 }
#                             history = collection_history.insert_one(data)

#                             # Chuẩn bị dữ liệu và chuyển datetime sang chuỗi
#                             data = {
#                                 "user_id": user_id,
#                                 "parking_id": self.cameraP.parking_id,
#                                 "license": license,
#                                 "time_in": time_in.isoformat(),  # Chuyển sang chuỗi
#                                 "time_out": time_out.isoformat(),  # Chuyển sang chuỗi
#                                 "parking_time": str(parking_time)
#                             }                   
#                             try:
#                                 # Gửi yêu cầu POST với dữ liệu JSON
#                                 response = requests.post(url, json=data)
#                                 if response.status_code == 200:
#                                     print("Dữ liệu history được gửi thành công.")
#                                 else:
#                                     print(f"Lỗi khi gửi dữ liệu history: {response.status_code} - {response.text}")
#                             except requests.exceptions.ConnectionError:
#                                 # Xử lý khi không thể kết nối đến server
#                                 print("Không thể kết nối tới server. Đã bỏ qua yêu cầu gửi history.")
#                             except requests.exceptions.RequestException as e:
#                                 # Xử lý các lỗi khác liên quan đến request
#                                 print(f"Lỗi khi gửi yêu cầu gửi history: {e}")

#                             # xóa thông tin tạm
#                             collection_pro.delete_one({"$and": [{"id_card": user_id}, {"license": license}]})
#                             # âm thanh xe ra
#                             Thread(target=self.play_sound, args=(self.mp3_url+'/xe-di-ra.mp3',)).start()
#                         else:
#                             # âm thanh cảnh báo
#                             Thread(target=self.play_sound, args=(self.mp3_url+'/bien-so-xe-khong-khop.mp3',)).start()

#             # Nhận dữ liệu từ máy đọc thẻ
#             elif key_name == "Key.enter":  # Kết thúc khi nhấn Enter (thường là kết thúc đầu đọc thẻ)
#                 print(f"Card Data: {self.card_data}")
#                 if len(self.card_data) == 10:# đảm bảo dữ liệu là từ máy đọc , dùng regex
#                     # Tạo hoặc sử dụng một collection
#                     collection_pro = self.db["Provisional_List"]
#                     #Kiểm tra xem xe vào hay ra
#                     result = collection_pro.find_one({"id_card": self.card_data})
#                     if result is None:# truong hop xe di vao
#                         #kiem tra bai xe con slot khong
#                         if self.cameraP.total_available == 0:# het cho
#                             Thread(target=self.play_sound, args=(self.mp3_url+'/het-slot.mp3',)).start()
#                         else:# con cho
#                             # call model detect license
#                             license = detectLicense(self.cam_in)
#                             if license is False:
#                                 Thread(target=self.play_sound, args=(self.mp3_url+'/cam-mat-ket-noi.mp3',)).start()
#                                 return
#                             if license is None:
#                                 Thread(target=self.play_sound, args=(self.mp3_url+'/khong-nhan-dang-duoc-bien-so.mp3',)).start()
#                                 return
#                             else:
#                                 #insert trường hợp xe đi vào
#                                 data = {
#                                     "id_card": self.card_data,
#                                     "license": license,
#                                     "customer_type": "visitor",# guest
#                                     "time_in": datetime.now()
#                                 }
#                                 collection_pro.insert_one(data)
#                                 Thread(target=self.play_sound, args=(self.mp3_url+'/xe-di-vao.mp3',)).start()   

#                     else: #trường hợp xe đi ra
#                         # call model detect license
#                         cam_out = self.cameraP.combobox2.currentIndex()
#                         license = detectLicense(cam_out)
#                         if license is False:
#                                 Thread(target=self.play_sound, args=(self.mp3_url+'/cam-mat-ket-noi.mp3',)).start()
#                                 return
#                         if license is None:
#                             Thread(target=self.play_sound, args=(self.mp3_url+'/khong-nhan-dang-duoc-bien-so.mp3',)).start()
#                             return
#                         else:
#                             if result["license"] == license:
#                                 # tạo hóa đơn
#                                 collection_history = self.db["History"]

#                                 current_date = datetime.now()
#                                 # Tách các giá trị ngày, tháng, năm
#                                 day = current_date.day
#                                 month = current_date.month
#                                 year = current_date.year
#                                 date = f"{day}/{month}/{year}"

#                                 time_in = result["time_in"]
#                                 time_out = datetime.now()
#                                 parking_time = time_out-time_in
#                                 parking_time = parking_time.total_seconds()/3600
#                                 parking_time = f"{parking_time:.2f}"
#                                 total_price = 50000
#                                 data = {
#                                     "license": license,
#                                     "time_in": time_in,
#                                     "time_out": time_out,
#                                     "parking_time": parking_time,
#                                     "customer_type": "visitor"
#                                 }
#                                 history = collection_history.insert_one(data)
#                                 # in hóa đơn
#                                 write_file_pdf(date,license,time_in,time_out,parking_time,total_price)
#                                 printting()
#                                 # xóa thông tin tạm
#                                 collection_pro.delete_one({"$and": [{"id_card": self.card_data}, {"license": license}]})
#                                 # âm thanh xe ra
#                                 Thread(target=self.play_sound, args=(self.mp3_url+'/xe-di-ra.mp3',)).start()
#                             else:
#                                 # âm thanh cảnh báo
#                                 Thread(target=self.play_sound, args=(self.mp3_url+'/bien-so-xe-khong-khop.mp3',)).start()

#                 self.card_data = ""  # Reset dữ liệu để đọc thẻ mới

#             else: # xử lý các trường hợp nhập liệu bao gồm từ bàn phím và máy đọc
#                 if time.time() - self.last_time < 0.1: #trường hợp máy đọc nhập liệu không phải lần nhập đầu tiên 
#                     self.card_data += key_name 
#                 else: # trường hợp nhập liệu từ bàn phím hoặc máy đọc nhập liệu lần đầu tiên
#                     self.card_data = key_name

#                 self.last_time = time.time() # cập nhật thời gian nhập gần nhất

#         except AttributeError:
#             pass

#     def stop(self):
#         if self.listener:
#             print("Thread camera 2 stopped.")
#             self.listener.stop()

#     def soundEffect(self,path):
#         player = vlc.MediaPlayer(path)
#         player.play()

#     def play_sound(self,path):
#         player = vlc.MediaPlayer(path)
#         player.play()

# # Luồng đồng bộ dữ liệu khách hàng từ cloud server
# class Sync_Thread(QThread):
#     # Tạo tín hiệu (signal) để gửi thông báo về giao diện chính
#     update_signal = pyqtSignal(str)

#     def __init__(self, camera_page):
#         super().__init__()
#         print("Khởi tạo Thread Sync")
#         self.running = False
#         self.cameraP = camera_page
#         # # Kết nối tới MongoDB cục bộ
#         self.client = MongoClient("mongodb://localhost:27017/")
#         # Tạo hoặc sử dụng một cơ sở dữ liệu
#         self.db = self.client["server_local"]

#     def run(self):
#         """ Phương thức thực thi công việc đồng bộ dữ liệu """
#         self.running = True
#         print("Thread sync started")
#         while self.running:
#             self.sync_registers()
#             time.sleep(10)  # Lặp lại sau mỗi 10 giây
    
#     def stop(self):
#         """ Dừng luồng """
#         print("Thread Sync stopped.")
#         self.running = False

#     # get api register
#     def sync_registers(self):
#         print("Đang đồng bộ dữ liệu khách hàng")
#         """ Đồng bộ dữ liệu với server cloud và MongoDB """
#         collection = self.db["Customer"]
#         url = self.cameraP.url_cloud_server+"/api/registers/get_register_list" # tên api giống với tên collection
#         try:
#             # Gửi yêu cầu POST đến server cloud
#             # Sử dụng parking_id từ cameraP thay vì hard-coded
#             data={
#                 "parking_id": self.cameraP.parking_id
#                 }
#             response = requests.post(url, json=data)
#             #Kiểm tra mã phản hồi
#             print(f"Response Status Code: {response.status_code}")
#             if response.status_code == 200:
#                 try:
#                     # Kiểm tra nội dung JSON trả về
#                     registers = response.json()["data"]
#                     for register in registers:
#                         user_id = register["user_id"]
#                         result = collection.find_one({"user_id": user_id})
#                         if result is None:  # Trường hợp khách hàng mới
#                             data = {
#                                 "user_id": user_id,
#                                 "register_list": register["register_list"],
#                             }
#                             collection.insert_one(data)
#                         elif len(register["register_list"]) != len(result["register_list"]):  # Trường hợp khách hàng đăng ký thêm số xe mới
#                             collection.delete_one({"user_id": user_id})
#                             data = {
#                                 "user_id": user_id,
#                                 "register_list": register["register_list"],
#                             }
#                             collection.insert_one(data)
#                 except Exception as e:
#                     print(f"Error parsing JSON: {e}")
#             else:
#                 print(f"Không thể cập nhật khách hàng: {response.status_code}")
#         except Exception as e:
#             print(f"Máy chủ không phản hồi, không thể đồng bộ khách hàng: {e}")

#             # Cập nhật tín hiệu (signal) tới giao diện chính nếu có lỗi
#             self.update_signal.emit(f"Error syncing registers: {e}")