import asyncio
import app.modules.globals as globals
from bleak import BleakClient, BleakScanner, BleakError
import struct
import os
from dotenv import load_dotenv
import threading
from collections import deque
from app.modules.utils import play_sound
from app.modules.cloud_api import update_environment
# Load environment variables
load_dotenv()

# BLE address of the XG26 sensor device
XG26_SENSOR_ADDRESS = os.getenv("XG26_SENSOR_ADDRESS")

# UUIDs for various sensor characteristics
IMU_UUID = os.getenv("IMU_UUID")
CHAR_UUID_PRESSURE    = os.getenv("CHAR_UUID_PRESSURE")
CHAR_UUID_TEMPERATURE = os.getenv("CHAR_UUID_TEMPERATURE")
CHAR_UUID_HUMIDITY    = os.getenv("CHAR_UUID_HUMIDITY")
CHAR_UUID_LIGHT       = os.getenv("CHAR_UUID_LIGHT")
CHAR_UUID_SOUND       = os.getenv("CHAR_UUID_SOUND")
CHAR_UUID_MAGNETIC    = os.getenv("CHAR_UUID_MAGNETIC")

# Mapping from characteristic UUID to (label, format, scale, is_notify)
CHAR_MAP = {
    # CHAR_UUID_PRESSURE: ("Pressure (hPa)", "<I", 1000.0, False),
    CHAR_UUID_TEMPERATURE: ("Temperature (°C)", "<h", 100.0, False),
    CHAR_UUID_HUMIDITY: ("Humidity (%)", "<H", 100.0, False),
    CHAR_UUID_LIGHT: ("Light (lux)", "<I", 1.0, False),
    # CHAR_UUID_SOUND: ("Sound (dB)", "<H", 1.0, False),
    # CHAR_UUID_MAGNETIC: ("Magnetic Field (µT)", "<I", 1.0, False),
    IMU_UUID: ("IMU (X, Y, Z)", "<hhh", 1.0, True)
}

# Global variables for shake and lean detection
delay_count_lean = 0
delay_threshold_lean = 30

delay_count_shake = 0
delay_threshold_shake = 15
windows_length = 5
windows = deque([0] * windows_length, maxlen=windows_length)
pre_x, pre_y, pre_z = (0,0,0)
sound_file_path_shake = "dong-dat.mp3"

def compute_shake(x,y,z,pre_x, pre_y, pre_z, windows):
    dx = abs(x - pre_x)
    dy = abs(y - pre_y)
    dz = abs(z - pre_z)
    total_d = dx + dy + dz
    pre_x, pre_y, pre_z = x, y, z
    windows.append(total_d)
    return sum(windows)

def imu_processing(x,y,z):
    global delay_count_lean, delay_threshold_lean, delay_count_shake, delay_threshold_shake, windows, windows_length, pre_x, pre_y, pre_z, sound_file_path_lean, sound_file_path_shake
    total_shake = compute_shake(x,y,z, pre_x, pre_y, pre_z, windows)

    # Check for shake detection
    if total_shake > (globals.get_threatshold_imu_shake() * windows_length):
        delay_count_shake += 1
        if delay_count_shake >= delay_threshold_shake: 
            print(f"[ALERT] Significant shake detected! Total={total_shake}")
            threading.Thread(target=play_sound, args=(sound_file_path_shake,)).start()
            delay_count_shake = 0
            delay_threshold_shake = 30
            globals.set_shelf_shake(True)
            globals.earthquake = True
    else:
        delay_count_shake = 0
        delay_threshold_shake = 10

# Create handler to receive IMU notifications
def create_notify_handler(uuid):
    def handler(sender, data):
        if uuid == IMU_UUID and len(data) == 6:
            x, y, z = struct.unpack("<hhh", data)
            if globals.get_imu_data_init() is None:
                global pre_x, pre_y, pre_z
                globals.set_imu_data_init((x, y, z))
                pre_x, pre_y, pre_z = x, y, z
            else:
                imu_processing(x, y, z)
    return handler

# Main BLE connection and reading loop
async def connect_and_monitor():
    while True:
        try:
            print("Searching for xg26 sensor device...")
            device = await BleakScanner.find_device_by_address(XG26_SENSOR_ADDRESS, timeout=10.0)
            if not device:
                print("xg26 sensor not found. Retrying...")
                await asyncio.sleep(5)
                continue

            async with BleakClient(device, disconnected_callback=lambda c: print("Disconnected xg26 sensor device.")) as client:
                print("Connected to xg26 sensor device.")
                sound_file_path = "sensor_connected.mp3"
                threading.Thread(target=play_sound, args=(sound_file_path,)).start()
                globals.set_imu_data_init(None)  # Reset IMU initial data on new connection
                # Enable notifications
                for uuid, (_, _, _, is_notify) in CHAR_MAP.items():
                    if is_notify:
                        await client.start_notify(uuid, create_notify_handler(uuid))

                while client.is_connected:
                    #print("-" * 40)

                    for uuid, (label, fmt, scale, is_notify) in CHAR_MAP.items():
                        if is_notify:
                            # if globals.imu_data:
                            #     x, y, z = globals.imu_data
                            #     print(f"{label}: X={x} Y={y} Z={z}")
                            # else:
                            #     print(f"{label}: No data yet.")
                            pass
                        else:
                            try:
                                data = await client.read_gatt_char(uuid)
                                if len(data) == struct.calcsize(fmt):
                                    value = struct.unpack(fmt, data)[0] / scale
                                    #print(f"{label}: {round(value, 2)}")

                                    # Assign to global variable
                                    # if uuid == CHAR_UUID_PRESSURE:
                                    #     globals.set_pressure(value)
                                    if uuid == CHAR_UUID_TEMPERATURE:
                                        globals.set_temperature(value)
                                    elif uuid == CHAR_UUID_HUMIDITY:
                                        globals.set_humidity(value)
                                    elif uuid == CHAR_UUID_LIGHT:
                                        globals.set_light(value)
                                    # elif uuid == CHAR_UUID_SOUND:
                                    #     globals.set_sound(value)
                                    # elif uuid == CHAR_UUID_MAGNETIC:
                                    #     globals.set_magnetic(value)
                                else:
                                    print(f"{label}: Invalid data length.")
                            except Exception as e:
                                print(f"{label}: Read error - {e}")
                    
                    # Print values for debug
                    # print(f"\n[DEBUG] Pressure: {globals.pressure}, Temp: {globals.temperature}, Humidity: {globals.humidity}")
                    # print(f"[DEBUG] Light: {globals.light}, Sound: {globals.sound}, Magnetic: {globals.magnetic}")
                    # print(f"[DEBUG] IMU: {globals.imu_data}")
                    data = {
                        "parking_id": os.getenv("PARKING_ID"),
                        "temperature": globals.temperature,
                        "humidity": globals.humidity,
                        "light": globals.light
                    }
                    if update_environment(data):
                        pass
                        #print("[INFO] Environment data updated to cloud.")
                    else:
                        print("[WARNING] Failed to update environment data to cloud.")
                    await asyncio.sleep(10) # Delay between reads

        except (BleakError, OSError) as e:
            print(f"Xg26 sensor connection error: {e}")
            print("Reconnecting xg26 sensor in 10 seconds...")
            await asyncio.sleep(10)
def start_connect_xg26():
    # Start the async event loop
    asyncio.run(connect_and_monitor())