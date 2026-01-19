# 🔄 PROJECT MIGRATION SUMMARY

## From: Loadcell Smart Shelf System
## To: Smart Parking Management System

---

## ✅ COMPLETED CHANGES

### 1. **New Hardware Drivers Created**

#### IR Sensors (Car Detection)
- **Files:** `ir_sensor.c`, `ir_sensor.h`
- **Pins:** PB0 (car_in), PB1 (car_out)
- **Function:** Detect vehicles at entrance/exit

#### Servo Motors (Barrier Control)
- **Files:** `servo.c`, `servo.h`
- **Pins:** PC0 (barrier_in), PC1 (barrier_out)
- **Function:** Control access barriers (0° closed, 90° open)
- **Note:** Uses software PWM (can upgrade to hardware TIMER PWM)

#### Environment Sensors
- **Files:** `parking_sensors.c`, `parking_sensors.h`
- **Light Sensor (PB2):** Detect day/night for automatic lighting
- **Flame Sensor (PB3):** Fire detection with alarm trigger

#### Button Handler
- **Files:** `button.c`, `button.h`
- **Pin:** PC7
- **Events:** Short press (toggle barrier), Long press (reset stats)

### 2. **Display Drivers**

#### LCD 16x2 I2C
- **Files:** `lcd_i2c.c`, `lcd_i2c.h` (reused from old project)
- **Address:** 0x27
- **Note:** PCA9548A multiplexer code commented out (single LCD now)

#### OLED 128x64 I2C
- **Files:** `oled_i2c.c`, `oled_i2c.h` (NEW)
- **Address:** 0x3C
- **Driver:** SSD1306
- **Font:** Built-in 5x7 ASCII font

### 3. **BLE GATT Database Redesigned**

**File:** `config/btconf/gatt_configuration.btconf`

**Old Service:** Loadcell Service (5 characteristics for product management)

**New Service:** Parking System Service

| **Characteristic**     | **UUID** | **Properties** | **Purpose**                          |
|------------------------|----------|----------------|--------------------------------------|
| IR Sensor Status       | 2393...  | Notify, Read   | Send car detection events            |
| LCD Display Data       | 8a03...  | Write          | Remote LCD content control           |
| OLED Display Data      | d200...  | Write          | Remote OLED content control          |
| Barrier Control        | ccfc...  | Write          | Manual barrier open/close            |
| Sensor Status          | 99c6...  | Notify, Read   | Light, flame, alarm status           |

### 4. **Application Logic Rewritten**

#### app.c (Main Application)
**Removed:**
- HX711 loadcell reading
- Product inventory management
- Weight calculation & calibration
- Scale/offset configuration
- PCA9548A multiplexer control

**Added:**
- IR sensor monitoring with edge detection
- Automatic barrier control logic
- Car counting (in/out) with statistics
- Flame detection with alarm
- Auto-close barriers after configurable delay
- NVM3 storage for parking stats & config
- Dual display management (LCD + OLED)

#### ble.c (BLE Event Handler)
**Removed:**
- Product data write handlers (weight_of_one, verified_quantity, product_name, product_price)

**Added:**
- Display data write handlers (LCD/OLED remote control)
- Barrier control write handler
- IR sensor status notification
- Sensor status notification
- Read request handlers for sensor data

### 5. **Data Structures**

**Old (Removed):**
```c
int32_t offset[LOADCELL_NUM];
int scale[LOADCELL_NUM];
int weight_of_one[LOADCELL_NUM];
int8_t verified_quantity[LOADCELL_NUM];
char product_name[LOADCELL_NUM][20];
int product_price[LOADCELL_NUM];
```

**New (Added):**
```c
typedef struct {
    uint8_t barrier_auto_close_delay_sec;
    uint8_t alarm_enabled;
    uint8_t night_mode_enabled;
} parking_config_t;

typedef struct {
    uint32_t total_cars_in;
    uint32_t total_cars_out;
    uint32_t current_cars_in_lot;
    uint32_t alarm_triggers;
} parking_stats_t;

char lcd_display_buffer[100];
char oled_display_buffer[100];
```

### 6. **Files Backed Up**

The following old files were renamed (not deleted) for reference:
- `app_old_backup.c` (original loadcell app)
- `ble_old_backup.c` (original BLE handler)
- `hx711_old_backup.c/.h` (HX711 loadcell driver)
- `app_bm_old_backup.c` (bare metal app variant)

### 7. **Reused Components** ✅

These components were kept from the original project:
- **timer_control.c/.h** - Non-blocking GPIO timer (buzzer)
- **lcd_i2c.c/.h** - LCD I2C driver (simplified)
- **BLE stack configuration** - Core BLE setup
- **NVM3 storage functions** - Data persistence
- **I2C peripheral** - `sl_i2cspm_mikroe` instance
- **Project structure** - `.slcp` file, build system

---

## 📋 TESTING CHECKLIST

Before deploying to hardware, verify:

### Hardware Connections:
- [ ] IR sensors wired to PB0, PB1
- [ ] Servo motors connected to PC0, PC1 with 5V power
- [ ] Light sensor on PB2
- [ ] Flame sensor on PB3
- [ ] Buzzer on PA0
- [ ] Button on PC7
- [ ] I2C devices (LCD 0x27, OLED 0x3C) on PD2/PD3

### Software Build:
- [ ] Project compiles without errors
- [ ] GATT database regenerated from .btconf
- [ ] All new drivers included in build
- [ ] Old HX711 references removed from build

### Functional Tests:
- [ ] IR sensors detect objects (LOW when blocked)
- [ ] Servos move to 0° and 90°
- [ ] LCD shows text correctly
- [ ] OLED displays content
- [ ] Button short/long press works
- [ ] Buzzer sounds on events
- [ ] BLE advertising visible
- [ ] BLE characteristics readable/writable
- [ ] Statistics saved to NVM3

---

## 🔧 KNOWN LIMITATIONS & FUTURE IMPROVEMENTS

### Current Implementation:
1. **Servo Control:** Uses software PWM (blocking delays)
   - **Improvement:** Use TIMER peripheral for hardware PWM

2. **OLED Font:** Only 5x7 ASCII characters
   - **Improvement:** Add larger fonts or graphics library

3. **IR Sensor Debouncing:** Basic edge detection
   - **Improvement:** Add software debouncing filter

4. **No RTOS:** Bare-metal super loop
   - **Improvement:** Port to FreeRTOS for better multitasking

5. **Fixed I2C Addresses:** Hardcoded in headers
   - **Improvement:** Add I2C bus scanning and auto-detection

### Safety Features to Add:
- [ ] Maximum capacity limit (reject entry when full)
- [ ] Emergency override (force all barriers open)
- [ ] Backup power detection
- [ ] Watchdog timer for system reliability

---

## 📞 Support

For issues or questions about the migration:

**Email:** duongkhang1676@gmail.com

**Migration Date:** December 4, 2025

**BGM220 SDK:** v2024.12.2

**Toolchain:** GNU ARM v12.2.1

---

## 🎯 NEXT STEPS

1. **Build the project** in Simplicity Studio
2. **Flash firmware** to BGM220
3. **Connect hardware** according to pin configuration
4. **Test each subsystem** individually
5. **Integrate and test** full parking flow
6. **Deploy mobile app** for BLE remote control

---

© 2025 – Project migrated by **Võ Dương Khang**
