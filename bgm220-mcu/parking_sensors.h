#ifndef PARKING_SENSORS_H
#define PARKING_SENSORS_H

#include "em_gpio.h"
#include <stdbool.h>
#include <stdint.h>

// Flame Sensor GPIO (digital output: LOW=flame detected, HIGH=no flame)
#define FLAME_SENSOR_PORT   gpioPortC
#define FLAME_SENSOR_PIN    6

// Sensor states
typedef enum {
    FLAME_NOT_DETECTED = 0,
    FLAME_DETECTED = 1
} flame_state_t;

typedef struct {
    flame_state_t flame_state;
    bool flame_alarm_active;
} parking_sensor_data_t;

extern parking_sensor_data_t parking_sensors;

/**
 * @brief Initialize light and flame sensors
 */
void parking_sensors_init(void);

/**
 * @brief Read flame sensor state
 * @return true if flame detected, false otherwise
 */
bool flame_sensor_is_detected(void);

/**
 * @brief Update all sensor readings
 */
void parking_sensors_update(void);

/**
 * @brief Get sensor status for BLE/display
 * @param status Output buffer (3 bytes): [flame, alarm, reserved]
 */
void parking_sensors_get_status(uint8_t *status);

#endif // PARKING_SENSORS_H
