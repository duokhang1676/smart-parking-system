import threading
from multiprocessing import Manager
from app.modules.utils import play_sound, save_regisstered_vehicles_to_file
from app.modules import mqtt_topic, tracking_car, detect_license, connect_bgm220, connect_xg26, globals
from app.modules.cloud_api import get_registered_vehicles

def main():
    # Khởi tạo shared memory cho search_vehicle để child processes có thể đọc
    manager = Manager()
    search_vehicle_shared = manager.dict()
    search_vehicle_shared['value'] = ""
    globals.search_vehicle_shared = search_vehicle_shared
    
    threading.Thread(target=play_sound, args=("start-program.mp3",)).start()
    threading.Thread(target=save_regisstered_vehicles_to_file, args=(get_registered_vehicles(),)).start()
    threading.Thread(target=tracking_car.start_tracking_car, daemon=True).start()
    threading.Thread(target=detect_license.start_detect_license, daemon=True).start()
    threading.Thread(target=connect_bgm220.start_connect_bgm220, daemon=True).start()
    threading.Thread(target=connect_xg26.start_connect_xg26, daemon=True).start()
    threading.Thread(target=mqtt_topic.start_mqtt_topic, daemon=True).start()
if __name__ == '__main__':
    main()
    while True:
        try:
            # Keep the main thread alive
            globals.registered_vehicles = get_registered_vehicles()
            threading.Event().wait(10)
        except KeyboardInterrupt:
            print("Exiting...")
            break   