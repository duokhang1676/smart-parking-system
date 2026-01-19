#ifndef OLED_I2C_H
#define OLED_I2C_H

#include "sl_i2cspm_instances.h"
#include <stdint.h>
#include <stdbool.h>

// OLED I2C address (SSD1306 usually 0x3C or 0x3D)
#define OLED_I2C_ADDR       0x3C

// OLED display dimensions
#define OLED_WIDTH          128
#define OLED_HEIGHT         64
#define OLED_PAGES          8   // 64 pixels / 8 = 8 pages

// OLED commands
#define OLED_CMD_DISPLAY_OFF        0xAE
#define OLED_CMD_DISPLAY_ON         0xAF
#define OLED_CMD_SET_CONTRAST       0x81
#define OLED_CMD_NORMAL_DISPLAY     0xA6
#define OLED_CMD_INVERSE_DISPLAY    0xA7

/**
 * @brief Initialize the OLED display (SSD1306)
 * @return true if successful, false otherwise
 */
bool oled_init(void);

/**
 * @brief Clear the OLED display
 */
void oled_clear(void);

/**
 * @brief Update the OLED display with buffer content
 */
void oled_update(void);

/**
 * @brief Set cursor position
 * @param x X coordinate (0-127)
 * @param y Y coordinate (0-7 pages)
 */
void oled_set_cursor(uint8_t x, uint8_t y);

/**
 * @brief Write a character to the OLED at current cursor
 * @param c Character to write
 */
void oled_write_char(char c);

/**
 * @brief Write a string to the OLED
 * @param str Null-terminated string
 */
void oled_write_string(const char *str);

/**
 * @brief Write string at specific position
 * @param x X position (0-127)
 * @param y Y position (0-7 pages)
 * @param str String to write
 */
void oled_write_string_at(uint8_t x, uint8_t y, const char *str);

/**
 * @brief Turn OLED display on
 */
void oled_display_on(void);

/**
 * @brief Turn OLED display off
 */
void oled_display_off(void);

/**
 * @brief Set OLED contrast
 * @param contrast Contrast value (0-255)
 */
void oled_set_contrast(uint8_t contrast);

/**
 * @brief Fill entire display buffer with pattern
 * @param pattern Byte pattern to fill
 */
void oled_fill(uint8_t pattern);

#endif // OLED_I2C_H
