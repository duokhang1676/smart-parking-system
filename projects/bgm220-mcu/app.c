/*******************************************************************************
* Smart Parking System with BLE
* Copyright 2025 - Parking Management System
*
* Features:
* - IR sensors detect cars at entrance/exit
* - Servo barriers control access (0°=open, 90°=closed)
* - Flame sensor for fire detection
* - LCD & OLED displays for information
* - BLE communication for remote monitoring & control
* - Button for manual control and alarm reset
*******************************************************************************/

#include <stdio.h>
#include <string.h>
#include <ctype.h>
#include "sl_sleeptimer.h"
#include "sl_i2cspm_instances.h"
#include "sl_bt_api.h"
#include "sl_iostream.h"
#include "sl_iostream_handles.h"
#include "app.h"
#include "ble.h"
#include "ir_sensor.h"
#include "servo.h"
#include "parking_sensors.h"
#include "button.h"
#include "timer_control.h"
#include "lcd_i2c.h"
#include "oled_i2c.h"
#include "em_gpio.h"

extern sl_i2cspm_t *sl_i2cspm_mikroe;

// UART command buffer
#define UART_CMD_BUFFER_SIZE 64
static char uart_cmd_buffer[UART_CMD_BUFFER_SIZE];
static uint8_t uart_cmd_index = 0;

/*************** Global Variables ***************/
parking_config_t parking_config = {
    .barrier_auto_close_delay_sec = 2,  // Auto-close after 2 seconds
    .alarm_enabled = 1,
    .night_mode_enabled = 1,
    .reserved = 0
};

parking_stats_t parking_stats = {
    .total_cars_in = 0,
    .total_cars_out = 0,
    .current_cars_in_lot = 0,
    .alarm_triggers = 0
};

// Display buffers
char lcd_display_buffer[100] = "Parking System";
char oled_display_buffer[100] = "Welcome!";
bool display_update_needed = true;

// Fire alarm state
bool fire_alarm_active = false;

// Earthquake alarm state
bool earthquake_alarm_active = false;

// LED control (GPIO PB4)
#define LED_PORT gpioPortB
#define LED_PIN 4

// Parking slot information from PC
static char slot_recommend[32] = "A0 - B0 - C0";
static uint8_t parking_num_slot[3] = {0, 0, 0};  // A, B, C occupied count
static uint8_t slot_total[3] = {5, 5, 5};  // A, B, C total slots

// State tracking
static bool last_car_in_state = false;
static bool last_car_out_state = false;
static uint32_t barrier_in_close_time = 0;
static uint32_t barrier_out_close_time = 0;

/*************** UART Command Processing ***************/

/**
 * @brief Process received UART command
 */
void process_uart_command(const char* cmd)
{
    // Remove trailing whitespace
    char clean_cmd[UART_CMD_BUFFER_SIZE];
    strncpy(clean_cmd, cmd, sizeof(clean_cmd) - 1);
    clean_cmd[sizeof(clean_cmd) - 1] = '\0';
    
    // Remove newline/carriage return
    size_t len = strlen(clean_cmd);
    while (len > 0 && (clean_cmd[len-1] == '\n' || clean_cmd[len-1] == '\r')) {
        clean_cmd[--len] = '\0';
    }
    
    // Compare command
    if (strcmp(clean_cmd, "open_in") == 0) {
        servo_open_barrier_in();
        printf("OK: Entrance barrier opened\n");
        fflush(stdout);
    } 
    else if (strcmp(clean_cmd, "open_out") == 0) {
        servo_open_barrier_out();
        printf("OK: Exit barrier opened\n");
        fflush(stdout);
    }
    else if (strcmp(clean_cmd, "close_in") == 0) {
        servo_close_barrier_in();
        barrier_in_close_time = 0;  // Cancel auto-close timer
        printf("OK: Entrance barrier closed\n");
        fflush(stdout);
    }
    else if (strcmp(clean_cmd, "close_out") == 0) {
        servo_close_barrier_out();
        barrier_out_close_time = 0;  // Cancel auto-close timer
        printf("OK: Exit barrier closed\n");
        fflush(stdout);
    }
    else if (strcmp(clean_cmd, "earthquake") == 0) {
        earthquake_alarm_active = true;
        fire_alarm_active = false;  // Override fire alarm
        
        // Open both barriers immediately
        servo_open_barrier_in();
        servo_open_barrier_out();
        
        // Cancel auto-close timers
        barrier_in_close_time = 0;
        barrier_out_close_time = 0;
        
        printf("OK: Earthquake alarm activated\n");
        fflush(stdout);
    }
    else if (strcmp(clean_cmd, "earthquake_stop") == 0) {
        earthquake_alarm_active = false;
        printf("OK: Earthquake alarm stopped\n");
        fflush(stdout);
    }
    else if (strcmp(clean_cmd, "turn_on_light") == 0) {
        GPIO_PinOutSet(LED_PORT, LED_PIN);
        printf("OK: Light turned on\n");
        fflush(stdout);
    }
    else if (strcmp(clean_cmd, "turn_off_light") == 0) {
        GPIO_PinOutClear(LED_PORT, LED_PIN);
        printf("OK: Light turned off\n");
        fflush(stdout);
    }
    else if (strncmp(clean_cmd, "slot_recommend:", 15) == 0) {
        strncpy(slot_recommend, clean_cmd + 15, sizeof(slot_recommend) - 1);
        slot_recommend[sizeof(slot_recommend) - 1] = '\0';
        display_update_needed = true;
        printf("OK: Slot recommend updated: %s\n", slot_recommend);
        fflush(stdout);
    }
    else if (strncmp(clean_cmd, "parking_num_slot:", 17) == 0) {
        // Parse "parking_num_slot:2,1,1" format
        const char* data = clean_cmd + 17;
        int count = sscanf(data, "%hhu,%hhu,%hhu", 
                          &parking_num_slot[0], 
                          &parking_num_slot[1], 
                          &parking_num_slot[2]);
        if (count == 3) {
            display_update_needed = true;
            printf("OK: Parking slot data updated: %d,%d,%d\n", 
                   parking_num_slot[0], parking_num_slot[1], parking_num_slot[2]);
        } else {
            printf("ERROR: Invalid parking_num_slot format\n");
        }
        fflush(stdout);
    }
    else if (strcmp(clean_cmd, "update_display") == 0) {
        // PC signals to update display (slot data will follow)
        printf("OK: Ready for display data\n");
        fflush(stdout);
    }
    else if (len > 0) {
        printf("ERROR: Unknown command '%s'\n", clean_cmd);
        fflush(stdout);
    }
}

/**
 * @brief Check for incoming UART data
 */
void check_uart_input(void)
{
    char c;
    size_t bytes_read;
    
    // Process multiple characters per call (up to 10 commands per loop)
    for (int i = 0; i < 50; i++) {
        // Read one character at a time
        if (sl_iostream_read(sl_iostream_vcom_handle, &c, 1, &bytes_read) == SL_STATUS_OK && bytes_read > 0) {
            if (c == '\n' || c == '\r') {
                // End of command
                if (uart_cmd_index > 0) {
                    uart_cmd_buffer[uart_cmd_index] = '\0';
                    printf("[CMD] Received: %s\n", uart_cmd_buffer);
                    fflush(stdout);
                    process_uart_command(uart_cmd_buffer);
                    uart_cmd_index = 0;
                }
            } else if (uart_cmd_index < UART_CMD_BUFFER_SIZE - 1) {
                // Add character to buffer
                uart_cmd_buffer[uart_cmd_index++] = c;
            } else {
                // Buffer overflow - reset
                printf("[ERROR] UART buffer overflow\n");
                fflush(stdout);
                uart_cmd_index = 0;
            }
        } else {
            // No more data available
            break;
        }
    }
}

/*************** Display Update Functions ***************/

/**
 * @brief Update LCD display with current info
 */
void update_lcd_display(void)
{
    char line1[17], line2[17];
    
    // LCD always displays slot recommendation only
    snprintf(line1, sizeof(line1), "Recommend:");
    snprintf(line2, sizeof(line2), "%s", slot_recommend);
    
    lcd_clear();
    lcd_set_cursor(0, 0);
    lcd_write_string(line1);
    lcd_set_cursor(0, 1);
    lcd_write_string(line2);
}

/**
 * @brief Update OLED display with current info
 */
void update_oled_display(void)
{
    char line[32];
    
    oled_clear();
    oled_write_string_at(0, 0, "PARKING SYSTEM");
    
    if (earthquake_alarm_active) {
        oled_write_string_at(0, 2, "!! EARTHQUAKE !!");
        oled_write_string_at(0, 3, "EVACUATE NOW!");
        oled_write_string_at(0, 4, "Barriers OPEN");
        oled_write_string_at(0, 5, "Leave immediately");
    } else if (fire_alarm_active) {
        oled_write_string_at(0, 2, "!!! FIRE ALARM !!!");
        oled_write_string_at(0, 3, "Barriers OPEN");
        oled_write_string_at(0, 4, "Press BTN to stop");
    } else {
        // Display parking slot table (always show)
        oled_write_string_at(0, 1, "Slot Occ Avail Tot");
        oled_write_string_at(0, 2, "-------------------");
        
        // Row A
        uint8_t avail_a = slot_total[0] - parking_num_slot[0];
        snprintf(line, sizeof(line), " A   %2d   %2d   %2d", 
                 parking_num_slot[0], avail_a, slot_total[0]);
        oled_write_string_at(0, 3, line);
        
        // Row B
        uint8_t avail_b = slot_total[1] - parking_num_slot[1];
        snprintf(line, sizeof(line), " B   %2d   %2d   %2d", 
                 parking_num_slot[1], avail_b, slot_total[1]);
        oled_write_string_at(0, 4, line);
        
        // Row C
        uint8_t avail_c = slot_total[2] - parking_num_slot[2];
        snprintf(line, sizeof(line), " C   %2d   %2d   %2d", 
                 parking_num_slot[2], avail_c, slot_total[2]);
        oled_write_string_at(0, 5, line);
        
        oled_write_string_at(0, 6, "-------------------");
        
        // Total row
        uint8_t total_occ = parking_num_slot[0] + parking_num_slot[1] + parking_num_slot[2];
        uint8_t total_avail = avail_a + avail_b + avail_c;
        uint8_t total_all = slot_total[0] + slot_total[1] + slot_total[2];
        snprintf(line, sizeof(line), "ALL  %2d   %2d   %2d", 
                 total_occ, total_avail, total_all);
        oled_write_string_at(0, 7, line);
    }
    
    oled_update();
}

/**
 * @brief Handle button events
 */
void app_button_handler(uint8_t event)
{
    if (event == BUTTON_EVENT_SHORT_PRESS) {
        // If earthquake alarm is active, stop it (priority)
        if (earthquake_alarm_active) {
            earthquake_alarm_active = false;
            
            // Close both barriers
            servo_close_barrier_in();
            servo_close_barrier_out();
            
            display_update_needed = true;
            
        } else if (fire_alarm_active) {
            // If fire alarm is active, stop it
            fire_alarm_active = false;
            
            // Close both barriers
            servo_close_barrier_in();
            servo_close_barrier_out();
            
            display_update_needed = true;
            
        } else {
            // Normal mode: toggle both barriers
            if (servo_status.barrier_in_state == SERVO_STATE_OPEN || 
                servo_status.barrier_out_state == SERVO_STATE_OPEN) {
                // If any barrier is open, close both
                servo_close_barrier_in();
                servo_close_barrier_out();
            } else {
                // If both are closed, open both
                servo_open_barrier_in();
                servo_open_barrier_out();
            }
            
            if (is_trigger_done()) {
                trigger_gpio_high_nonblocking(100);
            }
        }
        
    } else if (event == BUTTON_EVENT_LONG_PRESS) {
        parking_stats.total_cars_in = 0;
        parking_stats.total_cars_out = 0;
        parking_stats.current_cars_in_lot = 0;
        parking_stats.alarm_triggers = 0;
        
        display_update_needed = true;
        
        // Beep confirmation
        if (is_trigger_done()) {
            trigger_gpio_high_nonblocking(100);
            sl_sleeptimer_delay_millisecond(200);
            trigger_gpio_high_nonblocking(100);
        }
    }
}

/**
 * @brief Update displays when needed
 */
void app_update_displays(void)
{
    if (display_update_needed) {
        update_lcd_display();
        update_oled_display();
        display_update_needed = false;
    }
}

/*************** Main Application Functions ***************/

/**
 * @brief Application initialization
 */
SL_WEAK void app_init(void)
{
    // Initialize LED control pin (PB4)
    GPIO_PinModeSet(LED_PORT, LED_PIN, gpioModePushPull, 0);
    
    // Initialize all drivers
    timer_control_init();
    button_init();
    ir_sensor_init();
    servo_init();
    parking_sensors_init();
    
    // Initialize displays
    lcd_init();
    oled_init();
    
    // Register button callback
    button_register_callback(app_button_handler);
    
    // Initial display update
    display_update_needed = true;
    app_update_displays();
    
    // Startup beep
    if (is_trigger_done()) {
        trigger_gpio_high_nonblocking(200);
    }
}

/**
 * @brief Runtime initialization (called after app_init)
 */
SL_WEAK void app_init_runtime(void)
{
    // Empty - can be used for RTOS task creation if needed
}

/**
 * @brief Main application loop
 */
SL_WEAK void app_process_action(void)
{
    static uint32_t loop_counter = 0;
    loop_counter++;
    
    // Check for UART commands from PC
    check_uart_input();
    
    // Update all sensors
    ir_sensor_update();
    parking_sensors_update();
    button_update();
    
    // Keep buzzer on during earthquake alarm (short beeps pattern)
    if (earthquake_alarm_active) {
        if (is_trigger_done()) {
            trigger_gpio_high_nonblocking(200);  // Short beep
        }
    }
    
    // Handle flame detection alarm
    if (parking_sensors.flame_state == FLAME_DETECTED && !fire_alarm_active && !earthquake_alarm_active) {
        fire_alarm_active = true;
        
        // Open both barriers immediately (0 degrees)
        servo_open_barrier_in();
        servo_open_barrier_out();
        
        parking_stats.alarm_triggers++;
        display_update_needed = true;
        
        // Notify via BLE
        if (connection_handle != 0xff) {
            uint8_t sensor_status[3];
            parking_sensors_get_status(sensor_status);
            ble_notify_sensor_status(sensor_status, 3);
        }
    }
    
    // Keep buzzer on during fire alarm
    if (fire_alarm_active && !earthquake_alarm_active) {
        if (is_trigger_done()) {
            trigger_gpio_high_nonblocking(1000);  // Continuous long beep
        }
    }
    
    // Detect car_in state changes and send BLE message
    if (ir_data.car_in_detected != last_car_in_state) {
        if (ir_data.car_in_detected) {
            // car_in_detected = true -> send code 1
//            ble_send_ir_state_message(1);
            printf("car_in:1\n");
            fflush(stdout);
            
            // Beep on state change
            if (is_trigger_done()) {
                trigger_gpio_high_nonblocking(100);
            }
            
            if (!fire_alarm_active && !earthquake_alarm_active) {
                // Open entrance barrier (0 degrees)
                //servo_open_barrier_in();
                
                // Update stats
                parking_stats.total_cars_in++;
                parking_stats.current_cars_in_lot++;
                
                display_update_needed = true;
            }
        } else {
            // car_in_detected = false -> send code 0
            //ble_send_ir_state_message(0);
            printf("car_in:0\n");
            fflush(stdout);
            
            // Beep on state change
            if (is_trigger_done()) {
                trigger_gpio_high_nonblocking(100);
            }
            
            // Schedule auto-close after 2 seconds when car passes
            if (!fire_alarm_active && !earthquake_alarm_active) {
                barrier_in_close_time = sl_sleeptimer_get_tick_count() +
                                        sl_sleeptimer_ms_to_tick(parking_config.barrier_auto_close_delay_sec * 1000);
            }
        }
        last_car_in_state = ir_data.car_in_detected;
    }
    
    // Detect car_out state changes and send BLE message
    if (ir_data.car_out_detected != last_car_out_state) {
        if (ir_data.car_out_detected) {
            // car_out_detected = true -> send code 3
            //ble_send_ir_state_message(3);
            printf("car_out:1\n");
            fflush(stdout);
            
            // Beep on state change
            if (is_trigger_done()) {
                trigger_gpio_high_nonblocking(100);
            }
            
            if (!fire_alarm_active && !earthquake_alarm_active) {
                // Open exit barrier (0 degrees)
                //servo_open_barrier_out();
                
                // Update stats
                parking_stats.total_cars_out++;
                if (parking_stats.current_cars_in_lot > 0) {
                    parking_stats.current_cars_in_lot--;
                }
                
                display_update_needed = true;
            }
        } else {
            // car_out_detected = false -> send code 2
            //ble_send_ir_state_message(2);
            printf("car_out:0\n");
            fflush(stdout);
            
            // Beep on state change
            if (is_trigger_done()) {
                trigger_gpio_high_nonblocking(100);
            }
            
            // Schedule auto-close after 2 seconds when car passes
            if (!fire_alarm_active && !earthquake_alarm_active) {
                barrier_out_close_time = sl_sleeptimer_get_tick_count() +
                                         sl_sleeptimer_ms_to_tick(parking_config.barrier_auto_close_delay_sec * 1000);
            }
        }
        last_car_out_state = ir_data.car_out_detected;
    }
    
    // Auto-close entrance barrier after 2s (only when no fire/earthquake alarm)
    if (!fire_alarm_active && !earthquake_alarm_active && barrier_in_close_time > 0 &&
        sl_sleeptimer_get_tick_count() >= barrier_in_close_time &&
        !ir_data.car_in_detected) {
        servo_close_barrier_in();
        barrier_in_close_time = 0;
    }
    
    // Auto-close exit barrier after 2s (only when no fire/earthquake alarm)
    if (!fire_alarm_active && !earthquake_alarm_active && barrier_out_close_time > 0 &&
        sl_sleeptimer_get_tick_count() >= barrier_out_close_time &&
        !ir_data.car_out_detected) {
        servo_close_barrier_out();
        barrier_out_close_time = 0;
    }
    
    // Update displays
    app_update_displays();
    
    // Sleep for 100ms (faster response to UART commands)
    sl_sleeptimer_delay_millisecond(100);
}

/**
 * @brief BLE event handler
 */
void sl_bt_on_event(sl_bt_msg_t *evt)
{
    ble_process_event(evt);
}
