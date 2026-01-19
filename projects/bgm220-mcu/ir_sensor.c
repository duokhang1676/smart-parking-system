#include "ir_sensor.h"
#include "em_gpio.h"
#include "sl_sleeptimer.h"
#include <stdio.h>

// Global IR sensor data
ir_sensor_data_t ir_data = {
    .car_in_detected = false,
    .car_out_detected = false,
    .car_in_timestamp = 0,
    .car_out_timestamp = 0
};

/**
 * @brief Initialize IR sensor GPIO pins
 * IR sensors output LOW when object detected, HIGH when no object
 */
void ir_sensor_init(void)
{
    // Configure IR sensor pins as input with pull-up
    GPIO_PinModeSet(IR_CAR_IN_PORT, IR_CAR_IN_PIN, gpioModeInputPull, 1);
    GPIO_PinModeSet(IR_CAR_OUT_PORT, IR_CAR_OUT_PIN, gpioModeInputPull, 1);
}

/**
 * @brief Read car_in sensor state
 * @return true if car detected (sensor LOW), false if no car (sensor HIGH)
 */
bool ir_read_car_in(void)
{
    // IR sensor outputs LOW when object blocks the beam
    return (GPIO_PinInGet(IR_CAR_IN_PORT, IR_CAR_IN_PIN) == 0);
}

/**
 * @brief Read car_out sensor state
 * @return true if car detected (sensor LOW), false if no car (sensor HIGH)
 */
bool ir_read_car_out(void)
{
    // IR sensor outputs LOW when object blocks the beam
    return (GPIO_PinInGet(IR_CAR_OUT_PORT, IR_CAR_OUT_PIN) == 0);
}

/**
 * @brief Update IR sensor data structure with current readings
 */
void ir_sensor_update(void)
{
    bool car_in_now = ir_read_car_in();
    bool car_out_now = ir_read_car_out();
    
    // Detect rising edge (car just detected)
    if (car_in_now && !ir_data.car_in_detected) {
        ir_data.car_in_timestamp = sl_sleeptimer_get_tick_count();
        //printf("IR: Car detected at entrance\n");
    }
    
    if (car_out_now && !ir_data.car_out_detected) {
        ir_data.car_out_timestamp = sl_sleeptimer_get_tick_count();
        //printf("IR: Car detected at exit\n");
    }
    
    // Update current state
    ir_data.car_in_detected = car_in_now;
    ir_data.car_out_detected = car_out_now;
}

/**
 * @brief Get packed sensor status for BLE transmission
 * @param status Pointer to 2-byte array to store status
 */
void ir_get_status_bytes(uint8_t *status)
{
    status[0] = ir_data.car_in_detected ? 1 : 0;
    status[1] = ir_data.car_out_detected ? 1 : 0;
}
