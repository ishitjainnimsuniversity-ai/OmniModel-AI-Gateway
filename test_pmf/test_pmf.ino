#include <Arduino.h>
#include <WiFi.h>
#include "esp_wifi.h"

void testPassword(const char* pass, bool pmf_req) {
    Serial.printf("\n--- Testing Password: '%s' (PMF Required: %d) ---\n", pass, pmf_req);
    WiFi.disconnect(true);
    delay(500);

    WiFi.mode(WIFI_STA);

    wifi_config_t conf;
    memset(&conf, 0, sizeof(conf));
    strcpy((char*)conf.sta.ssid, "Lost Case");
    strcpy((char*)conf.sta.password, pass);
    conf.sta.pmf_cfg.capable = true;
    conf.sta.pmf_cfg.required = pmf_req;

    esp_wifi_set_mode(WIFI_MODE_STA);
    esp_wifi_set_config(WIFI_IF_STA, &conf);
    esp_wifi_start();
    esp_wifi_connect();

    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 20) {
        delay(500);
        Serial.printf(".[%d]", WiFi.status());
        attempts++;
    }

    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\n>>> SUCCESS! Connected to Lost Case! <<<");
        Serial.print("IP: ");
        Serial.println(WiFi.localIP());
    } else {
        Serial.printf("\n>>> FAILED (status %d) <<<\n", WiFi.status());
    }
}

void setup() {
    Serial.begin(115200);
    delay(1000);

    Serial.println("\n\nTesting WPA2/WPA3 Mixed Mode Handshake on ESP32-C5...");
    
    // Test 1: Given password with PMF capable
    testPassword("453441C1", false);
    
    // Test 2: Lowercase variant
    if (WiFi.status() != WL_CONNECTED) {
        testPassword("453441c1", false);
    }
}

void loop() {}
