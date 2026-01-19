import serial
import threading
import time
from app.modules.utils import play_sound, verify_car_out
import dotenv
import os
from app.modules import globals
dotenv.load_dotenv()

# Giao tiếp serial với micro controller
def start_connect_bgm220():
   # Thiết lập cổng Serial (kiểm tra cổng COM trong Device Manager)
    port = os.getenv('UART_PORT')
    baudrate = 115200
    
    # DEBUG: Kiểm tra port config
    #print(f"[DEBUG] Attempting to connect to UART Port: {port}, Baudrate: {baudrate}")
    
    if port is None or port == "":
        print("[ERROR] UART_PORT not configured in .env file!")
        return
    
    # Thiết lập cổng Serial (kiểm tra cổng COM trong Device Manager)
    try:
        # Kết nối Serial
        ser = serial.Serial(port, baudrate, timeout=1)
        print(f"[SUCCESS] Kết nối thành công với {port}")
        threading.Thread(target=play_sound, args=('connected_bgm220.mp3',)).start()
        while True:
            time.sleep(0.2)  # Giảm từ 1s xuống 0.2s để đọc nhanh hơn
            # DEBUG: Kiểm tra buffer
            # if ser.in_waiting > 0:
            #     print(f"[DEBUG] Bytes available in buffer: {ser.in_waiting}")
            
            # Danh sách dữ liệu từ Arduino
            if globals.update_display:
                if globals.slot_recommend == "" or len(globals.parking_num_slot) == 0:
                    globals.update_display = False
                else:
                    ser.write(f'slot_recommend:{globals.slot_recommend}\n'.encode())
                    time.sleep(0.2)  # Đợi một chút để Arduino xử lý
                    ser.write(f'parking_num_slot:{",".join(map(str, globals.parking_num_slot))}\n'.encode())
                    globals.update_display = False
                    print("[SEND] Cập nhật màn hình hiển thị")
            
            # Kiểm tra ánh sáng (chỉ xử lý khi có dữ liệu)
            current_light = globals.get_light()
            if globals.turn_light and globals.light_state == False and globals.auto_light_mode == False:
                ser.write(b'turn_on_light\n')
                print("[SEND] Bật đèn chiếu sáng")
                globals.light_state = True

            elif globals.turn_light == False and globals.light_state == True and globals.auto_light_mode == False:
                ser.write(b'turn_off_light\n')
                print("[SEND] Tắt đèn chiếu sáng")
                globals.light_state = False
                
            if current_light is not None and globals.auto_light_mode:
                if current_light < 100 and globals.light_state == False:
                    ser.write(b'turn_on_light\n')
                    threading.Thread(target=play_sound, args=('troi-toi.mp3',)).start()
                    print("[SEND] Bật đèn chiếu sáng")
                    globals.light_state = True
                elif current_light >= 100 and globals.light_state == True:
                    ser.write(b'turn_off_light\n')
                    threading.Thread(target=play_sound, args=('troi-sang.mp3',)).start()
                    print("[SEND] Tắt đèn chiếu sáng")
                    globals.light_state = False

            if globals.earthquake:
                ser.write(b'earthquake\n')   
                print("[SEND] Mở barie (in và out)")
                globals.earthquake = False

            if globals.open_in:
                threading.Thread(target=play_sound, args=('xin-moi-vao.mp3',)).start()
                ser.write(b'open_in\n')  # Gửi lệnh mở barie vào
                print("[SEND] Mở barie vào")
                globals.open_in = False

            if globals.open_out:
                threading.Thread(target=play_sound, args=('tam-biet-quy-khach.mp3',)).start()
                ser.write(b'open_out\n')  # Gửi lệnh mở barie ra
                print("[SEND] Mở barie ra")
                verify_car_out(globals.license_plate)
                globals.open_out = False
            
            if globals.close_in:
                ser.write(b'close_in\n')  # Gửi lệnh đóng barie vào
                print("[SEND] Đóng barie vào")
                globals.close_in = False
            
            if globals.close_out:
                ser.write(b'close_out\n')  # Gửi lệnh đóng barie ra
                print("[SEND] Đóng barie ra")
                globals.close_out = False
            
            # Đọc dữ liệu từ UART
            if ser.in_waiting > 0:
                try:
                    # Đọc dữ liệu từ BGM220
                    data = ser.readline().decode('utf-8').strip()
                    
                    # DEBUG: In raw data
                    print(f"[RECEIVE] Raw data: '{data}'")
                    
                    if not data:
                        print("[WARNING] Empty data received")
                        continue
                    
                    # Kiểm tra định dạng và tách key, value
                    if ":" in data:
                        key, value = data.split(":", 1)
                        #print(f"[PARSE] Key: '{key}', Value: '{value}'")
            
                        # Xe vào
                        if key == "car_in":
                            if value == "1":
                                threading.Thread(target=play_sound, args=('quet-ma.mp3',)).start()
                                print("[ACTION] Xe vào - Bật detect license")
                                globals.start_detect_license = True
                                globals.car_in = True
                            else:
                                print("[ACTION] Xe vào kết thúc - Tắt detect license")
                                globals.start_detect_license = False
                                globals.license_plate = ""
                                globals.qr_code = ""
                                globals.car_in = False
                        # Xe ra
                        elif key == "car_out":
                            if value == "1":
                                threading.Thread(target=play_sound, args=('quet-ma.mp3',)).start()
                                print("[ACTION] Xe ra - Bật detect license")
                                globals.start_detect_license = True
                                globals.car_out = True
                            else:
                                print("[ACTION] Xe ra kết thúc - Tắt detect license")
                                globals.start_detect_license = False
                                globals.license_plate = ""
                                globals.qr_code = ""
                                globals.car_out = False
                        else:
                            print(f"[WARNING] Unknown key: '{key}'")
                    else:
                        print(f"[WARNING] Invalid data format (no ':' separator): '{data}'")
                        
                except UnicodeDecodeError as e:
                    print(f"[ERROR] Decode error: {e}")
                except Exception as e:
                    print(f"[ERROR] Error reading UART: {e}")
            else:
                # Không có dữ liệu trong buffer
                pass
    
    except serial.SerialException as e:
        print(f"[ERROR] Không thể kết nối tới {port}: {e}")
        print("[HELP] Kiểm tra:")
        print("  1. Port có đúng không? (Device Manager > Ports)")
        print("  2. Thiết bị có được cắm vào không?")
        print("  3. Driver đã cài đặt chưa?")
        print("  4. Port có đang bị sử dụng bởi chương trình khác không?")
    except KeyboardInterrupt:
        print("\n[INFO] Đã thoát chương trình.")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("[INFO] Đã đóng cổng Serial.")