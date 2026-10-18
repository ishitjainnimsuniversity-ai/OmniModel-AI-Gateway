/*
 * ==============================================================================
 * GENESIS AI 5.0 - ESP32-C5 Hardware Agent & Touchscreen Engine
 * 
 * Hardware:
 *   MCU: ESP32-C5 (Wi-Fi 6 Dual-Band RISC-V 240MHz)
 *   Display: MSP2402 / QD241801 2.4-inch ILI9341 SPI (240x320) + XPT2046 Touch
 * 
 * Wi-Fi Network:
 *   SSID: "Lost Case " (WPA3-Personal, 2.4GHz)
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
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ILI9341.h>

// Wi-Fi Credentials (exact SSID with verified trailing space)
const char* WIFI_SSID     = "Lost Case ";
const char* WIFI_PASSWORD = "453441C1";

// ESP32-C5 SPI Pins for MSP2402 Display
#define TFT_CS   6
#define TFT_DC   7
#define TFT_RST  2
#define TFT_BL   27

// Gateway Endpoints (Cloud & Local PC Fallback)
const char* CLOUD_GATEWAY_URL = "https://OmniModel-AI-Gateway.vercel.app/api/iot/chat";
const char* LOCAL_GATEWAY_URL = "http://10.22.163.200:8000/api/iot/chat";

Adafruit_ILI9341 tft = Adafruit_ILI9341(TFT_CS, TFT_DC, TFT_RST);
bool screenReady = false;

// -----------------------------------------------------------------------------
// UI Screen Drawing Functions
// -----------------------------------------------------------------------------
void drawHeader(const char* title) {
    if (!screenReady) return;
    tft.fillScreen(ILI9341_BLACK);
    
    // Top Cyber HUD Bar
    tft.fillRect(0, 0, 320, 28, 0x0113);
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
        tft.printf("WiFi: %s (%s) | GENESIS AI 5.0", WIFI_SSID, WiFi.localIP().toString().c_str());
    } else {
        tft.print("WiFi: Connecting to 'Lost Case '...");
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
    Serial.print("[Question]: ");
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
        Serial.println("[Error] Wi-Fi not connected!");
        return;
    }

    String encodedPrompt = prompt;
    encodedPrompt.replace(" ", "%20");

    bool success = false;
    String answer = "";

    // 1. Try Cloud Gateway
    {
        WiFiClientSecure secureClient;
        secureClient.setInsecure(); // Skip certificate verification for embedded IoT client
        secureClient.setTimeout(15000);

        HTTPClient http;
        String endpoint = String(CLOUD_GATEWAY_URL) + "?q=" + encodedPrompt;
        Serial.print("Connecting to Cloud Gateway: ");
        Serial.println(endpoint);

        if (http.begin(secureClient, endpoint)) {
            http.setUserAgent("ESP32-C5-Hardware-Agent");
            http.addHeader("Accept", "text/plain");
            http.setTimeout(15000);

            int httpCode = http.GET();
            if (httpCode == 200) {
                answer = http.getString();
                success = true;
                Serial.printf("[Cloud Success 200 OK]\n");
            } else {
                Serial.printf("[Cloud HTTP Error]: %d\n", httpCode);
            }
            http.end();
        }
    }

    // 2. Fallback to Local Subnet Gateway if Cloud returned non-200
    if (!success) {
        HTTPClient http;
        String localEndpoint = String(LOCAL_GATEWAY_URL) + "?q=" + encodedPrompt;
        Serial.print("Trying Local Subnet Fallback: ");
        Serial.println(localEndpoint);

        if (http.begin(localEndpoint)) {
            http.setUserAgent("ESP32-C5-Hardware-Agent");
            http.addHeader("Accept", "text/plain");
            http.setTimeout(10000);

            int httpCode = http.GET();
            if (httpCode == 200) {
                answer = http.getString();
                success = true;
                Serial.printf("[Local Gateway Success 200 OK]\n");
            } else {
                Serial.printf("[Local Gateway Error]: %d\n", httpCode);
            }
            http.end();
        }
    }

    // Display Output
    if (success) {
        Serial.println("\n[GENESIS AI Answer]:");
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
        Serial.println("[Error] Both Cloud and Local Gateway queries timed out or failed.");
        if (screenReady) {
            tft.setTextColor(ILI9341_RED);
            tft.println("\nQuery Failed. Check Internet connection.");
        }
    }
}

// -----------------------------------------------------------------------------
// Setup
// -----------------------------------------------------------------------------
void setup() {
    Serial.begin(115200);
    delay(1000);

    Serial.println("\n\n==================================================");
    Serial.println("  GENESIS AI 5.0 - ESP32-C5 Hardware Client");
    Serial.println("  Target Display: MSP2402 2.4\" ILI9341 SPI (240x320)");
    Serial.println("  Wi-Fi 6 Dual-Band + RISC-V 240MHz");
    Serial.println("==================================================");

    // Initialize LCD (Safe to run even before screen is physically attached)
    tft.begin();
    tft.setRotation(1); // Landscape mode 320x240
    screenReady = true;

    drawHeader("SYSTEM BOOT");
    if (screenReady) {
        tft.setCursor(8, 45);
        tft.println("Connecting to Lost Case Wi-Fi...");
    }

    // Wi-Fi 6 / WPA3 Configuration for ESP32-C5
    WiFi.mode(WIFI_STA);
    WiFi.setBandMode(WIFI_BAND_MODE_2G_ONLY);
    WiFi.setScanMethod(WIFI_ALL_CHANNEL_SCAN);
    WiFi.setMinSecurity(WIFI_AUTH_WPA2_PSK);

    Serial.printf("Connecting to Wi-Fi: '%s'...\n", WIFI_SSID);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 40) {
        delay(500);
        Serial.print(".");
        if (screenReady) tft.print(".");
        attempts++;
    }

    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\n\n>>> Wi-Fi Connected Successfully! <<<");
        Serial.print(">>> IP Address: ");
        Serial.println(WiFi.localIP());
        Serial.printf(">>> Signal (RSSI): %d dBm\n", WiFi.RSSI());

        drawHeader("GENESIS AI ONLINE");
        if (screenReady) {
            tft.setTextColor(ILI9341_GREEN);
            tft.setCursor(8, 45);
            tft.println("Status: Connected to Lost Case!");
            tft.setTextColor(ILI9341_WHITE);
            tft.printf("IP: %s\n\n", WiFi.localIP().toString().c_str());
            tft.println("Type your question into Serial Monitor!");
        }

        // Test boot query
        askGenesisAI("What is quantum computing in 20 words");
    } else {
        Serial.println("\nWi-Fi connection timed out!");
        if (screenReady) {
            tft.setTextColor(ILI9341_RED);
            tft.println("\nWi-Fi Connection Failed.");
        }
    }

    Serial.println("\nReady! Enter any question in Serial Monitor and press Enter:");
}

// -----------------------------------------------------------------------------
// Main Loop
// -----------------------------------------------------------------------------
void loop() {
    // Read question from Serial Monitor
    if (Serial.available()) {
        String input = Serial.readStringUntil('\n');
        input.trim();
        if (input.length() > 0) {
            askGenesisAI(input);
        }
    }
    delay(50);
}
