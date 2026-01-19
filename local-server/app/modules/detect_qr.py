import os
import cv2
import time
import threading
from app.modules import globals
from dotenv import load_dotenv
from app.modules.utils import play_sound
load_dotenv()
def start_detect_qr():
    cap = cv2.VideoCapture(int(os.getenv("QR_CAMERA")))
    # Khởi tạo QRCodeDetector
    qr_decoder = cv2.QRCodeDetector()
    while True:
        if not globals.start_detect_qr:
            time.sleep(1)
            continue
        else:
            if globals.qr_code == "":
                ret, frame = cap.read()
                if frame is None:
                    print("QR frame is none!")
                    time.sleep(1)
                    continue
                print("QR Detecting...")
                qr_code, points, _ = qr_decoder.detectAndDecode(frame)
                if points is not None:
                    if qr_code:
                        globals.qr_code = qr_code
                        print("Detected QR Code:", qr_code)
                        threading.Thread(target=play_sound, args=('scan.mp3',)).start()
                        globals.start_detect_qr = False
            else:
                time.sleep(1)