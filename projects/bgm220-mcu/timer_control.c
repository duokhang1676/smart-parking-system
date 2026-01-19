#include "timer_control.h"
#include "sl_sleeptimer.h"
#include "em_gpio.h"
#include "app_assert.h"

#define TRIGGER_GPIO_PORT   gpioPortA
#define TRIGGER_GPIO_PIN    0

static sl_sleeptimer_timer_handle_t timer_handle;
static volatile bool timer_done = true;

static void timer_callback(sl_sleeptimer_timer_handle_t *handle, void *data)
{
    (void)handle;
    (void)data;

    GPIO_PinOutClear(TRIGGER_GPIO_PORT, TRIGGER_GPIO_PIN); // Turn off GPIO pin after timeout
    timer_done = true;
}

void timer_control_init(void)
{
    // Config GPIO output
    GPIO_PinModeSet(TRIGGER_GPIO_PORT, TRIGGER_GPIO_PIN, gpioModePushPull, 0);
    timer_done = true;
}

sl_status_t trigger_gpio_high_nonblocking(uint32_t duration_ms)
{
    if (!timer_done) {
        return SL_STATUS_BUSY;
    }

    timer_done = false;

    GPIO_PinOutSet(TRIGGER_GPIO_PORT, TRIGGER_GPIO_PIN); // Turn on GPIO

    sl_status_t sc = sl_sleeptimer_start_timer_ms(
        &timer_handle,
        duration_ms,
        timer_callback,
        NULL,
        0,
        0
    );

    app_assert_status(sc);
    return sc;
}

bool is_trigger_done(void)
{
    return timer_done;
}
