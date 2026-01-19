#ifndef IR_SENSOR_H
#define IR_SENSOR_H

#include "em_gpio.h"
#include <stdbool.h>
#include <stdint.h>

// IR Sensor GPIO definitions
#define IR_CAR_IN_PORT      gpioPortC
#define IR_CAR_IN_PIN       0

#define IR_CAR_OUT_PORT     gpioPortC
#define IR_CAR_OUT_PIN      2

// IR Sensor states
typedef enum {
    IR_NO_CAR = 0,      // No car detected (IR beam not broken)
    IR_CAR_DETECTED = 1  // Car detected (IR beam broken)
} ir_state_t;

// IR Sensor data structure
typedef struct {
    bool car_in_detected;
    bool car_out_detected;
    uint32_t car_in_timestamp;
    uint32_t car_out_timestamp;
} ir_sensor_data_t;

extern ir_sensor_data_t ir_data;

/**
 * @brief Initialize IR sensor GPIO pins
 */
void ir_sensor_init(void);

/**
 * @brief Read car_in sensor state
 * @return true if car detected, false otherwise
 */
bool ir_read_car_in(void);

/**
 * @brief Read car_out sensor state
 * @return true if car detected, false otherwise
 */
bool ir_read_car_out(void);

/**
 * @brief Update IR sensor data structure
 */
void ir_sensor_update(void);

/**
 * @brief Get packed sensor status for BLE transmission (2 bytes)
 * byte[0]: car_in state (0 or 1)
 * byte[1]: car_out state (0 or 1)
 */
void ir_get_status_bytes(uint8_t *status);

#endif // IR_SENSOR_H
