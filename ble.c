#include "ble.h"
#include "app_assert.h"
#include "gatt_db.h"
#include "app.h"
#include "ir_sensor.h"
#include "parking_sensors.h"
#include "servo.h"
#include "timer_control.h"
#include "lcd_i2c.h"
#include "oled_i2c.h"
#include "sl_iostream.h"
#include <stdio.h>
#include <string.h>

uint8_t connection_handle = 0xff;
static uint8_t advertising_set_handle = 0xff;

void ble_init(void)
{
    sl_status_t sc;

    // Create advertiser set
    sc = sl_bt_advertiser_create_set(&advertising_set_handle);
    app_assert_status(sc);

    // Create advertising data
    sc = sl_bt_legacy_advertiser_generate_data(advertising_set_handle,
                                               sl_bt_advertiser_general_discoverable);
    app_assert_status(sc);

    // Set advertising timing (100ms)
    sc = sl_bt_advertiser_set_timing(advertising_set_handle,
                                     160, 160, 0, 0);
    app_assert_status(sc);

    // Start advertising
    sc = sl_bt_legacy_advertiser_start(advertising_set_handle,
                                       sl_bt_legacy_advertiser_connectable);
    app_assert_status(sc);
}

/**
 * @brief Notify IR sensor status via BLE
 * @param data IR status (2 bytes: car_in, car_out)
 * @param length Data length
 */
void ble_notify_ir_status(uint8_t *data, uint8_t length)
{
    if (connection_handle != 0xff) {
        sl_bt_gatt_server_send_notification(
            connection_handle,
            gattdb_ir_sensor_characteristic,
            length,
            data
        );
    }
}

/**
 * @brief Notify sensor status via BLE
 * @param data Sensor status (4 bytes: light, flame, alarm, reserved)
 * @param length Data length
 */
void ble_notify_sensor_status(uint8_t *data, uint8_t length)
{
    if (connection_handle != 0xff) {
        sl_bt_gatt_server_send_notification(
            connection_handle,
            gattdb_sensor_status_characteristic,
            length,
            data
        );
    }
}

void ble_process_event(sl_bt_msg_t *evt)
{
    sl_status_t sc;

    switch (SL_BT_MSG_ID(evt->header)) {
        case sl_bt_evt_system_boot_id:
            ble_init();
            break;

        case sl_bt_evt_connection_opened_id:
            connection_handle = evt->data.evt_connection_opened.connection;
            
            // Connection sound
            trigger_gpio_high_nonblocking(100);
            sl_sleeptimer_delay_millisecond(200);
            trigger_gpio_high_nonblocking(100);
            
            // Set connection parameters
            sl_bt_connection_set_parameters(connection_handle,
                                            40,   // min interval (50ms)
                                            80,   // max interval (100ms)
                                            0,    // latency
                                            400,  // timeout (4s)
                                            0,    // min CE length
                                            0);   // max CE length
            break;

        case sl_bt_evt_gatt_server_characteristic_status_id:
        {
            sl_bt_evt_gatt_server_characteristic_status_t *status_evt =
                &evt->data.evt_gatt_server_characteristic_status;

            // When client enables notifications, send initial data
            if (status_evt->status_flags == sl_bt_gatt_server_client_config &&
                status_evt->client_config_flags == sl_bt_gatt_notification) {
                
                if (status_evt->characteristic == gattdb_ir_sensor_characteristic) {
                    uint8_t ir_status[2];
                    ir_get_status_bytes(ir_status);
                    ble_notify_ir_status(ir_status, 2);
                }
                
                if (status_evt->characteristic == gattdb_sensor_status_characteristic) {
                    uint8_t sensor_status[4];
                    parking_sensors_get_status(sensor_status);
                    ble_notify_sensor_status(sensor_status, 4);
                }
            }
        }
        break;

        case sl_bt_evt_connection_closed_id:
            connection_handle = 0xff;
            
            // Disconnection sound
            trigger_gpio_high_nonblocking(100);
            sl_sleeptimer_delay_millisecond(200);
            trigger_gpio_high_nonblocking(100);
            sl_sleeptimer_delay_millisecond(200);
            trigger_gpio_high_nonblocking(100);

            // Restart advertising
            sc = sl_bt_legacy_advertiser_start(advertising_set_handle,
                                               sl_bt_legacy_advertiser_connectable);
            app_assert_status(sc);
            break;

        case sl_bt_evt_gatt_server_user_write_request_id:
        {
            uint8_t char_id = evt->data.evt_gatt_server_user_write_request.characteristic;
            uint8_t *data = evt->data.evt_gatt_server_user_write_request.value.data;
            uint16_t length = evt->data.evt_gatt_server_user_write_request.value.len;

            // Handle LCD display data
            if (char_id == gattdb_lcd_display_characteristic) {
                memset(lcd_display_buffer, 0, sizeof(lcd_display_buffer));
                memcpy(lcd_display_buffer, data, length < sizeof(lcd_display_buffer) ? length : sizeof(lcd_display_buffer) - 1);
                
                display_update_needed = true;
            }

            // Handle OLED display data
            if (char_id == gattdb_oled_display_characteristic) {
                memset(oled_display_buffer, 0, sizeof(oled_display_buffer));
                memcpy(oled_display_buffer, data, length < sizeof(oled_display_buffer) ? length : sizeof(oled_display_buffer) - 1);
                
                display_update_needed = true;
            }

            // Handle barrier control
            if (char_id == gattdb_barrier_control_characteristic) {
                if (length >= 2) {
                    uint8_t barrier_in_cmd = data[0];
                    uint8_t barrier_out_cmd = data[1];
                    
                    // Control entrance barrier
                    if (barrier_in_cmd == 1) {
                        servo_open_barrier_in();
                    } else if (barrier_in_cmd == 0) {
                        servo_close_barrier_in();
                    }
                    
                    // Control exit barrier
                    if (barrier_out_cmd == 1) {
                        servo_open_barrier_out();
                    } else if (barrier_out_cmd == 0) {
                        servo_close_barrier_out();
                    }
                    
                    // Confirmation beep
                    if (is_trigger_done()) {
                        trigger_gpio_high_nonblocking(50);
                    }
                }
            }

            // Send response confirmation
            sl_bt_gatt_server_send_user_write_response(
                evt->data.evt_gatt_server_user_write_request.connection,
                char_id,
                SL_STATUS_OK
            );
            break;
        }

        case sl_bt_evt_gatt_server_user_read_request_id:
        {
            uint8_t char_id = evt->data.evt_gatt_server_user_read_request.characteristic;
            
            // Handle read requests for IR sensor
            if (char_id == gattdb_ir_sensor_characteristic) {
                uint8_t ir_status[2];
                ir_get_status_bytes(ir_status);
                
                sl_bt_gatt_server_send_user_read_response(
                    evt->data.evt_gatt_server_user_read_request.connection,
                    char_id,
                    SL_STATUS_OK,
                    2,
                    ir_status,
                    NULL
                );
            }
            
            // Handle read requests for sensor status
            if (char_id == gattdb_sensor_status_characteristic) {
                uint8_t sensor_status[4];
                parking_sensors_get_status(sensor_status);
                
                sl_bt_gatt_server_send_user_read_response(
                    evt->data.evt_gatt_server_user_read_request.connection,
                    char_id,
                    SL_STATUS_OK,
                    4,
                    sensor_status,
                    NULL
                );
            }
            break;
        }

        default:
            break;
    }
}
