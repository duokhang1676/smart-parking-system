#ifndef TIMER_CONTROL_H
#define TIMER_CONTROL_H

#include "sl_status.h"
#include <stdbool.h>

void timer_control_init(void);
sl_status_t trigger_gpio_high_nonblocking(uint32_t duration_ms);
bool is_trigger_done(void);

#endif // TIMER_CONTROL_H
