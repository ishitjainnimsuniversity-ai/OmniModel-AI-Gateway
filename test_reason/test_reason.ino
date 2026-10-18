#include <Arduino.h>
#include <WiFi.h>
#include <esp_wifi.h>

// Notice the trailing space in the exact SSID: "Lost Case "
const char* ssid = "Lost Case ";
const char* password = "453441C1";

void setup() {
    Serial.begin(115200);
    delay(2000);

    Serial.println("\n==========================================");
    Serial.println("  ESP32-C5 WPA3-SAE Exact SSID Connect    ");
    Serial.println("==========================================");

    WiFi.onEvent([](WiFiEvent_t event, WiFiEventInfo_t info) {
        if (event == ARDUINO_EVENT_WIFI_STA_DISCONNECTED) {
            uint8_t reason = info.wifi_sta_disconnected.reason;
            Serial.printf("[WiFi Disconnected] Reason Code: %d (%s)\n", 
                reason, WiFi.disconnectReasonName((wifi_err_reason_t)reason));
        } else if (event == ARDUINO_EVENT_WIFI_STA_CONNECTED) {
            Serial.println("[WiFi Connected to AP!] Handshake Successful!");
        } else if (event == ARDUINO_EVENT_WIFI_STA_GOT_IP) {
            Serial.print("\n>>> [WiFi Got IP Successfully!]: ");
            Serial.println(WiFi.localIP());
            Serial.printf(">>> Gateway IP: %s\n", WiFi.gatewayIP().toString().c_str());
            Serial.printf(">>> RSSI: %d dBm\n", WiFi.RSSI());
        }
    });

    WiFi.mode(WIFI_STA);
    WiFi.setBandMode(WIFI_BAND_MODE_2G_ONLY);
    WiFi.setScanMethod(WIFI_ALL_CHANNEL_SCAN);
    WiFi.setMinSecurity(WIFI_AUTH_WPA2_PSK);

    Serial.printf("Connecting to SSID: '%s'...\n", ssid);
    WiFi.begin(ssid, password);
}

void loop() {
    static unsigned long lastCheck = 0;
    if (millis() - lastCheck > 3000) {
        lastCheck = millis();
        if (WiFi.status() == WL_CONNECTED) {
            Serial.printf("[ONLINE] IP: %s, RSSI: %d dBm\n", 
                WiFi.localIP().toString().c_str(), WiFi.RSSI());
        } else {
            Serial.printf("[CONNECTING...] Status: %d\n", WiFi.status());
        }
    }
    delay(100);
}
