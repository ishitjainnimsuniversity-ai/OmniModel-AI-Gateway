// GENESIS AI firmware configuration TEMPLATE. Copy to config.h and edit.
#pragma once
#define WIFI_SSID        "your-hotspot-name"
#define WIFI_PASSWORD    "your-hotspot-password"
#define BACKEND_HOST     "192.168.x.x"        // PC running: python -m genesis_ai
#define BACKEND_PORT     8100
#define GENESIS_TOKEN    "token-printed-by-backend"

#define WIFI_CONNECT_TIMEOUT_MS   25000
#define HTTP_CONNECT_TIMEOUT_MS   2500
#define HTTP_FEED_TIMEOUT_MS      4000
#define HTTP_DEEP_TIMEOUT_MS      15000
#define BOOT_BUTTON_PIN  28
