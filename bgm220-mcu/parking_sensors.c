#include "parking_sensors.h"
#include "em_gpio.h"
#include <stdio.h>

// Global sensor data
parking_sensor_data_t parking_sensors = {
    .flame_state = FLAME_NOT_DETECTED,
    .flame_alarm_active = false
};

/**
 * @brief Initialize light and flame sensors GPIO
 */
void parking_sensors_init(void)
{
    // Configure sensor pins as input with pull-up
    GPIO_PinModeSet(FLAME_SENSOR_PORT, FLAME_SENSOR_PIN, gpioModeInputPull, 1);
}

/**
 * @brief Read flame sensor state
 * @return true if flame detected (sensor LOW), false otherwise (sensor HIGH)
 * 
 * Most flame sensors output LOW when flame detected
 */
bool flame_sensor_is_detected(void)
{
    return (GPIO_PinInGet(FLAME_SENSOR_PORT, FLAME_SENSOR_PIN) == 0);
}

/**
 * @brief Update all sensor readings
 */
void parking_sensors_update(void)
{
    // Read current states
    bool flame_detected = flame_sensor_is_detected();
    
    // Update flame state
    if (flame_detected != (parking_sensors.flame_state == FLAME_DETECTED)) {
        parking_sensors.flame_state = flame_detected ? FLAME_DETECTED : FLAME_NOT_DETECTED;
        
        if (flame_detected) {
            printf("*** FLAME DETECTED! ***\n");
            parking_sensors.flame_alarm_active = true;
        } else {
            printf("Flame cleared\n");
            parking_sensors.flame_alarm_active = false;
        }
    }
}

/**
 * @brief Get sensor status for BLE/display
 * @param status Output buffer (3 bytes): [flame, alarm, reserved]
 */
void parking_sensors_get_status(uint8_t *status)
{
    status[0] = (uint8_t)parking_sensors.flame_state;
    status[1] = parking_sensors.flame_alarm_active ? 1 : 0;
    status[2] = 0; // Reserved for future use
}
