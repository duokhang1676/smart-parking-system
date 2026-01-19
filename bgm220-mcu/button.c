#include "button.h"
#include "em_gpio.h"
#include <stdio.h>

// Button state tracking
static button_state_t current_state = BUTTON_RELEASED;
static button_state_t last_state = BUTTON_RELEASED;
static uint32_t press_counter = 0;
static button_callback_t button_callback = NULL;

// Timing constants (in update cycles)
#define DEBOUNCE_CYCLES     3      // ~150ms at 50ms update rate
#define LONG_PRESS_CYCLES   20     // ~1s at 50ms update rate

/**
 * @brief Initialize button GPIO
 */
void button_init(void)
{
    // Configure button pin as input with pull-up (active low)
    GPIO_PinModeSet(BUTTON_PORT, BUTTON_PIN, gpioModeInputPullFilter, 1);
}

/**
 * @brief Read button state (with active-low logic)
 * @return true if pressed (LOW), false if released (HIGH)
 */
bool button_is_pressed(void)
{
    return (GPIO_PinInGet(BUTTON_PORT, BUTTON_PIN) == 0);
}

/**
 * @brief Update button state and detect events
 * Call this periodically (e.g., every 50-100ms)
 * @return Detected button event
 */
button_event_t button_update(void)
{
    button_event_t event = BUTTON_EVENT_NONE;
    bool pressed = button_is_pressed();
    
    // Detect state change
    if (pressed != (current_state == BUTTON_PRESSED)) {
        if (pressed) {
            // Button just pressed
            current_state = BUTTON_PRESSED;
            press_counter = 0;
        } else {
            // Button just released
            current_state = BUTTON_RELEASED;
            
            // Determine event type based on press duration
            if (press_counter >= LONG_PRESS_CYCLES) {
                event = BUTTON_EVENT_LONG_PRESS;
            } else if (press_counter >= DEBOUNCE_CYCLES) {
                event = BUTTON_EVENT_SHORT_PRESS;
            }
            
            // Trigger callback if registered
            if (button_callback != NULL && event != BUTTON_EVENT_NONE) {
                button_callback(event);
            }
        }
    }
    
    // Increment press counter while button is held
    if (current_state == BUTTON_PRESSED) {
        press_counter++;
    }
    
    last_state = current_state;
    return event;
}

/**
 * @brief Register callback for button events
 * @param callback Function to call when button event occurs
 */
void button_register_callback(button_callback_t callback)
{
    button_callback = callback;
}
