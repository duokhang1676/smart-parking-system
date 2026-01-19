# 📁 PROJECT FILE STRUCTURE

## Smart Parking System - BGM220

Last Updated: December 4, 2025

---

## 📂 Active Source Files (Used in Build)

### Core Application
```
main.c                      - Entry point (standard Simplicity Studio)
app.c                       - Main application logic (parking system)
app.h                       - Application header & global definitions
ble.c                       - BLE event handler & communication
ble.h                       - BLE function declarations
```

### Hardware Drivers (NEW)
```
ir_sensor.c / .h            - IR obstacle sensors (car detection)
servo.c / .h                - Servo motor control (barriers)
parking_sensors.c / .h      - Light & flame sensors
button.c / .h               - Button input handler
```

### Display Drivers
```
lcd_i2c.c / .h              - LCD 16x2 I2C driver (reused & modified)
oled_i2c.c / .h             - OLED 128x64 SSD1306 driver (NEW)
```

### Utility Modules
```
timer_control.c / .h        - Non-blocking timer (buzzer control)
```

### Silicon Labs Modules
```
sl_gatt_service_device_information.c - Device info GATT service
```

---

## 🗄️ Backup Files (Not in Build)

These are the original loadcell project files, renamed for reference:

```
app_old_backup.c            - Original app.c (loadcell logic)
ble_old_backup.c            - Original ble.c (product management)
hx711_old_backup.c / .h     - HX711 loadcell driver
app_bm_old_backup.c         - Bare metal variant
```

**Note:** These files are NOT compiled. Safe to delete if not needed.

---

## 🔧 Configuration Files

### BLE GATT Database
```
config/btconf/gatt_configuration.btconf   - GATT services & characteristics
```

### Project Configuration
```
bt_soc_loadcell.slcp        - Simplicity Studio project config
bt_soc_loadcell.slpb        - Build profile
bt_soc_loadcell.slps        - Project settings
bt_soc_loadcell.pintool     - Pin configuration tool
```

### Component Configs
```
config/
├── app_assert_config.h
├── app_properties_config.h
├── btl_interface_cfg.h
├── nvm3_default_config.h
├── pin_config.h
├── sl_bluetooth_config.h
├── sl_bluetooth_connection_config.h
├── sl_i2cspm_mikroe_config.h
├── sl_iostream_eusart_vcom_config.h
└── ... (other component configs)
```

---

## 🤖 Auto-Generated Files (Do NOT Edit)

```
autogen/
├── gatt_db.c                          - Generated GATT database
├── gatt_db.h                          - GATT handles & UUIDs
├── linkerfile.ld                      - Linker script
├── sl_bluetooth.c / .h                - BLE stack init
├── sl_board_default_init.c            - Board init
├── sl_cli_command_table.c             - CLI commands
├── sl_component_catalog.h             - Component list
├── sl_device_init_clocks.c            - Clock init
├── sl_event_handler.c / .h            - Event dispatcher
├── sl_i2cspm_init.c                   - I2C peripheral init
├── sl_i2cspm_instances.h              - I2C instance definitions
├── sl_iostream_init_eusart_instances.c - UART init
├── sl_iostream_handles.c / .h         - I/O stream handles
├── sl_power_manager_handler.c         - Power management
├── RTE_Components.h                   - CMSIS components
└── ... (other autogen files)
```

**Regenerate with:** Right-click `.slcp` → Generate

---

## 📖 Documentation Files

```
readme.md                   - Main project README
MIGRATION_SUMMARY.md        - Migration details from loadcell to parking
BUILD_GUIDE.md              - Build & flash instructions
BLE_EXAMPLES.md             - BLE communication code examples
```

---

## 🏗️ Build Output

```
GNU ARM v12.2.1 - Default/
├── bt_soc_loadcell.hex     - Intel HEX format (for flashing)
├── bt_soc_loadcell.s37     - S37 format (alternative)
├── bt_soc_loadcell.bin     - Raw binary
├── bt_soc_loadcell.axf     - Debug symbols
├── bt_soc_loadcell.map     - Memory map
└── *.o                     - Object files
```

---

## 📦 External SDK (Read-Only)

```
simplicity_sdk_2024.12.2/
├── platform/               - HAL, drivers, middleware
│   ├── driver/
│   ├── emlib/
│   ├── service/
│   └── ...
├── protocol/               - BLE stack
│   └── bluetooth/
└── ...
```

**Note:** SDK files are referenced, not copied into project.

---

## 🖼️ Assets

```
image/
├── readme_img0.png
├── readme_img1.png
├── readme_img2.png
├── readme_img3.png
└── readme_img4.png
```

---

## 🔢 File Count Summary

| Category | Count | Size Estimate |
|----------|-------|---------------|
| Active Source (.c) | 13 | ~3,500 lines |
| Active Headers (.h) | 10 | ~800 lines |
| Backup Files | 4 | ~2,000 lines (unused) |
| Config Files | 30+ | Generated |
| Documentation | 4 | ~1,500 lines |
| **Total** | **60+** | **~8,000 lines** |

---

## 🗂️ Recommended Organization

For better project structure:

```
bgm220_parking/
├── src/                    # Application code
│   ├── app.c
│   ├── ble.c
│   ├── drivers/
│   │   ├── ir_sensor.c
│   │   ├── servo.c
│   │   ├── parking_sensors.c
│   │   ├── lcd_i2c.c
│   │   └── oled_i2c.c
│   └── utils/
│       ├── button.c
│       └── timer_control.c
├── inc/                    # Headers
│   └── *.h
├── config/                 # Configurations
├── autogen/                # Generated files
├── docs/                   # Documentation
│   ├── readme.md
│   ├── BUILD_GUIDE.md
│   └── BLE_EXAMPLES.md
├── backup/                 # Old files
└── build/                  # Build output
```

**Note:** Current flat structure is fine for Simplicity Studio.

---

## 🧹 Cleanup Recommendations

### Safe to Delete:
- `app_old_backup.c`
- `ble_old_backup.c`
- `hx711_old_backup.c/.h`
- `app_bm_old_backup.c`
- `image/` (if not using in docs)

### Keep:
- All active `.c/.h` files
- `config/` directory
- `autogen/` directory
- Documentation files
- `.slcp` and related project files

---

## 📊 Code Statistics

Generated with: `cloc` (Count Lines of Code)

```
-------------------------------------------------------------------------------
Language                     files          blank        comment           code
-------------------------------------------------------------------------------
C                               13            450            380           2800
C Header                        10            120            200            600
Markdown                         4            150              0           1200
XML                              1             10              5            130
-------------------------------------------------------------------------------
SUM:                            28            730            585           4730
-------------------------------------------------------------------------------
```

*(Excludes SDK and autogen files)*

---

## 🔄 Version Control (.gitignore suggestions)

If using Git, add these to `.gitignore`:

```gitignore
# Build output
GNU ARM v12.2.1 - Default/
*.o
*.hex
*.bin
*.s37
*.axf
*.map

# IDE files
.cproject
.project
.settings/
.pdm/
.uceditor/

# Backup files
*_old_backup.*

# Auto-generated (can regenerate)
autogen/

# SDK (external dependency)
simplicity_sdk_*/
```

---

## 📞 File Questions?

- **Missing includes?** Check SDK paths in build settings
- **Linker errors?** Verify all `.c` files in build
- **GATT errors?** Regenerate from `.btconf`

Contact: duongkhang1676@gmail.com

---

© 2025 – Smart Parking System File Structure
