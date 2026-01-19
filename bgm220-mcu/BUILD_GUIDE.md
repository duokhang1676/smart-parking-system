# 🏗️ BUILD INSTRUCTIONS - Smart Parking System

## Prerequisites

1. **Simplicity Studio 5** installed
2. **Gecko SDK 2024.12.2** (or compatible)
3. **GNU ARM Toolchain v12.2.1**
4. **BGM220 Explorer Kit** (BRD4314A)

---

## 📦 Project Setup

### Step 1: Open in Simplicity Studio

1. Launch **Simplicity Studio 5**
2. Go to **File** → **Import**
3. Select **General** → **Existing Projects into Workspace**
4. Browse to: `c:\Users\LENOVO\Documents\9_HK1 2025-2026\KLTN\bgm220`
5. Click **Finish**

### Step 2: Regenerate GATT Database

**IMPORTANT:** After changing `gatt_configuration.btconf`, you must regenerate:

1. In Project Explorer, expand **config/btconf/**
2. Right-click **gatt_configuration.btconf**
3. Select **Generate** → **Generate Files**
4. Verify `autogen/gatt_db.h` and `gatt_db.c` are updated

### Step 3: Clean Build

```bash
# In Simplicity Studio:
Right-click project → Clean Project
Right-click project → Build Project

# Or use terminal (if make available):
cd "c:\Users\LENOVO\Documents\9_HK1 2025-2026\KLTN\bgm220"
make clean
make all
```

---

## 🔧 Build Configuration

### Required Source Files

Ensure these files are included in build (check `.slcp` or project settings):

**Application Code:**
```
app.c
main.c
ble.c
ir_sensor.c
servo.c
parking_sensors.c
button.c
timer_control.c
lcd_i2c.c
oled_i2c.c
sl_gatt_service_device_information.c
```

**Auto-generated (don't modify):**
```
autogen/gatt_db.c
autogen/sl_bluetooth.c
autogen/sl_event_handler.c
autogen/sl_i2cspm_init.c
autogen/sl_iostream_init_eusart_instances.c
(and other autogen files)
```

### Required Components (from .slcp)

These should already be configured:
- `BGM220PC22HNA` (MCU)
- `brd4314a` (Board)
- `bluetooth_stack`
- `bluetooth_feature_gatt_server`
- `bluetooth_feature_legacy_advertiser`
- `gatt_configuration`
- `i2cspm` (mikroe instance)
- `iostream_retarget_stdio`
- `nvm3_lib`
- `sl_system`

---

## ⚠️ Common Build Issues

### Issue 1: GATT Database Errors
```
Error: gattdb_ir_sensor_characteristic undeclared
```

**Solution:**
1. Open `config/btconf/gatt_configuration.btconf`
2. Right-click → **Generate**
3. Clean and rebuild project

### Issue 2: Missing Include Paths
```
Error: sl_i2cspm.h not found
```

**Solution:**
- SDK paths should be auto-configured
- Verify in **Project Properties** → **C/C++ Build** → **Settings** → **Includes**
- Typical paths:
  ```
  ${StudioSdkPath}/platform/service/iostream/inc
  ${StudioSdkPath}/platform/driver/i2cspm/inc
  ${StudioSdkPath}/platform/emlib/inc
  ```

### Issue 3: Linker Errors
```
Error: undefined reference to 'sl_i2cspm_mikroe'
```

**Solution:**
- Check `autogen/sl_i2cspm_init.c` is being compiled
- Verify `i2cspm` component is added in `.slcp`
- Regenerate project: **File** → **New** → **Project from .slcp**

### Issue 4: Old Symbol References
```
Error: 'hx711_read' undeclared
```

**Solution:**
- Old code still referencing removed files
- Search project for `hx711`, `loadcell`, `weight_of_one`, etc.
- Remove or comment out old references

---

## 🎯 Build Targets

### Debug Build (Development)
- Optimization: `-Og` (debug-friendly)
- Symbols: Included
- Size: Larger (~150-200 KB)

```bash
# In Simplicity Studio:
Build Configuration: Debug
```

### Release Build (Production)
- Optimization: `-Os` (size optimization)
- Symbols: Stripped
- Size: Smaller (~100-150 KB)

```bash
# In Simplicity Studio:
Build Configuration: Release
```

---

## 📤 Flash to Device

### Using Simplicity Studio (Recommended)

1. Connect BGM220 via USB (J-Link)
2. Click **Debug** button (green bug icon)
3. Or: Right-click project → **Debug As** → **Silicon Labs ARM Program**
4. Wait for flash completion
5. Click **Resume** to start running

### Using Commander CLI

```bash
# Windows:
commander flash build/bt_soc_loadcell.hex --device BGM220PC22HNA

# Or use .s37 file:
commander flash build/bt_soc_loadcell.s37 --device BGM220PC22HNA
```

---

## 🖥️ Serial Console Output

To view printf debug messages:

1. In Simplicity Studio: **Tools** → **Simplicity Commander**
2. Select **Serial Console** tab
3. Configure:
   - Baud rate: **115200**
   - Data bits: **8**
   - Stop bits: **1**
   - Parity: **None**
4. Connect to COM port (USB VCOM)

You should see:
```
========== SMART PARKING SYSTEM ==========
Initializing peripherals...
IR Sensors initialized: car_in=PB0, car_out=PB1
Servo motors initialized: ...
System ready!
==========================================
```

---

## 🐛 Debugging Tips

### Enable More Debug Output

In `app.c`, add verbose logging:
```c
#define DEBUG_VERBOSE 1

#if DEBUG_VERBOSE
    printf("IR car_in raw: %d\n", GPIO_PinInGet(IR_CAR_IN_PORT, IR_CAR_IN_PIN));
#endif
```

### Use RTT (Real-Time Transfer)

For faster debug output than UART:
1. Add `SEGGER RTT` component in `.slcp`
2. Replace `printf()` with `SEGGER_RTT_printf()`
3. Use **J-Link RTT Viewer** to monitor

### Breakpoint Debugging

Set breakpoints in:
- `app_init()` - Check initialization
- `ir_sensor_update()` - Monitor sensor readings
- `ble_process_event()` - Debug BLE events

---

## ✅ Verification Checklist

After successful build and flash:

- [ ] Serial console shows startup messages
- [ ] BLE device visible in nRF Connect (name: "BGM220")
- [ ] Can connect via BLE
- [ ] GATT service UUID matches: `80c17bcd...`
- [ ] IR sensor notifications work
- [ ] Display write characteristics functional
- [ ] No hard faults or crashes

---

## 📚 Additional Resources

- [Silicon Labs BGM220 Datasheet](https://www.silabs.com/documents/public/data-sheets/bgm220-datasheet.pdf)
- [Bluetooth LE Fundamentals](https://www.silabs.com/documents/public/application-notes/an1377-using-bluetooth-le-gatt-database.pdf)
- [Gecko SDK Documentation](https://docs.silabs.com/gecko-platform/latest/)

---

## 🆘 Get Help

If build issues persist:

1. **Clean Everything:**
   ```bash
   Delete: GNU ARM v12.2.1 - Default/ folder
   Project → Clean...
   Rebuild
   ```

2. **Re-import Project:**
   - Export `.slcp` file
   - Create new project from `.slcp`
   - Copy source files

3. **Contact Support:**
   📧 duongkhang1676@gmail.com

---

**Build Date:** December 4, 2025  
**Project:** Smart Parking System  
**Platform:** BGM220PC22HNA (BRD4314A)
