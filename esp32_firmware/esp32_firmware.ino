/*
 * ==============================================================================
 * GENESIS AI 5.0 - ESP32-C5 Hardware Agent & Touchscreen Engine
 * 
 * Hardware:
 *   MCU: ESP32-C5 (Wi-Fi 6 Dual-Band RISC-V 240MHz)
 *   Display: MSP2402 / QD241801 2.4-inch ILI9341 SPI (240x320) + XPT2046 Touch
 * 
 * Pinout Configuration for ESP32-C5:
 *   TFT_CS   -> GPIO 6
 *   TFT_DC   -> GPIO 7
 *   TFT_RST  -> GPIO 2
 *   TFT_MOSI -> GPIO 8 (Hardware SPI MOSI)
 *   TFT_MISO -> GPIO 9 (Hardware SPI MISO)
 *   TFT_SCK  -> GPIO 10 (Hardware SPI SCK)
 *   TFT_BL   -> 3.3V (or GPIO 27)
 *   TOUCH_CS -> GPIO 3
 * ==============================================================================
 */

#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ILI9341.h>
#include <WiFiManager.h>

// ESP32-C5 SPI Pins for MSP2402
#define TFT_CS   6
#define TFT_DC   7
#define TFT_RST  2
#define TFT_BL   27

// Gateway API Endpoint
const char* GATEWAY_IOT_URL = "https://OmniModel-AI-Gateway.vercel.app/api/iot/chat";

Adafruit_ILI9341 tft = Adafruit_ILI9341(TFT_CS, TFT_DC, TFT_RST);
bool screenReady = false;

// -----------------------------------------------------------------------------
// UI Screen Drawing Functions
// -----------------------------------------------------------------------------
void drawHeader(const char* title) {
    if (!screenReady) return;
    tft.fillScreen(ILI9341_BLACK);
    
    // Top HUD Bar
    tft.fillRect(0, 0, 320, 28, 0x0113); // Deep cyber blue
    tft.drawFastHLine(0, 28, 320, ILI9341_CYAN);
    tft.setTextColor(ILI9341_CYAN);
    tft.setTextSize(2);
    tft.setCursor(8, 6);
    tft.print(title);

    // Bottom Status Bar
    tft.fillRect(0, 222, 320, 18, 0x10A2);
    tft.drawFastHLine(0, 221, 320, 0x2124);
    tft.setTextColor(ILI9341_LIGHTGREY);
    tft.setTextSize(1);
    tft.setCursor(8, 227);
    if (WiFi.status() == WL_CONNECTED) {
        tft.printf("WiFi: %s | GENESIS AI 5.0", WiFi.localIP().toString().c_str());
    } else {
        tft.print("Hotspot: GENESIS-AI-HOTSPOT (192.168.4.1)");
    }

    tft.setCursor(8, 36);
    tft.setTextColor(ILI9341_WHITE);
    tft.setTextSize(1);
}

// -----------------------------------------------------------------------------
// Query Gateway API
// -----------------------------------------------------------------------------
void askGenesisAI(String prompt) {
    Serial.println("\n==================================================");
    Serial.print("🤖 [Question]: ");
    Serial.println(prompt);

    if (screenReady) {
        drawHeader("GENESIS AI 5.0");
        tft.setTextColor(ILI9341_GREEN);
        tft.setTextSize(2);
        tft.print("Q: ");
        tft.setTextSize(1);
        tft.println(prompt);

        tft.setTextColor(ILI9341_ORANGE);
        tft.setCursor(8, 70);
        tft.println("\nThinking... (Querying Gateway via Wi-Fi 6)");
    }

    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("❌ WiFi not connected!");
        return;
    }

    HTTPClient http;
    String endpoint = String(GATEWAY_IOT_URL) + "?q=" + prompt;
    endpoint.replace(" ", "+");

    Serial.print("📡 Contacting Gateway: ");
    Serial.println(endpoint);

    http.begin(endpoint);
    http.setUserAgent("ESP32-C5-Hardware-Agent");
    http.addHeader("Accept", "text/plain");
    http.setTimeout(15000);

    int httpCode = http.GET();

    if (httpCode == 200) {
        String answer = http.getString();
        Serial.println("\n✨ [GENESIS AI Answer]:");
        Serial.println(answer);
        Serial.println("==================================================");

        if (screenReady) {
            drawHeader("GENESIS AI 5.0");
            tft.setTextColor(ILI9341_GREEN);
            tft.setTextSize(1);
            tft.printf("Q: %s\n\n", prompt.c_str());

            tft.setTextColor(ILI9341_YELLOW);
            tft.setTextSize(2);
            tft.println("Answer:");
            tft.setTextSize(1);
            tft.setTextColor(ILI9341_WHITE);
            tft.println(answer);
        }
    } else {
        Serial.printf("❌ [HTTP Error]: %d\n", httpCode);
        if (screenReady) {
            tft.setTextColor(ILI9341_RED);
            tft.printf("\nHTTP Error: %d\nCheck internet or API key.", httpCode);
        }
    }
    http.end();
}

// -----------------------------------------------------------------------------
// Setup
// -----------------------------------------------------------------------------
void setup() {
    Serial.begin(115200);
    delay(1000);

    Serial.println("\n==================================================");
    Serial.println("🚀 GENESIS AI 5.0 - ESP32-C5 Hardware Client");
    Serial.println("Target: MSP2402 2.4\" ILI9341 SPI (240x320)");
    Serial.println("Wi-Fi 6 Dual-Band + RISC-V 240MHz");
    Serial.println("==================================================");

    // Initialize LCD
    tft.begin();
    tft.setRotation(1); // Landscape 320x240
    screenReady = true;

    drawHeader("SYSTEM BOOT");
    tft.setCursor(8, 45);
    tft.println("Initializing Wi-Fi 6 Stack...");

    // Wi-Fi Configuration Portal
    WiFiManager wm;
    wm.setConfigPortalTimeout(180); // 3 minutes timeout

    Serial.println("📡 Connecting to saved Wi-Fi...");
    tft.println("Starting Wi-Fi / Auto-Portal...");

    bool res = wm.autoConnect("GENESIS-AI-HOTSPOT");

    if (!res) {
        Serial.println("❌ Failed to connect or portal timed out.");
        drawHeader("WI-FI SETUP NEEDED");
        tft.setTextColor(ILI9341_ORANGE);
        tft.setCursor(8, 45);
        tft.println("Wi-Fi Setup Hotspot Active:");
        tft.setTextColor(ILI9341_CYAN);
        tft.setTextSize(2);
        tft.println("SSID: GENESIS-AI-HOTSPOT");
        tft.setTextSize(1);
        tft.setTextColor(ILI9341_WHITE);
        tft.println("\nConnect your phone to 'GENESIS-AI-HOTSPOT'");
        tft.println("Open browser to: http://192.168.4.1");
    } else {
        Serial.println("✅ Wi-Fi Connected Successfully!");
        Serial.print("📍 IP: ");
        Serial.println(WiFi.localIP());

        drawHeader("GENESIS AI READY");
        tft.setTextColor(ILI9341_GREEN);
        tft.setCursor(8, 45);
        tft.println("Wi-Fi Status: Connected!");
        tft.setTextColor(ILI9341_WHITE);
        tft.printf("IP: %s\n\n", WiFi.localIP().toString().c_str());
        tft.println("Type your question in Arduino Serial Monitor!");

        // Boot test query
        askGenesisAI("What is the core principle of quantum physics in 20 words");
    }

    Serial.println("\n💬 Enter any question in the Serial Monitor and press Enter:");
}

// -----------------------------------------------------------------------------
// Loop
// -----------------------------------------------------------------------------
void loop() {
    if (Serial.available()) {
        String input = Serial.readStringUntil('\n');
        input.trim();
        if (input.length() > 0) {
            askGenesisAI(input);
        }
    }
    delay(50);
}
