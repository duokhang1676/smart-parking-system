#include "servo.h"
#include "em_gpio.h"
#include "em_cmu.h"
#include "sl_udelay.h"
#include <stdio.h>

// Global servo status
servo_status_t servo_status = {
    .barrier_in_state = SERVO_STATE_CLOSED,
    .barrier_out_state = SERVO_STATE_CLOSED
};

/**
 * @brief Initialize servo motors using software PWM
 * Note: For BGM220, we'll use software PWM with GPIO timing
 * For hardware PWM, TIMER peripheral would be needed
 */
void servo_init(void)
{
    // Configure servo pins as push-pull outputs
    GPIO_PinModeSet(SERVO_IN_PORT, SERVO_IN_PIN, gpioModePushPull, 0);
    GPIO_PinModeSet(SERVO_OUT_PORT, SERVO_OUT_PIN, gpioModePushPull, 0);
    
    // Force initialize both barriers to closed position (bypass state check)
    servo_set_angle(SERVO_IN_PORT, SERVO_IN_PIN, SERVO_CLOSED_ANGLE);
    servo_status.barrier_in_state = SERVO_STATE_CLOSED;
    
    servo_set_angle(SERVO_OUT_PORT, SERVO_OUT_PIN, SERVO_CLOSED_ANGLE);
    servo_status.barrier_out_state = SERVO_STATE_CLOSED;
}

/**
 * @brief Generate PWM pulse for servo (software PWM)
 * @param port GPIO port
 * @param pin GPIO pin
 * @param pulse_us Pulse width in microseconds (500-2500)
 * 
 * This is a simplified software PWM. For production, use TIMER peripheral.
 */
static void servo_send_pulse(GPIO_Port_TypeDef port, uint8_t pin, uint16_t pulse_us)
{
    // Send pulse HIGH
    GPIO_PinOutSet(port, pin);
    sl_udelay_wait(pulse_us);
    
    // Send pulse LOW
    GPIO_PinOutClear(port, pin);
    sl_udelay_wait(SERVO_PERIOD_US - pulse_us);
}

/**
 * @brief Set servo angle (0-180 degrees)
 * @param port GPIO port
 * @param pin GPIO pin
 * @param angle Angle in degrees (0-180)
 */
void servo_set_angle(GPIO_Port_TypeDef port, uint8_t pin, uint8_t angle)
{
    // Limit angle to 0-180
    if (angle > 180) {
        angle = 180;
    }
    
    // Convert angle to pulse width (500us to 2500us)
    uint16_t pulse_us = SERVO_MIN_PULSE_US + 
                        ((uint32_t)angle * (SERVO_MAX_PULSE_US - SERVO_MIN_PULSE_US)) / 180;
    
    // Send 3 pulses for fastest response
    for (int i = 0; i < 3; i++) {
        servo_send_pulse(port, pin, pulse_us);
    }
}

/**
 * @brief Open barrier_in (entrance barrier up - 0 degrees)
 */
void servo_open_barrier_in(void)
{
    if (servo_status.barrier_in_state != SERVO_STATE_OPEN) {
        servo_set_angle(SERVO_IN_PORT, SERVO_IN_PIN, SERVO_OPEN_ANGLE);
        servo_status.barrier_in_state = SERVO_STATE_OPEN;
    }
}

/**
 * @brief Close barrier_in (entrance barrier down - 90 degrees)
 */
void servo_close_barrier_in(void)
{
    if (servo_status.barrier_in_state != SERVO_STATE_CLOSED) {
        servo_set_angle(SERVO_IN_PORT, SERVO_IN_PIN, SERVO_CLOSED_ANGLE);
        servo_status.barrier_in_state = SERVO_STATE_CLOSED;
    }
}

/**
 * @brief Open barrier_out (exit barrier up - 0 degrees)
 */
void servo_open_barrier_out(void)
{
    if (servo_status.barrier_out_state != SERVO_STATE_OPEN) {
        servo_set_angle(SERVO_OUT_PORT, SERVO_OUT_PIN, SERVO_OPEN_ANGLE);
        servo_status.barrier_out_state = SERVO_STATE_OPEN;
    }
}

/**
 * @brief Close barrier_out (exit barrier down - 90 degrees)
 */
void servo_close_barrier_out(void)
{
    if (servo_status.barrier_out_state != SERVO_STATE_CLOSED) {
        servo_set_angle(SERVO_OUT_PORT, SERVO_OUT_PIN, SERVO_CLOSED_ANGLE);
        servo_status.barrier_out_state = SERVO_STATE_CLOSED;
    }
}

/**
 * @brief Get current barrier states
 */
servo_status_t servo_get_status(void)
{
    return servo_status;
}
