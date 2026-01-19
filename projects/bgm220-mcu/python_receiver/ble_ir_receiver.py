"""
BLE IR Sensor State Receiver
Receives IR sensor state changes from BGM220 parking system

State codes:
- 0: car_in_detected = false (entrance cleared)
- 1: car_in_detected = true (car at entrance)
- 2: car_out_detected = false (exit cleared)
- 3: car_out_detected = true (car at exit)
"""

import asyncio
from bleak import BleakClient, BleakScanner
from datetime import datetime

# BLE Configuration
DEVICE_NAME = "Smart Parking"  # Change to your device name
IR_SENSOR_CHAR_UUID = "00000000-0000-0000-0000-000000000000"  # Update with your UUID

# State code meanings
STATE_MESSAGES = {
    0: "🚗 ENTRANCE: Car cleared (sensor released)",
    1: "🚗 ENTRANCE: Car detected (sensor triggered)",
    2: "🚗 EXIT: Car cleared (sensor released)",
    3: "🚗 EXIT: Car detected (sensor triggered)"
}


def notification_handler(sender, data):
    """Handle incoming BLE notifications"""
    if len(data) > 0:
        state_code = data[0]
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        if state_code in STATE_MESSAGES:
            print(f"[{timestamp}] Code {state_code}: {STATE_MESSAGES[state_code]}")
        else:
            print(f"[{timestamp}] Unknown code: {state_code}")
        
        # You can add custom actions here based on state_code
        handle_state_change(state_code)


def handle_state_change(state_code):
    """Custom handler for state changes"""
    if state_code == 1:
        print("  ➜ Action: Car entering, barrier should open")
    elif state_code == 0:
        print("  ➜ Action: Car passed entrance, barrier will auto-close")
    elif state_code == 3:
        print("  ➜ Action: Car exiting, barrier should open")
    elif state_code == 2:
        print("  ➜ Action: Car passed exit, barrier will auto-close")


async def find_device():
    """Scan for BGM220 device"""
    print("🔍 Scanning for BLE devices...")
    devices = await BleakScanner.discover(timeout=10.0)
    
    for device in devices:
        print(f"  Found: {device.name} ({device.address})")
        if DEVICE_NAME.lower() in (device.name or "").lower():
            print(f"✅ Found target device: {device.name}")
            return device.address
    
    print(f"❌ Device '{DEVICE_NAME}' not found")
    return None


async def main():
    """Main BLE client loop"""
    print("=" * 60)
    print("  BLE IR Sensor State Receiver")
    print("=" * 60)
    
    # Find device
    device_address = await find_device()
    if not device_address:
        print("\n💡 Tips:")
        print("  1. Make sure BGM220 is powered and advertising")
        print("  2. Check DEVICE_NAME variable matches your device")
        print("  3. Try scanning with nRF Connect app first")
        return
    
    print(f"\n🔗 Connecting to {device_address}...")
    
    try:
        async with BleakClient(device_address, timeout=20.0) as client:
            print(f"✅ Connected!")
            
            # List all services and characteristics
            print("\n📋 Available services:")
            for service in client.services:
                print(f"  Service: {service.uuid}")
                for char in service.characteristics:
                    print(f"    Characteristic: {char.uuid}")
                    if "notify" in char.properties:
                        print(f"      ➜ This supports notifications!")
                        # Update IR_SENSOR_CHAR_UUID with this UUID
            
            # Subscribe to notifications
            # You need to update IR_SENSOR_CHAR_UUID with the correct UUID from above
            if IR_SENSOR_CHAR_UUID != "00000000-0000-0000-0000-000000000000":
                print(f"\n🔔 Subscribing to notifications on {IR_SENSOR_CHAR_UUID}")
                await client.start_notify(IR_SENSOR_CHAR_UUID, notification_handler)
                print("✅ Listening for IR sensor state changes...")
                print("   Press Ctrl+C to stop\n")
                
                # Keep connection alive
                while True:
                    await asyncio.sleep(1)
            else:
                print("\n❌ Please update IR_SENSOR_CHAR_UUID in the script!")
                print("   Use the UUID shown above that supports notifications")
                await asyncio.sleep(5)
                
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Troubleshooting:")
        print("  1. Make sure device is in range")
        print("  2. Check if device is already connected elsewhere")
        print("  3. Try power cycling the BGM220")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Disconnected by user")
