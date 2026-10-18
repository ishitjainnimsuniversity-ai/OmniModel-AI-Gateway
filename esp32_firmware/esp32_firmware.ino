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

// ESP32-C5 Hardware SPI Pins for MSP2402 2.4" Display
#define TFT_SCK  10
#define TFT_MISO 9
#define TFT_MOSI 8
#define TFT_CS   6
#define TFT_DC   7
#define TFT_RST  2
#define TFT_BL   27
#define TOUCH_CS 3

// Gateway Endpoints (Primary Local Subnet 10.22.163.78 & Cloud Fallback)
const char* PRIMARY_GATEWAY_URL = "http://10.22.163.78:8000/api/iot/chat";
const char* FALLBACK_GATEWAY_URL = "http://10.22.163.200:8000/api/iot/chat";
const char* CLOUD_GATEWAY_URL   = "https://OmniModel-AI-Gateway.vercel.app/api/iot/chat";

Adafruit_ILI9341 tft = Adafruit_ILI9341(TFT_CS, TFT_DC, TFT_RST);
bool screenReady = false;

// -----------------------------------------------------------------------------
// Native Circuit Board Background Drawing Engine for 2.4" LCD
// -----------------------------------------------------------------------------
void drawCircuitBoardBackground() {
    if (!screenReady) return;
    
    // Draw subtle golden copper circuit traces across background
    tft.drawFastHLine(20, 60, 280, 0x5285);
    tft.drawFastHLine(20, 62, 140, 0x9460);
    tft.drawLine(160, 62, 190, 92, 0x9460);
    tft.drawFastHLine(190, 92, 110, 0x9460);
    
    tft.drawFastHLine(20, 200, 280, 0x5285);
    tft.drawFastHLine(50, 204, 180, 0x9460);
    tft.drawLine(230, 204, 250, 184, 0x9460);
    tft.drawFastHLine(250, 184, 50, 0x9460);

    // Vertical bus traces with circuit solder vias
    tft.drawFastVLine(40, 60, 140, 0x3186);
    tft.fillCircle(40, 60, 2, 0xFD20);
    tft.fillCircle(40, 200, 2, 0xFD20);

    tft.drawFastVLine(280, 60, 140, 0x3186);
    tft.fillCircle(280, 60, 2, 0xFD20);
    tft.fillCircle(280, 200, 2, 0xFD20);

    // Central Processor Die Outline (Watermark on PCB)
    tft.drawRect(95, 85, 130, 90, 0x21A7);
    tft.drawRect(97, 87, 126, 86, 0x10A2);
    
    // Processor Golden Pins
    for (int p = 105; p < 215; p += 8) {
        tft.drawFastVLine(p, 80, 5, 0xFD20);   // Top pins
        tft.drawFastVLine(p, 175, 5, 0xFD20);  // Bottom pins
    }
    for (int p = 93; p < 170; p += 8) {
        tft.drawFastHLine(90, p, 5, 0xFD20);   // Left pins
        tft.drawFastHLine(225, p, 5, 0xFD20);  // Right pins
    }
}

// -----------------------------------------------------------------------------
// UI Screen Drawing Functions
// -----------------------------------------------------------------------------
void drawHeader(const char* title) {
    if (!screenReady) return;
    tft.fillScreen(ILI9341_BLACK);
    
    // Draw native circuit board watermark across background
    drawCircuitBoardBackground();

    // Top Cyber HUD Bar (Deep Cyber Blue)
    tft.fillRect(0, 0, 320, 28, 0x0113);
    tft.drawFastHLine(0, 27, 320, ILI9341_CYAN);
    tft.drawFastHLine(0, 28, 320, 0x0210);

    tft.setTextColor(ILI9341_CYAN);
    tft.setTextSize(2);
    tft.setCursor(8, 6);
    tft.print(title);

    // Mini Wi-Fi 6 Signal Meter (4 Bars)
    tft.fillRect(296, 18, 2, 4, ILI9341_CYAN);
    tft.fillRect(300, 15, 2, 7, ILI9341_CYAN);
    tft.fillRect(304, 12, 2, 10, ILI9341_CYAN);
    tft.fillRect(308, 9, 2, 13, ILI9341_CYAN);

    // Sub-header Telemetry Strip
    tft.fillRect(0, 29, 320, 11, 0x0110);
    tft.drawFastHLine(0, 40, 320, 0x18C3);
    tft.setTextColor(0x07E0); // Emerald Green
    tft.setTextSize(1);
    tft.setCursor(8, 31);
    tft.print("OMNIMODEL 5.2 | SPEED ROUTER | 240MHz RISC-V");

    // Cyber Corner HUD Reticles
    tft.drawFastHLine(3, 44, 6, ILI9341_CYAN);
    tft.drawFastVLine(3, 44, 6, ILI9341_CYAN);
    tft.drawFastHLine(311, 44, 6, ILI9341_CYAN);
    tft.drawFastVLine(316, 44, 6, ILI9341_CYAN);
    tft.drawFastHLine(3, 218, 6, ILI9341_CYAN);
    tft.drawFastVLine(3, 212, 6, ILI9341_CYAN);
    tft.drawFastHLine(311, 218, 6, ILI9341_CYAN);
    tft.drawFastVLine(316, 212, 6, ILI9341_CYAN);

    // Bottom Status Bar
    tft.fillRect(0, 222, 320, 18, 0x08A2);
    tft.drawFastHLine(0, 221, 320, 0x2124);
    tft.setTextColor(ILI9341_LIGHTGREY);
    tft.setTextSize(1);
    tft.setCursor(8, 227);
    if (WiFi.status() == WL_CONNECTED) {
        tft.printf("WiFi: %s (%s) | RSSI: %d dBm", WIFI_SSID, WiFi.localIP().toString().c_str(), WiFi.RSSI());
    } else {
        tft.print("WiFi: Connecting to 'Lost Case '...");
    }
}

void printWordWrapped(const String& text, int lineStartX = 8, int maxX = 312) {
    if (!screenReady) return;
    int curX = tft.getCursorX();
    int curY = tft.getCursorY();
    int charWidth = 6;   // font size 1 = 6px per char
    int lineHeight = 11; // 11px vertical line height
    
    int len = text.length();
    int i = 0;
    
    while (i < len) {
        char c = text.charAt(i);
        if (c == '\r') {
            i++;
            continue;
        }
        if (c == '\n') {
            curY += lineHeight;
            curX = lineStartX;
            tft.setCursor(curX, curY);
            i++;
            continue;
        }
        
        if (c == ' ') {
            if (curX + charWidth <= maxX) {
                tft.print(' ');
                curX += charWidth;
            } else {
                curY += lineHeight;
                curX = lineStartX;
                tft.setCursor(curX, curY);
            }
            i++;
            continue;
        }
        
        // Extract entire token up to next whitespace
        int wordEnd = i;
        while (wordEnd < len && text.charAt(wordEnd) != ' ' && text.charAt(wordEnd) != '\n' && text.charAt(wordEnd) != '\r') {
            wordEnd++;
        }
        
        String word = text.substring(i, wordEnd);
        int wordWidth = word.length() * charWidth;
        
        // Wrap word to next line if it exceeds screen margin
        if (curX + wordWidth > maxX && curX > lineStartX) {
            curY += lineHeight;
            curX = lineStartX;
            tft.setCursor(curX, curY);
        }
        
        tft.print(word);
        curX = tft.getCursorX();
        i = wordEnd;
    }
}

String urlEncode(const String& str) {
    String encoded = "";
    char hex[4];
    for (size_t i = 0; i < str.length(); i++) {
        char c = str.charAt(i);
        if (isalnum(c) || c == '-' || c == '_' || c == '.' || c == '~') {
            encoded += c;
        } else {
            sprintf(hex, "%%%02X", (unsigned char)c);
            encoded += hex;
        }
    }
    return encoded;
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
        tft.setTextSize(1);
        tft.setCursor(10, 46);
        tft.print("Q: ");
        printWordWrapped(prompt, 26, 310);

        tft.drawFastHLine(8, 72, 304, 0x18C3);
        tft.setTextColor(ILI9341_ORANGE);
        tft.setCursor(10, 80);
        tft.println("[ Querying Router via Wi-Fi 6... ]");
    }

    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("[Error] Wi-Fi not connected!");
        return;
    }

    String encodedPrompt = urlEncode(prompt);

    bool success = false;
    String answer = "";

    // 1. Try Primary Local Gateway
    {
        HTTPClient http;
        String localEndpoint = String(PRIMARY_GATEWAY_URL) + "?format=text&q=" + encodedPrompt;
        Serial.print("Connecting to Primary Gateway: ");
        Serial.println(localEndpoint);

        if (http.begin(localEndpoint)) {
            http.setFollowRedirects(HTTPC_STRICT_FOLLOW_REDIRECTS);
            http.setReuse(false);
            http.setUserAgent("ESP32-C5-Hardware-Agent");
            http.addHeader("Accept", "text/plain");
            http.setTimeout(8000);

            int httpCode = http.GET();
            if (httpCode == 200) {
                answer = http.getString();
                success = true;
                Serial.printf("[Gateway Success 200 OK]\n");
            } else {
                Serial.printf("[Gateway HTTP Error]: %d\n", httpCode);
            }
            http.end();
        }
    }

    // 1b. Try Secondary Local Gateway if Primary failed
    if (!success) {
        HTTPClient http;
        String localEndpoint2 = String(FALLBACK_GATEWAY_URL) + "?format=text&q=" + encodedPrompt;
        Serial.print("Connecting to Fallback Local Gateway: ");
        Serial.println(localEndpoint2);

        if (http.begin(localEndpoint2)) {
            http.setFollowRedirects(HTTPC_STRICT_FOLLOW_REDIRECTS);
            http.setReuse(false);
            http.setUserAgent("ESP32-C5-Hardware-Agent");
            http.addHeader("Accept", "text/plain");
            http.setTimeout(6000);

            int httpCode = http.GET();
            if (httpCode == 200) {
                answer = http.getString();
                success = true;
                Serial.printf("[Fallback Local Gateway Success 200 OK]\n");
            } else {
                Serial.printf("[Fallback Local Gateway HTTP Error]: %d\n", httpCode);
            }
            http.end();
        }
    }

    // 2. Fallback to Cloud Gateway if Local returned non-200
    if (!success) {
        WiFiClientSecure secureClient;
        secureClient.setInsecure();
        secureClient.setTimeout(15000);

        HTTPClient http;
        String endpoint = String(CLOUD_GATEWAY_URL) + "?format=text&q=" + encodedPrompt;
        Serial.print("Trying Cloud Gateway Fallback: ");
        Serial.println(endpoint);

        if (http.begin(secureClient, endpoint)) {
            http.setFollowRedirects(HTTPC_STRICT_FOLLOW_REDIRECTS);
            http.setReuse(false);
            http.setUserAgent("ESP32-C5-Hardware-Agent");
            http.addHeader("Accept", "text/plain");
            http.setTimeout(15000);

            int httpCode = http.GET();
            if (httpCode == 200) {
                answer = http.getString();
                success = true;
                Serial.printf("[Cloud Gateway Success 200 OK]\n");
            } else {
                Serial.printf("[Cloud Gateway Error]: %d\n", httpCode);
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
            tft.setCursor(10, 46);
            tft.print("Q: ");
            printWordWrapped(prompt, 26, 310);

            tft.drawFastHLine(8, 72, 304, 0x18C3);
            tft.setCursor(10, 76);
            tft.setTextColor(ILI9341_YELLOW);
            tft.setTextSize(1);
            tft.println("GENESIS AI ANSWER:");
            
            tft.setTextColor(ILI9341_WHITE);
            tft.setTextSize(1);
            tft.setCursor(10, 89);
            printWordWrapped(answer, 10, 310);
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

    // Initialize LCD Backlight (Active HIGH)
    pinMode(TFT_BL, OUTPUT);
    digitalWrite(TFT_BL, HIGH);

    // Initialize Hardware SPI Bus with exact ESP32-C5 pin assignments
    SPI.begin(TFT_SCK, TFT_MISO, TFT_MOSI, TFT_CS);
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
