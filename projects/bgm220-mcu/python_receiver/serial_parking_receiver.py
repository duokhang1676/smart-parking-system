"""
Serial Parking System Receiver
Tương tự Arduino version, nhận dữ liệu qua Serial/UART từ BGM220

Commands to BGM220:
- '0' : Close servo_in after 3s
- '1' : Open servo_in
- '2' : Close servo_out after 3s
- '3' : Open servo_out
- 'A,B,C,D,Total' : Update slot data (e.g., "2,3,1,4,10")
- 'text' : Display direction text on LCD (e.g., "D0-C0    B0-A0")

Receive from BGM220:
- 'car_in:1' : Car detected at entrance
- 'car_in:0' : Car cleared entrance
- 'car_out:1' : Car detected at exit
- 'car_out:0' : Car cleared exit
"""

import serial
import serial.tools.list_ports
import time
from datetime import datetime


class ParkingSystemController:
    def __init__(self, port=None, baudrate=115200):
        """Initialize serial connection to BGM220"""
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        
        if port is None:
            self.port = self.find_serial_port()
        
        if self.port:
            self.connect()
    
    def find_serial_port(self):
        """Auto-detect serial port"""
        print("🔍 Scanning for serial ports...")
        ports = serial.tools.list_ports.comports()
        
        for port in ports:
            print(f"  Found: {port.device} - {port.description}")
            # Look for Silicon Labs or J-Link (common for BGM220)
            if "Silicon Labs" in port.description or "J-Link" in port.description:
                print(f"✅ Selected: {port.device}")
                return port.device
        
        if ports:
            print(f"⚠️  Using first port: {ports[0].device}")
            return ports[0].device
        
        print("❌ No serial ports found!")
        return None
    
    def connect(self):
        """Connect to serial port"""
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=0.1,
                write_timeout=1
            )
            print(f"✅ Connected to {self.port} @ {self.baudrate} baud")
            time.sleep(2)  # Wait for device to initialize
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def send_command(self, cmd):
        """Send command to BGM220"""
        if self.ser and self.ser.is_open:
            try:
                self.ser.write(f"{cmd}\n".encode())
                print(f"📤 Sent: {cmd}")
                return True
            except Exception as e:
                print(f"❌ Send error: {e}")
                return False
        return False
    
    def read_data(self):
        """Read data from BGM220"""
        if self.ser and self.ser.is_open:
            try:
                if self.ser.in_waiting > 0:
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        return line
            except Exception as e:
                print(f"❌ Read error: {e}")
        return None
    
    def close(self):
        """Close serial connection"""
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("👋 Connection closed")


def handle_ir_event(event):
    """Handle IR sensor events"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    
    if "car_in:1" in event:
        print(f"[{timestamp}] 🚗 ENTRANCE: Car detected")
        print("  ➜ Action: Send '1' to open barrier")
        return "1"  # Open entrance barrier
        
    elif "car_in:0" in event:
        print(f"[{timestamp}] 🚗 ENTRANCE: Car cleared")
        print("  ➜ Action: Send '0' to close barrier after 3s")
        return "0"  # Close entrance barrier after 3s
        
    elif "car_out:1" in event:
        print(f"[{timestamp}] 🚗 EXIT: Car detected")
        print("  ➜ Action: Send '3' to open barrier")
        return "3"  # Open exit barrier
        
    elif "car_out:0" in event:
        print(f"[{timestamp}] 🚗 EXIT: Car cleared")
        print("  ➜ Action: Send '2' to close barrier after 3s")
        return "2"  # Close exit barrier after 3s
    
    return None


def demo_mode(controller):
    """Demo mode - test commands"""
    print("\n" + "="*60)
    print("  DEMO MODE")
    print("="*60)
    
    commands = [
        ("D0-C0    B0-A0", "Set LCD direction text"),
        ("2,3,1,4,10", "Update slot data (A=2, B=3, C=1, D=4, Total=10)"),
        ("1", "Open entrance barrier"),
        (None, "Wait 2 seconds..."),
        ("0", "Close entrance barrier (after 3s)"),
        (None, "Wait 2 seconds..."),
        ("3", "Open exit barrier"),
        (None, "Wait 2 seconds..."),
        ("2", "Close exit barrier (after 3s)"),
    ]
    
    for cmd, desc in commands:
        if cmd:
            print(f"\n📝 {desc}")
            controller.send_command(cmd)
            time.sleep(1)
        else:
            print(f"\n⏳ {desc}")
            time.sleep(2)
    
    print("\n✅ Demo completed!")


def main():
    print("=" * 60)
    print("  Serial Parking System Receiver (BGM220)")
    print("=" * 60)
    
    # Initialize controller
    controller = ParkingSystemController()
    
    if not controller.ser:
        print("\n💡 Tips:")
        print("  1. Make sure BGM220 is connected via USB")
        print("  2. Check if J-Link debugger is connected")
        print("  3. Try specifying port manually: ParkingSystemController('COM3')")
        return
    
    # Ask for demo mode
    print("\n📋 Options:")
    print("  1. Demo mode (auto test)")
    print("  2. Monitor mode (listen only)")
    print("  3. Interactive mode (manual commands)")
    
    try:
        choice = input("\nSelect mode (1/2/3): ").strip()
        
        if choice == "1":
            demo_mode(controller)
            
        elif choice == "2":
            print("\n👂 Monitoring IR sensor events... (Press Ctrl+C to stop)")
            print("-" * 60)
            
            while True:
                data = controller.read_data()
                if data:
                    print(f"📥 Received: {data}")
                    
                    # Auto-respond to IR events
                    response = handle_ir_event(data)
                    if response:
                        controller.send_command(response)
                
                time.sleep(0.05)
        
        elif choice == "3":
            print("\n⌨️  Interactive mode (Press Ctrl+C to stop)")
            print("Commands:")
            print("  '0' - Close servo_in")
            print("  '1' - Open servo_in")
            print("  '2' - Close servo_out")
            print("  '3' - Open servo_out")
            print("  '2,3,1,4,10' - Update slots")
            print("  'text' - Set LCD text")
            print("-" * 60)
            
            # Start reader thread
            import threading
            
            def read_thread():
                while True:
                    data = controller.read_data()
                    if data:
                        print(f"\n📥 {data}")
                    time.sleep(0.05)
            
            reader = threading.Thread(target=read_thread, daemon=True)
            reader.start()
            
            # Input loop
            while True:
                cmd = input("\n📤 Command: ").strip()
                if cmd:
                    controller.send_command(cmd)
    
    except KeyboardInterrupt:
        print("\n\n👋 Stopped by user")
    
    finally:
        controller.close()


if __name__ == "__main__":
    main()
