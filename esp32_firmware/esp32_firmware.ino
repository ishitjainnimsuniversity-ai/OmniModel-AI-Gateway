/*
 * ==============================================================================
 * GENESIS AI 5.0 - ESP32 Hardware Assistant
 * Target Display: MSP2402 / QD241801 2.4-inch ILI9341 SPI (240x320) + XPT2046 Touch
 * Target MCU: ESP32 / ESP32-C3 / ESP32-S3 / ESP32-C6
 * 
 * Works WITH or WITHOUT the screen attached!
 * You can test it right now via USB Serial Monitor (115200 baud).
 * ==============================================================================
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <SPI.h>
#include <TFT_eSPI.h>

// -----------------------------------------------------------------------------
// 1. WiFi & Gateway Configuration
// -----------------------------------------------------------------------------
// Enter your 2.4GHz WiFi credentials:
const char* WIFI_SSID     = "YOUR_WIFI_NAME";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// Enter your OmniModel Gateway URL:
// Option A: Local PC IP (e.g. "http://192.168.1.100:8000/api/iot/chat")
// Option B: Live Vercel URL (e.g. "https://omni-model-ai-gateway.vercel.app/api/iot/chat")
const char* GATEWAY_IOT_URL = "https://omni-model-ai-gateway.vercel.app/api/iot/chat";

// -----------------------------------------------------------------------------
// 2. Hardware Display Objects
// -----------------------------------------------------------------------------
TFT_eSPI tft = TFT_eSPI();
bool screenReady = false;

// -----------------------------------------------------------------------------
// 3. UI Drawing Helper Functions
// -----------------------------------------------------------------------------
void drawHeader(const char* title) {
    if (!screenReady) return;
    tft.fillScreen(TFT_BLACK);
    // Top banner
    tft.fillRect(0, 0, 320, 30, 0x0113); // Deep cyan/blue
    tft.setTextColor(0x07FF, 0x0113);    // Bright cyan
    tft.setTextSize(2);
    tft.setCursor(12, 7);
    tft.print(title);
    tft.drawFastHLine(0, 30, 320, 0x07FF);

    // Bottom status bar
    tft.fillRect(0, 220, 320, 20, 0x10A2);
    tft.setTextColor(TFT_LIGHTGREY, 0x10A2);
    tft.setTextSize(1);
    tft.setCursor(10, 226);
    tft.print("WiFi: Connected  |  GENESIS AI 5.0");

    tft.setCursor(10, 42);
    tft.setTextColor(TFT_WHITE, TFT_BLACK);
    tft.setTextSize(1);
}

// -----------------------------------------------------------------------------
// 4. Query GENESIS AI Gateway
// -----------------------------------------------------------------------------
void askGenesisAI(String prompt) {
    Serial.println("\n--------------------------------------------------");
    Serial.print("🤖 [User Question]: ");
    Serial.println(prompt);

    if (screenReady) {
        drawHeader("GENESIS AI 5.0");
        tft.setTextColor(0x07E0, TFT_BLACK); // Bright Green
        tft.setTextSize(2);
        tft.setCursor(10, 40);
        tft.print("Q: ");
        tft.setTextSize(1);
        tft.println(prompt);

        tft.setTextColor(0xFD20, TFT_BLACK); // Orange thinking status
        tft.setCursor(10, 75);
        tft.println("\nThinking... (Querying Gateway)");
    }

    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("❌ [Error] WiFi disconnected. Reconnecting...");
        WiFi.reconnect();
        return;
    }

    HTTPClient http;
    // Request lightweight IoT plain response
    String endpoint = String(GATEWAY_IOT_URL) + "?q=" + prompt;
    // Replace spaces with +
    endpoint.replace(" ", "+");

    Serial.print("📡 Contacting Gateway: ");
    Serial.println(endpoint);

    http.begin(endpoint);
    http.setUserAgent("ESP32-MSP2402-Client");
    http.addHeader("Accept", "text/plain");
    http.setTimeout(12000); // 12 second timeout

    int httpCode = http.GET();

    if (httpCode == 200) {
        String answer = http.getString();
        Serial.println("\n✨ [GENESIS AI Answer]:");
        Serial.println(answer);
        Serial.println("--------------------------------------------------");

        if (screenReady) {
            drawHeader("GENESIS AI 5.0");
            tft.setTextColor(0x07E0, TFT_BLACK); // Green
            tft.setTextSize(1);
            tft.printf("Q: %s\n\n", prompt.c_str());

            tft.setTextColor(TFT_WHITE, TFT_BLACK);
            tft.setTextSize(2);
            tft.println("Answer:");
            tft.setTextSize(1);
            tft.setTextColor(0xCE79, TFT_BLACK); // Soft cyan/white
            tft.println(answer);
        }
    } else {
        Serial.printf("❌ [HTTP Error Code]: %d\n", httpCode);
        if (screenReady) {
            tft.setTextColor(TFT_RED, TFT_BLACK);
            tft.printf("\nGateway Error HTTP: %d\nCheck internet or API key.", httpCode);
        }
    }
    http.end();
}

// -----------------------------------------------------------------------------
// 5. Setup & Initialization
// -----------------------------------------------------------------------------
void setup() {
    Serial.begin(115200);
    delay(1000);

    Serial.println("\n==================================================");
    Serial.println("🚀 GENESIS AI 5.0 - ESP32 Hardware Client Starting");
    Serial.println("Target: MSP2402 2.4\" ILI9341 SPI (240x320)");
    Serial.println("==================================================");

    // Initialize LCD (Safe to run even if screen is not yet plugged in)
    tft.init();
    tft.setRotation(1); // Landscape mode: 320x240
    screenReady = true;

    drawHeader("SYSTEM BOOTING");
    if (screenReady) {
        tft.setCursor(10, 50);
        tft.println("Connecting to WiFi network...");
    }

    // Connect to WiFi
    Serial.print("Connecting to WiFi: ");
    Serial.println(WIFI_SSID);
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 25) {
        delay(500);
        Serial.print(".");
        if (screenReady) tft.print(".");
        attempts++;
    }

    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\n✅ WiFi Connected!");
        Serial.print("📍 ESP32 IP Address: ");
        Serial.println(WiFi.localIP());

        if (screenReady) {
            drawHeader("GENESIS AI READY");
            tft.setTextColor(0x07E0, TFT_BLACK);
            tft.setCursor(10, 50);
            tft.println("Status: Online & Connected");
            tft.setTextColor(TFT_WHITE, TFT_BLACK);
            tft.printf("IP: %s\n\n", WiFi.localIP().toString().c_str());
            tft.println("Type your question into Arduino Serial Monitor!");
        }

        // Test Query right away!
        askGenesisAI("Explain quantum computing in 20 words");
    } else {
        Serial.println("\n❌ WiFi connection failed. Please check SSID & Password.");
        if (screenReady) {
            tft.setTextColor(TFT_RED, TFT_BLACK);
            tft.println("\nWiFi Failed. Check SSID / Password in code.");
        }
    }

    Serial.println("\n💬 Enter any question in the Serial Monitor and press Enter:");
}

// -----------------------------------------------------------------------------
// 6. Main Loop (Listens to Serial Monitor & Touch)
// -----------------------------------------------------------------------------
void loop() {
    // Allows sending questions via Serial Monitor right from your PC!
    if (Serial.available()) {
        String input = Serial.readStringUntil('\n');
        input.trim();
        if (input.length() > 0) {
            askGenesisAI(input);
        }
    }
    delay(50);
}
