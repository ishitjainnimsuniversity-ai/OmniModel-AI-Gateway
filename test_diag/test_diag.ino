#include <Arduino.h>
#include <WiFi.h>

void setup() {
    Serial.begin(115200);
    delay(1000);

    Serial.println("\n\nScanning Wi-Fi networks from ESP32-C5...");
    WiFi.mode(WIFI_STA);
    WiFi.disconnect();
    delay(500);

    int n = WiFi.scanNetworks();
    Serial.printf("Found %d networks:\n", n);
    for (int i = 0; i < n; ++i) {
        Serial.printf("%2d: %-20s | RSSI: %3d | Ch: %2d | Auth: %d\n",
                      i + 1,
                      WiFi.SSID(i).c_str(),
                      WiFi.RSSI(i),
                      WiFi.channel(i),
                      WiFi.encryptionType(i));
    }

    Serial.println("\nAttempting connection to 'Lost Case' with WPA3 support...");
    // Core 3.x WPA3 setting
    WiFi.setMinSecurity(WIFI_AUTH_OPEN); // Allow any authentication including WPA2/WPA3
    WiFi.begin("Lost Case", "453441C1");

    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 25) {
        delay(500);
        Serial.printf(".[%d]", WiFi.status());
        attempts++;
    }

    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\n>>> SUCCESS! Connected to Lost Case! <<<");
        Serial.print("IP: ");
        Serial.println(WiFi.localIP());
    } else {
        Serial.printf("\n>>> FAILED! Status: %d <<<\n", WiFi.status());
    }
}

void loop() {}
