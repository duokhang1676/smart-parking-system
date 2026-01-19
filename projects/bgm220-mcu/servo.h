#ifndef SERVO_H
#define SERVO_H

#include "em_gpio.h"
#include "em_timer.h"
#include <stdbool.h>
#include <stdint.h>

// Servo GPIO definitions (using PWM-capable pins)
#define SERVO_IN_PORT       gpioPortC
#define SERVO_IN_PIN        1

#define SERVO_OUT_PORT      gpioPortC
#define SERVO_OUT_PIN       3

// Servo positions (pulse width in microseconds)
#define SERVO_OPEN_ANGLE    0      // 0 degrees (barrier up - open)
#define SERVO_CLOSED_ANGLE  90     // 90 degrees (barrier down - closed)

#define SERVO_MIN_PULSE_US  500    // 0.5ms = 0 degrees
#define SERVO_MID_PULSE_US  1500   // 1.5ms = 90 degrees
#define SERVO_MAX_PULSE_US  2500   // 2.5ms = 180 degrees
#define SERVO_PERIOD_US     20000  // 20ms = 50Hz

// Servo state
typedef enum {
    SERVO_STATE_CLOSED = 0,
    SERVO_STATE_OPEN = 1
} servo_state_t;

typedef struct {
    servo_state_t barrier_in_state;
    servo_state_t barrier_out_state;
} servo_status_t;

extern servo_status_t servo_status;

/**
 * @brief Initialize servo motors (configure PWM)
 */
void servo_init(void);

/**
 * @brief Set servo angle (0-180 degrees)
 * @param port GPIO port
 * @param pin GPIO pin
 * @param angle Angle in degrees (0-180)
 */
void servo_set_angle(GPIO_Port_TypeDef port, uint8_t pin, uint8_t angle);

/**
 * @brief Open barrier_in (entrance barrier up)
 */
void servo_open_barrier_in(void);

/**
 * @brief Close barrier_in (entrance barrier down)
 */
void servo_close_barrier_in(void);

/**
 * @brief Open barrier_out (exit barrier up)
 */
void servo_open_barrier_out(void);

/**
 * @brief Close barrier_out (exit barrier down)
 */
void servo_close_barrier_out(void);

/**
 * @brief Get barrier states
 */
servo_status_t servo_get_status(void);

#endif // SERVO_H
