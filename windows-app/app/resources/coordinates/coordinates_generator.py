import cv2 as open_cv
import numpy as np
import re
from app.resources.coordinates.colors import COLOR_WHITE
from app.resources.coordinates.colors import COLOR_BLUE


class CoordinatesGenerator:
    # KEY_RESET = ord("r")
    # KEY_QUIT = ord("q")

    def __init__(self, image, output, color,nameCam, coordinates_data):
        self.coordinates_data = coordinates_data
        self.output = output
        self.caption = "Camera "+nameCam
        self.color = color

        self.image = image
        self.image_copy = self.image.copy()
    
        self.ids = 0
        self.spaceName = "A"
        self.coordinate = (0,0)
        self.coordinates = []
        self.titles = []

        open_cv.namedWindow(self.caption, open_cv.WINDOW_GUI_EXPANDED)
        open_cv.setMouseCallback(self.caption, self.__mouse_callback)
        
    def regain(self):
        for item in self.coordinates_data:
            open_cv.circle(self.image, item["coordinate"], 5, (0, 255, 0), -1)     
            open_cv.putText(self.image,str(item["id"]), (item["coordinate"][0]-10,item["coordinate"][1]-10), open_cv.FONT_HERSHEY_SIMPLEX, 0.5, COLOR_BLUE, 2)
            self.titles.append(str(item["id"]))
            self.coordinates.append(item["coordinate"])
            
    def generate(self):
        keys = ""
        self.regain()
        while True:
            open_cv.imshow(self.caption,self.image)
            key = open_cv.waitKey(0)

            if  key == 27:# esc
                
                self.output.seek(0)
                self.output.truncate(0)

                self.image = self.image_copy.copy()
                self.titles.clear()
                self.coordinates.clear()
                self.ids = 0
                keys = ""
            elif key == ord('\r'):# enter
                break
            elif key >= 48 and key <=57:# chọn số cho ô
                keys += str(chr(key))
                self.ids = int(keys)
            elif key == ord('\b'):  # Sử dụng '\b' để biểu thị Backspace
                self.undo()
            else: #Chọn tên cho ô
                self.spaceName = chr(key)
                self.ids = 0
                keys = ""
            
        open_cv.destroyWindow(self.caption)
        
    def undo(self):# ham quay lai net truoc do   
        if len(self.coordinates) == 0:
            return
        
        self.image = self.image_copy.copy()
        if self.ids > 0:
            self.ids -=1 # quay lai id truoc do
        
        self.coordinates.pop()
        self.titles.pop() 

        # Đọc và cập nhật lại nội dung file YAML
        self.output.seek(0)  # Di chuyển con trỏ về đầu file
        lines = self.output.readlines()  # Đọc tất cả dòng

        # Loại bỏ bản ghi cuối cùng (giả sử mỗi bản ghi là 2 dòng: id và coordinate)
        if len(lines) >= 2:
            lines = lines[:-2]  # Bỏ 2 dòng cuối cùng

        # Ghi lại nội dung vào file
        self.output.seek(0)  # Quay lại đầu file
        self.output.truncate(0)  # Xóa toàn bộ nội dung cũ
        self.output.writelines(lines)  # Ghi lại các dòng còn lại
                    
        # Vẽ lại tất cả các điểm còn lại
        for stt, coordinate in enumerate(self.coordinates):
            open_cv.circle(self.image, coordinate, 5, (0, 255, 0), -1)
            open_cv.putText(
                self.image, 
                str(self.titles[stt]), 
                (coordinate[0] - 10, coordinate[1] - 10), 
                open_cv.FONT_HERSHEY_SIMPLEX, 
                0.5, 
                (255, 0, 0),  # COLOR_BLUE
                2
            )
          
    def __mouse_callback(self, event, x, y, flags, params):

        if event == open_cv.EVENT_LBUTTONDOWN:
            self.coordinate=(x, y)
            self.coordinates.append(self.coordinate)
            self.__handle_done()

        open_cv.imshow(self.caption, self.image)

    def __handle_done(self):
        # Vẽ dấu chấm
        open_cv.circle(self.image, self.coordinate, 5, (0, 255, 0), -1)
        # Lưu vào file yml
        self.output.write("- id: " + str(self.spaceName + str(self.ids)) + "\n  coordinate: [" +
                           str(self.coordinate[0]) +", "+str(self.coordinate[1])+ "]\n")
        # Vẽ tên
        open_cv.putText(self.image, str(self.spaceName+str(self.ids)), (self.coordinate[0]-10,self.coordinate[1]-10), open_cv.FONT_HERSHEY_SIMPLEX, 0.5, COLOR_BLUE, 2)
        if self.spaceName == "":
            self.spaceName = "A"
        self.titles.append(str(self.spaceName+str(self.ids)))

        self.ids += 1   
        
        
        
