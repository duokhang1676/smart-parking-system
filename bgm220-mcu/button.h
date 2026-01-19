#ifndef BUTTON_H
#define BUTTON_H

#include "em_gpio.h"
#include <stdbool.h>
#include <stdint.h>

// Button GPIO definition
#define BUTTON_PORT     gpioPortC
#define BUTTON_PIN      7

// Button states
typedef enum {
    BUTTON_RELEASED = 0,
    BUTTON_PRESSED = 1
} button_state_t;

// Button event types
typedef enum {
    BUTTON_EVENT_NONE = 0,
    BUTTON_EVENT_SHORT_PRESS,
    BUTTON_EVENT_LONG_PRESS
} button_event_t;

// Button callback function type
typedef void (*button_callback_t)(button_event_t event);

/**
 * @brief Initialize button GPIO
 */
void button_init(void);

/**
 * @brief Read button state
 * @return true if pressed, false if released
 */
bool button_is_pressed(void);

/**
 * @brief Update button state and detect events
 * Call this periodically (e.g., every 50-100ms)
 * @return Detected button event
 */
button_event_t button_update(void);

/**
 * @brief Register callback for button events
 * @param callback Function to call when button event occurs
 */
void button_register_callback(button_callback_t callback);

#endif // BUTTON_H
