#include <lcd_i2c.h>
#include "sl_i2cspm.h"
#include "sl_sleeptimer.h"
#include <string.h>

// LCD control bits
#define LCD_BACKLIGHT   0x08  // Backlight control bit
#define LCD_ENABLE      0x04  // Enable bit
#define LCD_RW          0x00  // Read/Write bit (always write)
#define LCD_RS          0x01  // Register select bit (0 = command, 1 = data)

extern sl_i2cspm_t *sl_i2cspm_mikroe;

// Delay helper function (in milliseconds)
static void delay_ms(uint16_t ms)
{
    sl_sleeptimer_delay_millisecond(ms);
}

// ======================== PCA9548A ========================
/**
 * @brief Select a channel (0–7) on a specific PCA9548A multiplexer
 *
 * @param pca_addr I2C address of the PCA9548A (e.g. 0x70, 0x71)
 * @param channel  Channel number (0–7)
 */
void lcd_select_channel(uint8_t pca_addr, uint8_t channel)
{
    if (channel > 7) return;

    uint8_t data = 1 << channel;

    I2C_TransferSeq_TypeDef seq;
    seq.addr = pca_addr << 1;  // Correct I2C 8-bit address (shifted)
    seq.flags = I2C_FLAG_WRITE;
    seq.buf[0].data = &data;
    seq.buf[0].len = 1;
    seq.buf[1].len = 0;

    I2CSPM_Transfer(sl_i2cspm_mikroe, &seq);
}
// ==========================================================


/**
 * @brief Write one byte over I2C to the LCD module
 */
static void lcd_write_i2c(uint8_t data)
{
    I2C_TransferSeq_TypeDef seq;
    I2C_TransferReturn_TypeDef result;
    uint8_t tx_buf[1] = { data };

    seq.addr = LCD_I2C_ADDR << 1;
    seq.flags = I2C_FLAG_WRITE;
    seq.buf[0].data = tx_buf;
    seq.buf[0].len = 1;
    seq.buf[1].len = 0;

    result = I2CSPM_Transfer(sl_i2cspm_mikroe, &seq);
    if (result != i2cTransferDone) {
        // Optional: Handle transmission error here
    }
}

/**
 * @brief Pulse the LCD's enable line to latch data
 */
static void lcd_pulse_enable(uint8_t data)
{
    lcd_write_i2c(data | LCD_ENABLE);
    delay_ms(1);
    lcd_write_i2c(data & ~LCD_ENABLE);
    delay_ms(1);
}

/**
 * @brief Send one 4-bit nibble to the LCD
 */
static void lcd_send_nibble(uint8_t nibble, uint8_t mode)
{
    uint8_t data = nibble | LCD_BACKLIGHT | mode;
    lcd_pulse_enable(data);
}

/**
 * @brief Send a full 8-bit byte (split into 2 nibbles) to the LCD
 */
static void lcd_send_byte(uint8_t data, uint8_t mode)
{
    lcd_send_nibble(data & 0xF0, mode);            // high nibble
    lcd_send_nibble((data << 4) & 0xF0, mode);     // low nibble
}

/**
 * @brief Send a command byte to the LCD
 */
static void lcd_send_cmd(uint8_t cmd)
{
    lcd_send_byte(cmd, 0); // RS = 0
}

/**
 * @brief Send a data byte (character) to the LCD
 */
static void lcd_send_data(uint8_t data)
{
    lcd_send_byte(data, LCD_RS); // RS = 1
}

/**
 * @brief Initialize the LCD display in 4-bit mode
 */
void lcd_init(void)
{
    delay_ms(50);

    // Initialization sequence for 4-bit mode
    lcd_send_nibble(0x30, 0); delay_ms(5);
    lcd_send_nibble(0x30, 0); delay_ms(5);
    lcd_send_nibble(0x30, 0); delay_ms(5);
    lcd_send_nibble(0x20, 0); delay_ms(5); // Set 4-bit mode

    lcd_send_cmd(0x28); // Function set: 2 lines, 5x8 font
    lcd_send_cmd(0x08); // Display OFF
    lcd_send_cmd(0x01); // Clear display
    delay_ms(2);
    lcd_send_cmd(0x06); // Entry mode set
    lcd_send_cmd(0x0C); // Display ON, cursor OFF, blink OFF
}

/**
 * @brief Clear the LCD screen
 */
void lcd_clear(void)
{
    lcd_send_cmd(0x01);
    delay_ms(2);
}

/**
 * @brief Move the cursor to the home position
 */
void lcd_home(void)
{
    lcd_send_cmd(0x02);
    delay_ms(2);
}

/**
 * @brief Turn on the LCD display
 */
void lcd_display_on(void)
{
    lcd_send_cmd(0x0C);
}

/**
 * @brief Turn off the LCD display
 */
void lcd_display_off(void)
{
    lcd_send_cmd(0x08);
}

/**
 * @brief Set the LCD cursor to a specific column and row
 *
 * @param col Column number (0–15)
 * @param row Row number (0 or 1)
 */
void lcd_set_cursor(uint8_t col, uint8_t row)
{
    const uint8_t row_offsets[] = {0x00, 0x40, 0x14, 0x54};
    if (row > 1) row = 1;
    lcd_send_cmd(0x80 | (col + row_offsets[row]));
}

/**
 * @brief Write a single character to the LCD
 */
void lcd_write_char(char c)
{
    lcd_send_data(c);
}

/**
 * @brief Write a null-terminated string to the LCD
 */
void lcd_write_string(const char *str)
{
    while (*str) {
        lcd_write_char(*str++);
    }
}
