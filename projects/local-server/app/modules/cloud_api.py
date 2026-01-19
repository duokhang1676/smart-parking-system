from dotenv import load_dotenv
import os
import requests
import urllib.request
import json
load_dotenv()

CLOUD_SERVER_URL = os.getenv("CLOUD_SERVER_URL")    

# coordinates APIs
def get_coordinates(parking_id, camera_id):
    url = f'{CLOUD_SERVER_URL+"coordinates/"}{parking_id}/{camera_id}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()[0]
    else:
        return None

def update_coordinates(parking_id, camera_id, data):
    url = f'{CLOUD_SERVER_URL+"coordinates/"}update/{parking_id}/{camera_id}'
    response = requests.put(url, json=data)
    return response.status_code == 200

def insert_coordinates(data):
    url = f'{CLOUD_SERVER_URL+"coordinates/"}add'
    response = requests.post(url, json=data)
    return response.status_code == 201

# parked vehicle APIs
def insert_parked_vehicle(data):
    url = f'{CLOUD_SERVER_URL+"parked_vehicles/"}add_vehicle'
    response = requests.post(url, json=data)
    return response.status_code == 200

def remove_parked_vehicle(data):
    url = f'{CLOUD_SERVER_URL+"parked_vehicles/"}remove_vehicle'
    response = requests.delete(url, json=data)
    if response != 200:
        print(response)
    return response.status_code == 200

def update_parked_vehicle(data):
    url = f'{CLOUD_SERVER_URL+"parked_vehicles/"}update_vehicle'
    response = requests.put(url, json=data)
    return response.status_code == 200

def update_parked_vehicle_list(data):
    url = f'{CLOUD_SERVER_URL+"parked_vehicles/"}update_vehicle_list'
    response = requests.put(url, json=data)
    if response.status_code == 200:
        print(f"[CLOUD] Đã cập nhật danh sách xe đậu lên Cloud Server")
        return True
    else:
        print(f"[CLOUD] Lỗi khi cập nhật danh sách xe đậu lên Cloud Server")
        print(response.json())
        return False

# parking lot, environment, history APIs
def update_parking_lot(data):
    url = f'{CLOUD_SERVER_URL+"parking_slots/"}update_parking_slots'
    response = requests.post(url, json=data)
    if response.status_code == 200:
        print(f"[CLOUD] Đã cập nhật trạng thái bãi xe lên Cloud Server")
        return True
    else:
        print(f"[CLOUD] Lỗi khi cập nhật trạng thái bãi xe lên Cloud Server")
        return False

def update_environment(data):
    url = f'{CLOUD_SERVER_URL+"environments/"}update_environment'
    response = requests.post(url, json=data)
    return response.status_code == 200

def insert_history(data):
    url = f'{CLOUD_SERVER_URL+"histories/"}'
    response = requests.post(url, json=data)
    return response.status_code == 201

def get_registered_vehicles():
    url = f'{CLOUD_SERVER_URL}registers/get_register_list'  # Đúng endpoint: registers/get_register_list
    payload = {
        "parking_id": os.getenv("PARKING_ID", "parking_001")
    }
    
    # print(f"[DEBUG] Calling URL: {url}")
    # print(f"[DEBUG] Payload: {payload}")
    
    try:
        # Dùng requests thay vì urllib cho đơn giản
        response = requests.post(url, json=payload, timeout=10)
        
    #    print(f"[DEBUG] Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'success':
                data = result.get('data', [])
                # Chỉ lấy license_plate và user_id
                simplified_data = [
                    {
                        'license_plate': item.get('license_plate'),
                        'user_id': item.get('user_id')
                    }
                    for item in data
                ]
                #print(f"[SUCCESS] Fetched {len(simplified_data)} registered vehicles")
                return simplified_data
            else:
                print(f"[ERROR] API returned error: {result.get('message', 'Unknown error')}")
                return []
        elif response.status_code == 404:
            print("[INFO] No registers found for this parking_id")
            return []
        else:
            print(f"[ERROR] HTTP {response.status_code}: {response.text}")
            return []
            
    except requests.exceptions.Timeout:
        print("[ERROR] Request timeout - server took too long to respond")
    except requests.exceptions.ConnectionError:
        print("[ERROR] Connection error - cannot reach server")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
    
    # Fallback: Đọc từ file local nếu API không hoạt động
    print("[WARNING] API failed, using local fallback")
    try:
        local_file = "app/resources/database/registered_vehicles.json"
        if os.path.exists(local_file):
            with open(local_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Chỉ lấy license_plate và user_id từ file local
                simplified_data = [
                    {
                        'license_plate': item.get('license_plate'),
                        'user_id': item.get('user_id')
                    }
                    for item in data
                ]
                print(f"[FALLBACK] Loaded {len(simplified_data)} vehicles from local file")
                return simplified_data
        else:
            print(f"[WARNING] Local file not found: {local_file}")
    except Exception as e:
        print(f"[ERROR] Failed to read local file: {e}")
    
    return []
