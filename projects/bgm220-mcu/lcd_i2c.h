#ifndef LCD_I2C_H
#define LCD_I2C_H

#include "sl_i2cspm_instances.h"
#include <stdint.h>

// I2C address of the LCD (commonly 0x27 or 0x3F)
#define LCD_I2C_ADDR        0x27

// I2C addresses of two PCA9548A I2C multiplexers
#define PCA9548A_ADDR_1     0x70   // First PCA9548A (A0–A2 = 000)
#define PCA9548A_ADDR_2     0x71   // Second PCA9548A (A0–A2 = 100)

/**
 * @brief Select a specific channel on a given PCA9548A I2C multiplexer.
 *
 * This must be called before accessing any device connected to that channel,
 * such as an I2C LCD display.
 *
 * @param pca_addr  I2C address of the PCA9548A (0x70 to 0x77)
 * @param channel   Channel number (0–7)
 */
void lcd_select_channel(uint8_t pca_addr, uint8_t channel);

/**
 * @brief Initialize the LCD display in 4-bit mode.
 */
void lcd_init(void);

/**
 * @brief Clear the LCD display.
 */
void lcd_clear(void);

/**
 * @brief Move the LCD cursor to the home position (0,0).
 */
void lcd_home(void);

/**
 * @brief Set the LCD cursor to a specific column and row.
 *
 * @param col  Column number (0–15)
 * @param row  Row number (0 or 1)
 */
void lcd_set_cursor(uint8_t col, uint8_t row);

/**
 * @brief Write a single character to the LCD.
 *
 * @param c Character to write
 */
void lcd_write_char(char c);

/**
 * @brief Write a null-terminated string to the LCD.
 *
 * @param str Pointer to the string
 */
void lcd_write_string(const char *str);

/**
 * @brief Turn on the LCD display (without cursor or blinking).
 */
void lcd_display_on(void);

/**
 * @brief Turn off the LCD display.
 */
void lcd_display_off(void);

#endif  // LCD_I2C_H
