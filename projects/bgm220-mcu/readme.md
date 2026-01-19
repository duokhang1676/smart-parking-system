
# Smart Parking System with BLE (BGM220)

## 📘 Description

This is a **Smart Parking Management System** using BGM220 Bluetooth SoC. The system performs:
- Detects vehicles at entrance/exit using **IR sensors**
- Controls **servo barriers** to allow/deny vehicle access
- Monitors parking environment with **light sensor** and **flame detector**
- Displays real-time information on **LCD** (16x2) and **OLED** (128x64)
- Sends sensor data and receives control commands via **Bluetooth Low Energy (BLE)**
- Saves statistics to non-volatile memory (NVM3)

### Notification Sounds:
- **One 100ms beep**: Car detected (entrance/exit)
- **One 200ms beep**: System startup
- **One 500ms beep**: Fire alarm detected!
- **Two 100ms beeps (200ms apart)**: BLE connection opened
- **Three 100ms beeps (200ms apart)**: BLE connection closed

Developed on **Silicon Labs BGM220** platform using **C** with **Simplicity Studio**.

---

## 🧩 Project Structure

```
smart_parking_bgm220/
│
├── app.c, app.h             // Main application logic
├── ble.c, ble.h            // BLE communication (notify & write)
├── ir_sensor.c, .h         // IR sensors for car detection
├── servo.c, .h             // Servo motor control for barriers
├── parking_sensors.c, .h   // Light & flame sensors
├── button.c, .h            // Button input handler
├── timer_control.c, .h     // Non-blocking timer (buzzer control)
├── lcd_i2c.c, .h           // LCD 16x2 I2C driver
├── oled_i2c.c, .h          // OLED 128x64 I2C driver (SSD1306)
├── config/btconf/          // GATT database configuration
└── README.md               // This file
```

---

## 🔧 Software Dependencies

- **Simplicity Studio 5**
- **Silicon Labs Gecko SDK 2024.12.2**
- Toolchain: **GNU ARM v12.2.1**
- BLE GATT Configurator
- Development board: **BGM220 Explorer Kit (BRD4314A)**

---

## 🔌 Hardware Requirements

### Microcontroller:
- **BGM220PC22HNA** (BLE SoC)

### Sensors:
- **2x IR Obstacle Sensors** (car_in, car_out)
- **1x Light Sensor** (photoresistor or digital)
- **1x Flame Sensor** (IR flame detector)

### Actuators:
- **2x Servo Motors** (SG90 or similar, for barriers)
- **1x Buzzer/Piezo** (alarm & notifications)

### Displays:
- **1x LCD 16x2 I2C** (address 0x27)
- **1x OLED 128x64 I2C** (SSD1306, address 0x3C)

### Other:
- **1x Push Button** (manual control)
- Connecting wires, USB cable, power supply

---

## 📌 GPIO Pin Configuration

| **Device**        | **GPIO Pin** | **Type**  | **Description**            |
|-------------------|--------------|-----------|----------------------------|
| IR car_in         | PB0          | Input     | Entrance IR sensor         |
| IR car_out        | PB1          | Input     | Exit IR sensor             |
| Servo barrier_in  | PC0          | PWM Out   | Entrance servo motor       |
| Servo barrier_out | PC1          | PWM Out   | Exit servo motor           |
| Light Sensor      | PB2          | Input     | Light level detector       |
| Flame Sensor      | PB3          | Input     | Fire detector              |
| Buzzer            | PA0          | Output    | Audio notification         |
| Button            | PC7          | Input     | Manual control button      |
| I2C SDA           | PD3          | I2C       | LCD + OLED data line       |
| I2C SCL           | PD2          | I2C       | LCD + OLED clock line      |

*(Adjust pins in driver header files if needed)*

---

## 🚀 Getting Started

### 1. Hardware Setup
- Connect IR sensors to entrance/exit positions
- Mount servo motors as barrier gates
- Install light sensor (ceiling) and flame sensor (sensitive area)
- Connect LCD and OLED to I2C bus
- Wire buzzer and button

### 2. Install Simplicity Studio and Open Project
- Import the project into Simplicity Studio 5
- Select BGM220PC22HNA target
- Generate GATT database from `config/btconf/gatt_configuration.btconf`

### 3. Build and Flash Firmware
```bash
# Build in Simplicity Studio or via CLI
make clean
make all
# Flash to BGM220
```

### 4. Connect via BLE
- Use **nRF Connect**, **LightBlue**, or custom mobile app
- Device name: **BGM220** (or custom)
- Service UUID: `80c17bcd-a6f3-4c9e-9c0f-09b10af7fcab`

---

## 📡 BLE GATT Services

### Parking System Service
**UUID:** `80c17bcd-a6f3-4c9e-9c0f-09b10af7fcab`

#### Characteristics:

| **Characteristic**     | **UUID**                               | **Properties** | **Description**                      |
|------------------------|----------------------------------------|----------------|--------------------------------------|
| IR Sensor Status       | `2393cdd9-21f9-4ab5-b1ed-956b7b38c423` | Notify, Read   | 2 bytes: [car_in, car_out]          |
| LCD Display Data       | `8a03cd1e-2f09-40c1-9202-d26c45a081b9` | Write          | String to display on LCD (max 100)  |
| OLED Display Data      | `d2003ffe-af3d-4b46-b555-dec8601132e7` | Write          | String to display on OLED (max 100) |
| Barrier Control        | `ccfccece-ac38-49c5-8da7-3489689281db` | Write          | 2 bytes: [barrier_in, barrier_out]  |
| Sensor Status          | `99c6d7a1-05c1-4fc6-b61d-10c114d342a3` | Notify, Read   | 4 bytes: [light, flame, alarm, res] |

---

## 🔁 System Operation

### Automatic Mode:
1. **Car approaches entrance** → IR sensor triggers → Barrier opens
2. **Car passes** → Stats updated (cars in +1) → BLE notification sent
3. **After delay** → Barrier auto-closes
4. **Car approaches exit** → Same process (cars in -1)

### Manual Mode:
- **Short button press**: Toggle entrance barrier
- **Long button press (3s)**: Reset statistics

### Alarm Mode:
- **Flame detected**: Continuous beeping, BLE alert, display warning

### BLE Remote Control:
- Send display text to LCD/OLED
- Manually open/close barriers
- Monitor real-time sensor data

---

## 📊 Data Storage (NVM3)

| **Key**    | **Data**               | **Description**              |
|------------|------------------------|------------------------------|
| `0x10001`  | `parking_config_t`     | System configuration         |
| `0x10002`  | `parking_stats_t`      | Total cars in/out, alarms    |

Statistics persist across reboots.

---

## 🛠 Customization

### Change GPIO Pins:
Edit pin definitions in header files:
- `ir_sensor.h` - IR sensor pins
- `servo.h` - Servo PWM pins
- `parking_sensors.h` - Light & flame pins
- `button.h` - Button pin

### Adjust Timing:
In `app.c`:
```c
parking_config.barrier_auto_close_delay_sec = 5; // seconds
```

### Modify Display Content:
BLE write to LCD/OLED characteristics, or edit `update_lcd_display()` / `update_oled_display()` functions.

---

## 🐛 Troubleshooting

| **Issue**                  | **Solution**                                    |
|----------------------------|-------------------------------------------------|
| Servo not moving           | Check PWM pin, verify power supply (5V)        |
| I2C display not working    | Scan I2C bus, verify addresses (0x27, 0x3C)    |
| IR sensors always HIGH/LOW | Check sensor wiring, test with multimeter      |
| BLE not connecting         | Check advertising, verify GATT database build  |

---

## 📞 Contact & Contributions

For questions, issues, or contributions:

📧 **duongkhang1676@gmail.com**

---

© 2025 – Smart Parking System by **Võ Dương Khang**
