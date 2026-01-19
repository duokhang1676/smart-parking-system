#ifndef BLE_H
#define BLE_H

#include "sl_bt_api.h"
#include <stdint.h>

extern uint8_t connection_handle;

/**
 * @brief Initialize BLE stack and start advertising
 */
void ble_init(void);

/**
 * @brief Process BLE events
 * @param evt Pointer to BLE event
 */
void ble_process_event(sl_bt_msg_t *evt);

/**
 * @brief Notify IR sensor status via BLE
 * @param data IR status data (2 bytes)
 * @param length Data length
 */
void ble_notify_ir_status(uint8_t *data, uint8_t length);

/**
 * @brief Notify sensor status via BLE
 * @param data Sensor status data (3 bytes)
 * @param length Data length
 */
void ble_notify_sensor_status(uint8_t *data, uint8_t length);

/**
 * @brief Send IR state change message via BLE
 * @param state_code State code (0=car_in_false, 1=car_in_true, 2=car_out_false, 3=car_out_true)
 */
void ble_send_ir_state_message(uint8_t state_code);

#endif // BLE_H
