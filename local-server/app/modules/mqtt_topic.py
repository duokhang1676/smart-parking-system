import paho.mqtt.client as mqtt
from app.modules import globals

broker = "broker.hivemq.com"
port = 1883

# Định nghĩa các topics riêng biệt
TOPIC_LIGHT = "parking/light"
TOPIC_LIGHT_MODE = "parking/light/mode"
TOPIC_BARRIER_IN = "parking/barrier/in"
TOPIC_BARRIER_OUT = "parking/barrier/out"
TOPIC_SEARCH_VEHICLE = "parking/vehicle/search"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"[CONNECTED] Successfully connected to broker")
        # Subscribe tất cả các topics
        client.subscribe(TOPIC_LIGHT, qos=1)
        client.subscribe(TOPIC_LIGHT_MODE, qos=1)
        client.subscribe(TOPIC_BARRIER_IN, qos=1)
        client.subscribe(TOPIC_BARRIER_OUT, qos=1)
        client.subscribe(TOPIC_SEARCH_VEHICLE, qos=1)
        print(f"[SUBSCRIBED] Topics: {TOPIC_LIGHT}, {TOPIC_LIGHT_MODE}, {TOPIC_BARRIER_IN}, {TOPIC_BARRIER_OUT}, {TOPIC_SEARCH_VEHICLE} ")
    else:
        print(f"[ERROR] Connection failed with code: {rc}")

def on_message(client, userdata, msg):
    topic = msg.topic
    message = msg.payload.decode().lower()
    print(f"[RECEIVED] Topic: {topic} | Message: {message}")
    
    # Xử lý theo từng topic
    if topic == TOPIC_LIGHT:
        if message == "on":
            globals.turn_light = True
            print("[ACTION] Light turned ON")
        elif message == "off":
            globals.turn_light = False
            print("[ACTION] Light turned OFF")
    
    elif topic == TOPIC_BARRIER_IN:
        if message == "open":
            globals.open_in = True
            print("[ACTION] Barrier IN opened")
        elif message == "close":
            globals.close_in = True
            print("[ACTION] Barrier IN closed")
    
    elif topic == TOPIC_BARRIER_OUT:
        if message == "open":
            globals.open_out = True
            print("[ACTION] Barrier OUT opened")
        elif message == "close":
            globals.close_out = True
            print("[ACTION] Barrier OUT closed")
    elif topic == TOPIC_LIGHT_MODE:
        if message == "on":
            globals.auto_light_mode = True
            print("[ACTION] Auto Light Mode enabled")
        elif message == "off":
            globals.auto_light_mode = False
            print("[ACTION] Auto Light Mode disabled")
    elif topic == TOPIC_SEARCH_VEHICLE:
        globals.set_search_vehicle(message)
        print(f"[ACTION] Search Vehicle set to: {message}")
    else:
        print(f"[WARNING] Unknown topic: {topic}")
def on_subscribe(client, userdata, mid, granted_qos):
    print(f"[SUBSCRIBE CONFIRMED] QoS: {granted_qos}")

def start_mqtt_topic():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_subscribe = on_subscribe

    print(f"[INFO] Connecting to broker: {broker}:{port}")
    try:
        client.connect(broker, port, 60)
        print("[INFO] Starting loop...")
        client.loop_forever()
    except Exception as e:
        print(f"[ERROR] Connection error: {e}")
