#ifndef APP_H
#define APP_H

#include <stdbool.h>
#include <stdint.h>

// Parking system configuration
typedef struct {
    uint8_t barrier_auto_close_delay_sec;  // Auto-close barrier after car passes
    uint8_t alarm_enabled;                  // Enable/disable alarm system
    uint8_t night_mode_enabled;             // Enable night mode (auto lighting)
    uint8_t reserved;
} parking_config_t;

// Parking statistics
typedef struct {
    uint32_t total_cars_in;
    uint32_t total_cars_out;
    uint32_t current_cars_in_lot;
    uint32_t alarm_triggers;
} parking_stats_t;

extern parking_config_t parking_config;
extern parking_stats_t parking_stats;

// Display buffers (received from BLE)
extern char lcd_display_buffer[100];
extern char oled_display_buffer[100];
extern bool display_update_needed;

// Fire alarm state
extern bool fire_alarm_active;

/**************************************************************************//**
 * Application Init.
 *****************************************************************************/
void app_init(void);

/**************************************************************************//**
 * Initialize Runtime Environment.
 *****************************************************************************/
void app_init_runtime(void);

/**************************************************************************//**
 * Application Process Action (main loop).
 *****************************************************************************/
void app_process_action(void);

/**************************************************************************//**
 * Proceed with execution.
 *****************************************************************************/
void app_proceed(void);

/**************************************************************************//**
 * Check if it is required to process with execution.
 * @return true if required, false otherwise.
 *****************************************************************************/
bool app_is_process_required(void);

/**************************************************************************//**
 * Handle button events.
 *****************************************************************************/
void app_button_handler(uint8_t event);

/**************************************************************************//**
 * Update displays with current data.
 *****************************************************************************/
void app_update_displays(void);

#endif // APP_H
