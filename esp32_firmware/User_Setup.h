//                            USER DEFINED SETTINGS
//   Set for ESP32 + MSP2402 / QD241801 2.4-inch ILI9341 SPI (240x320) + XPT2046 Touch
//   Copy this file into: Arduino/libraries/TFT_eSPI/User_Setup.h

#define USER_SETUP_INFO "User_Setup_ESP32_MSP2402_ILI9341"

// 1. Define Driver
#define ILI9341_DRIVER

// 2. Define Display Dimensions
#define TFT_WIDTH  240
#define TFT_HEIGHT 320

// 3. Define ESP32 Hardware SPI Pins
// Standard ESP32 (WROOM-32 / NodeMCU-32S / ESP32-DevKit)
#define TFT_MISO 19
#define TFT_MOSI 23
#define TFT_SCLK 18
#define TFT_CS   15  // Chip select control pin
#define TFT_DC    2  // Data Command control pin
#define TFT_RST   4  // Reset pin (could connect to ESP32 EN/RST or GPIO4)

// Touch Controller (XPT2046) Pins on MSP2402
#define TOUCH_CS  5  // Chip select pin for Touch controller

// 4. Fonts to Load
#define LOAD_GLCD   // Standard 5x7 font
#define LOAD_FONT2  // Small 16 pixel high font
#define LOAD_FONT4  // Medium 26 pixel high font
#define LOAD_FONT6  // Large 48 pixel high font
#define LOAD_FONT7  // 7 segment 48 pixel font
#define LOAD_FONT8  // Large 75 pixel font
#define LOAD_GFXFF  // FreeFonts
#define SMOOTH_FONT

// 5. SPI Frequency Settings
#define SPI_FREQUENCY       40000000  // 40MHz for fast redraws
#define SPI_READ_FREQUENCY  20000000
#define SPI_TOUCH_FREQUENCY  2500000  // 2.5MHz for Touch controller
