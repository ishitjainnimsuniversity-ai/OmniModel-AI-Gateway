// GENESIS AI — Single-Phone Portable Firmware Configuration.
// Standalone SoftAP architecture: zero PC/server runtime dependency.
#pragma once
#include <Arduino.h>
#include <IPAddress.h>

// Wi-Fi SoftAP Configuration
#define SOFTAP_SSID           "GENESIS_AI"
#define SOFTAP_PASSWORD       NULL             // Open network (NULL for open SoftAP)
#define SOFTAP_CHANNEL        1
#define SOFTAP_MAX_CONN       4

// Static Network Configuration
const IPAddress SOFTAP_IP(192, 168, 4, 1);
const IPAddress SOFTAP_GW(192, 168, 4, 1);
const IPAddress SOFTAP_NETMASK(255, 255, 255, 0);

// Wi-Fi Station (Mobile Hotspot) Configuration
#define HOTSPOT_SSID_1        "Lost Case "     // Primary exact SSID with trailing space
#define HOTSPOT_SSID_2        "Lost Case"      // Fallback exact SSID without trailing space
#define HOTSPOT_PASS          "453441C1"

// Hardware Pins (Preserved verified wiring from ILI9341 display configuration)
#define TFT_SCK               10
#define TFT_MOSI              8
#define TFT_CS                6
#define TFT_DC                7
#define TFT_RST               2

// User input button (Built-in BOOT button on ESP32-C5)
#define BOOT_BUTTON_PIN       28

// GENESIS PHOTON Continuous Gaming Light Configuration (Onboard WS2812B RGB LED)
#define RGB_LED_PIN           27               // Strictly GPIO 27 (Built-in addressable RGB LED)
#define RGB_DEFAULT_BRIGHTNESS 40              // Initial 40% glare/power-optimized brightness

// Power Optimization (OTG brownout protection: 15dBm caps peak TX current < 150mA)
#define WIFI_TX_POWER_LEVEL   WIFI_POWER_15dBm
