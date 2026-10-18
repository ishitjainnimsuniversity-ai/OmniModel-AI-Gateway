#include <Arduino.h>
#include <WiFi.h>

void setup() {
    Serial.begin(115200);
    delay(1000);

    Serial.println("\n\n====================================");
    Serial.println("  GENESIS AI 5.0 - ESP32-C5 HOTSPOT  ");
    Serial.println("====================================");

    // Force 2.4GHz Channel 1 so all phones and PCs see it immediately
    WiFi.mode(WIFI_AP);
    bool ok = WiFi.softAP("GENESIS-AI-HOTSPOT", NULL, 1, 0, 4);
    if (ok) {
        Serial.println("✅ Hotspot ACTIVE: GENESIS-AI-HOTSPOT (2.4GHz Ch 1)");
        Serial.print("📍 IP: ");
        Serial.println(WiFi.softAPIP());
    } else {
        Serial.println("❌ Failed softAP");
    }
}

void loop() {
    delay(1000);
    Serial.print(".");
}
