// GENESIS AI firmware configuration. Contains ONLY local network settings.
// Cloud AI API keys are NEVER stored on the device - they live in the backend .env.
// Copy of config.example.h with real values. Do not publish this file.
#pragma once

// Phone hotspot (the ESP32-C5 joins it as a Wi-Fi STATION; DHCP + DHCP-provided DNS are used).
// NOTE: the SSID really ends with a trailing space.
#define WIFI_SSID        "Lost Case "
#define WIFI_PASSWORD    "453441C1"

// GENESIS AI backend (runs on the PC that is connected to the same hotspot).
#define BACKEND_HOST     "10.33.110.35"
#define BACKEND_PORT     8100
// LAN access token printed by the backend at start-up (GENESIS_ACCESS_TOKEN in backend .env).
#define GENESIS_TOKEN    "0SSGFo9wDHE4IlRxcHAC0kj3"

// Timeouts (ms)
#define WIFI_CONNECT_TIMEOUT_MS   25000
#define HTTP_CONNECT_TIMEOUT_MS   2500
#define HTTP_FEED_TIMEOUT_MS      4000
#define HTTP_DEEP_TIMEOUT_MS      15000

// Built-in BOOT button (existing hardware). Short press = next page, long press = new chat.
#define BOOT_BUTTON_PIN  28
