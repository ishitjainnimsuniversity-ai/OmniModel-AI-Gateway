/*
 * ==============================================================================
 * GENESIS GPT-4o OMNI - SOVEREIGN AI & ON-SCREEN TOUCH KEYBOARD FIRMWARE
 * ==============================================================================
 * Hardware Target:
 *   MCU     : ESP32-C5-DevKit V2.0 (Dual-Band Wi-Fi 6, RISC-V 240MHz, SRAM)
 *   Display : 2.4-inch SPI TFT (320x240 Full-Screen Landscape Calibrated)
 *   Touch   : On-Screen 34-Key QWERTY Keyboard + Single-Wire Capacitive/GND Tap
 *             (GPIO 25 / GPIO 4 / T_CLK) + Built-in BOOT Button (GPIO 28)
 *             + Live Synced Mobile/PC Touchscreen UI (http://192.168.4.1)
 * ==============================================================================
 */

#include <Arduino.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <WebServer.h>
#include <ESPmDNS.h>
#include <esp_netif.h>
#include "dhcpserver/dhcpserver.h"
#include "dhcpserver/dhcpserver_options.h"
#include <lwip/dns.h>
#include <lwip/ip_addr.h>
#include <ArduinoJson.h>
#include <Preferences.h>
#include <Update.h>
#include <ArduinoOTA.h>
#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ILI9341.h>
#include <driver/gpio.h>
#include <rom/ets_sys.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <freertos/queue.h>
#include <freertos/semphr.h>

#include "genesis_memory_engine.h"
#include "genesis_survival_engine.h"
#include "genesis_touch_engine.h"
#include "genesis_knowledge_engine.h"

// ==============================================================================
// 1. NETWORK & CLOUD AI CONFIGURATION
// ==============================================================================
const char* WIFI_SSID     = "Lost Case ";
const char* WIFI_PASSWORD = "453441C1";

const char* AP_SSID       = "ESP32-C5-AI";
const char* AP_PASSWORD   = "12345678";

String localGatewayUrl    = "http://10.33.110.35:8000/api/iot/chat";
String customGeminiApiKey = "";
String openRouterApiKey   = "";

// ==============================================================================
// 2. HARDWARE PIN DEFINITIONS (ESP32-C5 + 2.4" ILI9341)
// ==============================================================================
#define TFT_SCK        10
#define TFT_MISO       9
#define TFT_MOSI       8
#define TFT_CS         6
#define TFT_DC         7
#define TFT_RST        2   // MUST stay on Pin 2 (3.3V HIGH) so the 2.4" TFT screen never blanks!
#define TOUCH_TCLK_PIN 9   // Use the SDO(MISO) wire on Pin 9 for T_CLK (SDO is not needed by LCD!)
#define TFT_BL         24

// ==============================================================================
// 3. CALIBRATED 320x240 LANDSCAPE TFT DRIVER SUBCLASS
// ==============================================================================
class GenesisTFT : public Adafruit_ILI9341 {
public:
    GenesisTFT(int8_t cs, int8_t dc, int8_t rst) : Adafruit_ILI9341(cs, dc, rst) {}

    void applyPanelRotation(uint8_t r) {
        r = r % 4;
        Adafruit_ILI9341::setRotation(r);
        // On this 2.4" V1.3 panel:
        // r=0 (MADCTL 0x48) & r=2 (MADCTL 0x88) are 320x240 Landscape (14-pin header on left/right)
        // r=1 (MADCTL 0x28) & r=3 (MADCTL 0xE8) are 240x320 Portrait  (14-pin header on top/bottom)
        if (r % 2 == 0) {
            _width  = 320;
            _height = 240;
        } else {
            _width  = 240;
            _height = 320;
        }
        setTextWrap(false);
    }

    void purgeAllGRAM() {
        for (uint8_t r = 0; r < 4; r++) {
            applyPanelRotation(r);
            fillScreen(ILI9341_BLACK);
        }
        applyPanelRotation(0); // Lock to 320x240 Landscape (14-pin header on LEFT)
    }
};

GenesisTFT tft = GenesisTFT(TFT_CS, TFT_DC, TFT_RST);
WebServer webServer(80);
Preferences prefs;

SemaphoreHandle_t spiMutex = NULL;
QueueHandle_t aiQueue = NULL;

struct AIRequest {
    char prompt[256];
};

volatile bool screenReady    = false;
volatile bool touchReady     = false;
volatile bool nvsReady       = false;
volatile bool aiBusy         = false;
volatile int currentRotation = 0; // 0 = 320x240 Landscape (14-pin header on left)

String lastPrompt   = "Live Satellite Telemetry & World AI Ready";
String lastAnswer   = "GENESIS GPT-4o OMNI: Connected to Live Satellite Telemetry (ISS NORAD-25544 + NOAA Space Weather) & Full World Knowledge. Use the keyboard, BOOT button, or 192.168.4.1 to ask anything!";
String lastAISource = "real_ai";
String typingBuffer = "";
volatile bool liveTypingMode = true;
volatile int kbSelectedIndex = 0;  // Default highlighted key: 'Q' for immediate hand typing
int presetQuestionIdx = 0;
uint32_t totalQueries = 1;

const char* PRESET_QUESTIONS[] = {
    "Give me live satellite telemetry and ISS position",
    "What is the current NOAA space weather and solar storm status?",
    "Who are you and who created you?",
    "Explain quantum computing in 25 words",
    "How do black holes and Hawking radiation work?",
    "How does the James Webb Space Telescope work?",
    "What is the speed of light and E=mc^2?",
    "What are the specs of this ESP32-C5 AI?"
};
const int PRESET_COUNT = 8;

const char* KB_LABELS[34] = {
    "Q","W","E","R","T","Y","U","I","O","P",
    "A","S","D","F","G","H","J","K","L","?",
    "Z","X","C","V","B","N","M","SPC","DEL","CLR",
    "ASK AI","SPACE","SEND >","ROTATE"
};

// Forward Declarations
void askGenesisAI(String prompt);
void enqueueAIQuery(const String& q);
void drawGenesisHUD(const char* statusTitle);
void drawPromptBar();
void flashKeyTyped(int idx);
void updateKeyboardHighlight(int oldIdx, int newIdx);
void pressKeyboardKey(int idx);
void toggleRotation();
String sanitizeAscii(const String& raw);

// ==============================================================================
// 4. RGB LED HEARTBEAT ENGINE (GPIO 27)
// ==============================================================================
void updateLedFlicker(bool isBusyNow = false) {
    static unsigned long lastFlicker = 0;
    static int step = 0;
    if (isBusyNow || aiBusy) {
        rgbLedWrite(RGB_BUILTIN, 0, 180, 255);
        return;
    }
    if (millis() - lastFlicker > 200) {
        lastFlicker = millis();
        step = (step + 1) % 4;
        switch (step) {
            case 0: rgbLedWrite(RGB_BUILTIN, 0, 100, 140); break;
            case 1: rgbLedWrite(RGB_BUILTIN, 0, 0, 0);     break;
            case 2: rgbLedWrite(RGB_BUILTIN, 130, 50, 0);  break;
            case 3: rgbLedWrite(RGB_BUILTIN, 0, 0, 0);     break;
        }
    }
}

// ==============================================================================
// 5. SOVEREIGN ON-CHIP GPT KNOWLEDGE & MATH ENGINE
// ==============================================================================
String evaluateEmbeddedMath(const String& expr) {
    String s = expr;
    s.toLowerCase();
    s.replace("calculate", "");
    s.replace("what is", "");
    s.replace("solve", "");
    s.replace("evaluate", "");
    s.replace("?", "");
    s.replace(" ", "");
    s.trim();

    char op = 0;
    int opIdx = -1;
    for (int i = 1; i < (int)s.length(); i++) {
        char c = s.charAt(i);
        if (c == '+' || c == '-' || c == '*' || c == '/' || c == '^' || c == '%') {
            op = c;
            opIdx = i;
            break;
        }
    }

    if (opIdx > 0 && opIdx < (int)s.length() - 1) {
        String leftStr = s.substring(0, opIdx);
        String rightStr = s.substring(opIdx + 1);
        bool leftValid = isDigit(leftStr.charAt(0)) || leftStr.charAt(0) == '-';
        bool rightValid = isDigit(rightStr.charAt(0)) || rightStr.charAt(0) == '-';
        if (leftValid && rightValid) {
            double a = leftStr.toDouble();
            double b = rightStr.toDouble();
            double res = 0;
            if (op == '+') res = a + b;
            else if (op == '-') res = a - b;
            else if (op == '*') res = a * b;
            else if (op == '/') {
                if (b == 0) return "Division by zero is undefined.";
                res = a / b;
            }
            else if (op == '^') res = pow(a, b);
            else if (op == '%') res = (long)a % (long)b;

            if (floor(res) == res) return "Calculated Result: " + String((long)res);
            return "Calculated Result: " + String(res, 4);
        }
    }
    return "";
}

String getGenesisOfflineAnswer(const String& prompt) {
    // 1. Advanced Math, Roots, Percentages & Expressions
    String mathRes = evaluateAdvancedMathAndUnits(prompt);
    if (mathRes.length() > 0) return mathRes;

    String lower = prompt;
    lower.toLowerCase();
    lower.trim();

    // 2. Check NVS stored user facts
    int mCount = getMemoryCount();
    for (int m = 0; m < mCount; m++) {
        String fact = memPrefs.getString(("m_" + String(m)).c_str(), "");
        String factLower = fact;
        factLower.toLowerCase();
        if (fact.length() > 0) {
            if ((lower.indexOf("name") >= 0 && factLower.indexOf("name") >= 0) ||
                (lower.indexOf("who am i") >= 0 && factLower.indexOf("name") >= 0) ||
                (factLower.length() > 4 && lower.indexOf(factLower.substring(0, min(10, (int)factLower.length()))) >= 0)) {
                return "From GENESIS Memory: " + fact;
            }
        }
    }

    // 3. Core Identity, Capabilities & Hardware Specs
    if (lower.indexOf("what can you do") >= 0 || lower.indexOf("what you can do") >= 0 || lower.indexOf("what do you do") >= 0 || lower.indexOf("capabilities") >= 0 || lower.indexOf("features") >= 0 || lower == "help") {
        return "I can answer any world knowledge, science, coding, history, or math question, track live ISS satellite telemetry (NORAD-25544) & NOAA space weather, and remember facts for you!";
    }
    if (lower.indexOf("who are you") >= 0 || lower.indexOf("what are you") >= 0 || lower.indexOf("your name") >= 0 || lower.indexOf("created you") >= 0 || lower.indexOf("made you") >= 0) {
        return "I am GENESIS GPT-4o OMNI, a sovereign artificial intelligence created and architected by Ishit Jain, running on your 240MHz RISC-V ESP32-C5 with a 320x240 touchscreen HUD.";
    }
    if (lower.indexOf("how are you") >= 0 || lower.indexOf("how r u") >= 0 || lower.indexOf("whats up") >= 0 || lower.indexOf("what's up") >= 0) {
        return "All cognitive, satellite telemetry, and world-knowledge systems are 100% online at 240MHz! Ask me any question about science, space, math, coding, or the world.";
    }
    if (lower.indexOf("spec") >= 0 || lower.indexOf("status") >= 0 || lower.indexOf("hardware") >= 0) {
        String netStat = (WiFi.status() == WL_CONNECTED) ? ("WiFi Connected (" + WiFi.localIP().toString() + ")") : "Dual Mobile-Net + AP Mode (192.168.4.1)";
        return "GENESIS GPT-4o OMNI | MCU: ESP32-C5 RISC-V 240MHz | Net: " + netStat + " | Free RAM: " + String(ESP.getFreeHeap() / 1024) + "KB | Queries: #" + String(totalQueries);
    }
    if (lower == "hi" || lower == "hello" || lower == "hey" || lower.indexOf("good morning") >= 0 || lower.indexOf("good evening") >= 0) {
        return "Hello Ishit Jain! GENESIS GPT-4o OMNI is online and ready. Type any science, coding, math, history, satellite, or world question!";
    }

    // 4. Check 100+ Topic On-Chip Encyclopedia in PROGMEM
    String kbAns = queryOnChipKnowledgeBase(prompt);
    if (kbAns.length() > 0) return kbAns;

    // 5. Check Medical / Survival Knowledge Base
    String sTitle, sGuidance;
    if (checkAndProcessSurvival(prompt, sTitle, sGuidance)) {
        return sTitle + ": " + sGuidance;
    }

    // 6. Intelligent analytical response when offline
    return "GENESIS Sovereign Core analyzed '" + prompt + "'. Connect to Wi-Fi 'Lost Case ' or keep Mobile Data ON while connected to ESP32-C5-AI (192.168.4.1) for live Cloud GPT synthesis.";
}

// ==============================================================================
// 6. 320x240 CINEMATIC GPT HUD & ON-SCREEN QWERTY KEYBOARD ENGINE
// ==============================================================================
String sanitizeAscii(const String& raw) {
    String out = "";
    out.reserve(raw.length());
    bool lastSpace = false;
    for (size_t i = 0; i < raw.length(); i++) {
        unsigned char c = (unsigned char)raw.charAt(i);
        if (c == '\r' || c == '\n' || c == '\t') {
            if (!lastSpace && out.length() > 0) {
                out += ' ';
                lastSpace = true;
            }
        } else if (c >= 32 && c <= 126) {
            if (c == '*' || c == '#' || c == '`') continue;
            if (c == ' ') {
                if (!lastSpace && out.length() > 0) {
                    out += ' ';
                    lastSpace = true;
                }
            } else {
                out += (char)c;
                lastSpace = false;
            }
        }
    }
    out.trim();
    return out;
}

void renderWrappedBox(const String& rawText, int boxX, int boxY, int boxW, int boxH, uint16_t color) {
    if (!screenReady) return;
    String text = sanitizeAscii(rawText);
    tft.setTextWrap(false);
    tft.setTextSize(1);
    tft.setTextColor(color);

    int charW = 6;
    int lineH = 11;
    int maxCharsPerLine = max(1, boxW / charW);
    int maxLines = max(1, boxH / lineH);

    int curLine = 0;
    int idx = 0;
    int len = text.length();

    while (idx < len && curLine < maxLines) {
        while (idx < len && text.charAt(idx) == ' ') idx++;
        if (idx >= len) break;

        int remaining = len - idx;
        int take = remaining;
        if (take > maxCharsPerLine) {
            take = maxCharsPerLine;
            int spacePos = -1;
            for (int k = take; k >= 1; k--) {
                if (idx + k < len && text.charAt(idx + k) == ' ') {
                    spacePos = k;
                    break;
                }
            }
            if (spacePos > 0) take = spacePos;
        }

        String lineStr = text.substring(idx, idx + take);
        idx += take;
        while (idx < len && text.charAt(idx) == ' ') idx++;

        if (curLine == maxLines - 1 && idx < len) {
            if ((int)lineStr.length() > maxCharsPerLine - 3) {
                lineStr = lineStr.substring(0, max(0, maxCharsPerLine - 3));
            }
            lineStr += "...";
        }

        tft.setCursor(boxX, boxY + curLine * lineH);
        tft.print(lineStr);
        curLine++;
    }
}

void drawCircularArcReactor(int cx, int cy) {
    tft.drawCircle(cx, cy, 7, 0x051F);
    tft.drawCircle(cx, cy, 5, ILI9341_CYAN);
    tft.fillCircle(cx, cy, 2, aiBusy ? ILI9341_YELLOW : 0xFFE0);
}

void drawPromptBarInternal() {
    int W = tft.width();
    int pY = 21;
    int pH = 20;
    tft.fillRect(2, pY, W - 4, pH, 0x0121);
    tft.drawRect(2, pY, W - 4, pH, 0x07E0);

    tft.setTextWrap(false);
    tft.setTextSize(1);
    tft.setTextColor(0x07E0);
    tft.setCursor(6, pY + 6);
    tft.print("ASK > ");

    if (liveTypingMode || typingBuffer.length() > 0) {
        String keyLbl = String(KB_LABELS[kbSelectedIndex]);
        String shown = typingBuffer;
        int maxLen = max(8, (W - 110) / 6);
        if ((int)shown.length() > maxLen) {
            shown = shown.substring(shown.length() - maxLen);
        }
        tft.setTextColor(ILI9341_WHITE);
        tft.setCursor(42, pY + 6);
        tft.print(shown);

        // Draw glowing yellow active key preview cursor right after typed text
        int curX = tft.getCursorX() + 2;
        int badgeW = keyLbl.length() * 6 + 6;
        tft.fillRect(curX, pY + 3, badgeW, 14, 0xFFE0);
        tft.setTextColor(0x0000);
        tft.setCursor(curX + 3, pY + 6);
        tft.print(keyLbl);

        if (typingBuffer.length() == 0 && curX + badgeW + 60 < W) {
            tft.setTextColor(0x07FF);
            tft.setCursor(curX + badgeW + 5, pY + 6);
            tft.print("<Click:Next Hold:Type");
        } else if (typingBuffer.length() > 0 && curX + badgeW + 54 < W) {
            tft.setTextColor(0xFFE0);
            tft.setCursor(curX + badgeW + 5, pY + 6);
            tft.print("<Hold 1s:SEND");
        }
    } else {
        String dispP = sanitizeAscii(lastPrompt);
        int maxChars = max(10, (W - 50) / 6);
        if ((int)dispP.length() > maxChars) {
            dispP = dispP.substring(0, maxChars - 2) + "..";
        }
        tft.setTextColor(ILI9341_WHITE);
        tft.setCursor(42, pY + 6);
        tft.print(dispP);
    }
}

void drawPromptBar() {
    if (!screenReady) return;
    if (spiMutex && xSemaphoreTake(spiMutex, pdMS_TO_TICKS(100)) != pdTRUE) return;
    drawPromptBarInternal();
    if (spiMutex) xSemaphoreGive(spiMutex);
}

void drawSingleKeyInternal(int idx, bool selected) {
    if (idx < 0 || idx >= 34) return;
    int W = tft.width();
    int H = tft.height();
    int kbTop = H - 86;

    int kx = 0, ky = 0, kw = 0, kh = 18;
    uint16_t borderCol = 0x39E7;
    uint16_t fillCol   = 0x10A2;
    uint16_t txtCol    = ILI9341_WHITE;

    if (idx < 30) {
        int row = idx / 10;
        int col = idx % 10;
        int cellW = (W - 8) / 10;
        kx = 4 + col * cellW;
        ky = kbTop + 2 + row * 20;
        kw = cellW - 2;
        kh = 18;
        if (idx >= 27) {
            borderCol = 0xFD20;
            txtCol    = 0xFFE0;
        }
    } else {
        int actIdx = idx - 30;
        int cellW = (W - 8) / 4;
        kx = 4 + actIdx * cellW;
        ky = kbTop + 62;
        kw = cellW - 2;
        kh = 21;
        if (actIdx == 0)      { borderCol = 0x07E0; txtCol = 0x07E0; fillCol = 0x0121; }
        else if (actIdx == 1) { borderCol = 0x07FF; txtCol = 0x07FF; fillCol = 0x0083; }
        else if (actIdx == 2) { borderCol = 0xFFE0; txtCol = 0xFFE0; fillCol = 0x2100; }
        else                  { borderCol = 0xF81F; txtCol = 0xF81F; fillCol = 0x1803; }
    }

    if (selected) {
        fillCol   = 0xFFE0;
        borderCol = ILI9341_WHITE;
        txtCol    = 0x0000;
    }

    tft.fillRect(kx, ky, kw, kh, fillCol);
    tft.drawRect(kx, ky, kw, kh, borderCol);
    if (selected && kw > 4 && kh > 4) {
        tft.drawRect(kx + 1, ky + 1, kw - 2, kh - 2, ILI9341_WHITE);
    }

    const char* lbl = KB_LABELS[idx];
    int lblLen = strlen(lbl);
    int tx = kx + max(2, (kw - lblLen * 6) / 2);
    int ty = ky + (kh - 8) / 2;

    tft.setTextWrap(false);
    tft.setTextSize(1);
    tft.setTextColor(txtCol);
    tft.setCursor(tx, ty);
    tft.print(lbl);
}

void flashKeyTyped(int idx) {
    if (!screenReady || idx < 0 || idx >= 34) return;
    if (spiMutex && xSemaphoreTake(spiMutex, pdMS_TO_TICKS(100)) != pdTRUE) return;
    int W = tft.width();
    int H = tft.height();
    int kbTop = H - 86;
    int kx = 0, ky = 0, kw = 0, kh = 18;
    if (idx < 30) {
        int row = idx / 10;
        int col = idx % 10;
        int cellW = (W - 8) / 10;
        kx = 4 + col * cellW;
        ky = kbTop + 2 + row * 20;
        kw = cellW - 2;
        kh = 18;
    } else {
        int actIdx = idx - 30;
        int cellW = (W - 8) / 4;
        kx = 4 + actIdx * cellW;
        ky = kbTop + 62;
        kw = cellW - 2;
        kh = 21;
    }
    tft.fillRect(kx, ky, kw, kh, 0x07E0); // Bright Neon Green confirmation flash
    tft.drawRect(kx, ky, kw, kh, ILI9341_WHITE);
    const char* lbl = KB_LABELS[idx];
    int tx = kx + max(2, (kw - (int)strlen(lbl) * 6) / 2);
    int ty = ky + (kh - 8) / 2;
    tft.setTextSize(1);
    tft.setTextColor(0x0000);
    tft.setCursor(tx, ty);
    tft.print(lbl);
    if (spiMutex) xSemaphoreGive(spiMutex);
}

void updateKeyboardHighlight(int oldIdx, int newIdx) {
    if (!screenReady) return;
    if (spiMutex && xSemaphoreTake(spiMutex, pdMS_TO_TICKS(100)) != pdTRUE) return;
    drawSingleKeyInternal(oldIdx, false);
    drawSingleKeyInternal(newIdx, true);
    drawPromptBarInternal();
    if (spiMutex) xSemaphoreGive(spiMutex);
}

void drawGenesisHUD(const char* statusTitle) {
    if (!screenReady) return;
    if (spiMutex && xSemaphoreTake(spiMutex, pdMS_TO_TICKS(250)) != pdTRUE) return;

    int W = tft.width();
    int H = tft.height();
    tft.setTextWrap(false);

    // 100% Full-Screen Edge-to-Edge Clean Wipe
    tft.fillScreen(ILI9341_BLACK);
    tft.drawRect(0, 0, W, H, 0x051F);

    // 1. TOP CINEMATIC HEADER BAR (Y: 1..19)
    tft.fillRect(1, 1, W - 2, 19, 0x0085);
    tft.drawFastHLine(1, 20, W - 2, ILI9341_CYAN);

    drawCircularArcReactor(11, 10);

    tft.setTextColor(ILI9341_CYAN);
    tft.setTextSize(2);
    tft.setCursor(22, 3);
    tft.print("GENESIS GPT");

    tft.setTextSize(1);
    String ipTxt = (WiFi.status() == WL_CONNECTED) ? ("WEB:" + WiFi.localIP().toString()) : "AP:192.168.4.1";
    if (W >= 300) {
        tft.setTextColor(0x07E0);
        tft.setCursor(160, 2);
        tft.print(ipTxt + " | SAT:LIVE");
        tft.setTextColor(0xFD20);
        tft.setCursor(160, 11);
        tft.printf("WORLD+SAT AI | QRY:#%d", totalQueries);
    } else {
        tft.setTextColor(0x07E0);
        tft.setCursor(W - 76, 2);
        tft.print("SAT:25544");
        tft.setTextColor(0xFD20);
        tft.setCursor(W - 76, 11);
        tft.printf("QRY:#%d", totalQueries);
    }

    // 2. USER PROMPT & LIVE TYPING BAR (Y: 21..40)
    drawPromptBarInternal();

    // 3. MAIN GPT COGNITIVE RESPONSE VIEWPORT (Y: 42..H-88)
    int kbTop = H - 86;
    int aY = 42;
    int aH = kbTop - aY - 2;
    tft.fillRect(2, aY, W - 4, aH, 0x0042);
    tft.drawRect(2, aY, W - 4, aH, 0x051F);

    // Cinematic Gold Corner Brackets
    tft.drawFastHLine(2, aY, 8, 0xFFE0);
    tft.drawFastVLine(2, aY, 8, 0xFFE0);
    tft.drawFastHLine(W - 10, aY, 8, 0xFFE0);
    tft.drawFastVLine(W - 3, aY, 8, 0xFFE0);
    tft.drawFastHLine(2, aY + aH - 1, 8, 0xFFE0);
    tft.drawFastVLine(2, aY + aH - 8, 8, 0xFFE0);
    tft.drawFastHLine(W - 10, aY + aH - 1, 8, 0xFFE0);
    tft.drawFastVLine(W - 3, aY + aH - 8, 8, 0xFFE0);

    tft.setTextSize(1);
    tft.setTextColor(0xFD20);
    tft.setCursor(8, aY + 3);
    tft.print("GENESIS WORLD & SATELLITE AI CORE");

    tft.setTextColor(aiBusy ? 0xFFE0 : 0x07E0);
    tft.setCursor(W - 68, aY + 3);
    if (aiBusy) {
        tft.print("[THINKING]");
    } else if (lastAISource == "sat_live") {
        tft.print("[SAT-LIVE]");
    } else {
        tft.print("[WORLD-AI]");
    }

    tft.drawFastHLine(5, aY + 13, W - 10, 0x0290);

    // Word-wrapped response text strictly inside viewport
    renderWrappedBox(lastAnswer, 8, aY + 16, W - 16, aH - 19, ILI9341_WHITE);

    // 4. FULL ON-SCREEN QWERTY TOUCH KEYBOARD (Y: H-86..H-2)
    tft.fillRect(2, kbTop, W - 4, 84, 0x0021);
    tft.drawFastHLine(2, kbTop, W - 4, ILI9341_CYAN);

    for (int k = 0; k < 34; k++) {
        drawSingleKeyInternal(k, (k == kbSelectedIndex));
    }

    if (spiMutex) xSemaphoreGive(spiMutex);
}

void toggleRotation() {
    currentRotation = (currentRotation == 0) ? 2 : 0;
    if (spiMutex && xSemaphoreTake(spiMutex, pdMS_TO_TICKS(250)) == pdTRUE) {
        tft.applyPanelRotation(currentRotation);
        tft.fillScreen(ILI9341_BLACK);
        xSemaphoreGive(spiMutex);
    }
    drawGenesisHUD("ROTATED");
}

void pressKeyboardKey(int idx) {
    if (idx < 0 || idx >= 34) return;
    if (idx < 27) {
        char ch = KB_LABELS[idx][0];
        if (typingBuffer.length() > 0 && ch >= 'A' && ch <= 'Z') {
            ch = ch + 32;
        }
        typingBuffer += ch;
        drawPromptBar();
    } else if (idx == 27 || idx == 31) {
        typingBuffer += ' ';
        drawPromptBar();
    } else if (idx == 28) {
        if (typingBuffer.length() > 0) {
            typingBuffer.remove(typingBuffer.length() - 1);
            drawPromptBar();
        }
    } else if (idx == 29) {
        typingBuffer = "";
        drawPromptBar();
    } else if (idx == 30 || idx == 32) {
        if (typingBuffer.length() > 0) {
            String q = typingBuffer;
            typingBuffer = "";
            enqueueAIQuery(q);
        } else {
            String q = String(PRESET_QUESTIONS[presetQuestionIdx]);
            presetQuestionIdx = (presetQuestionIdx + 1) % PRESET_COUNT;
            enqueueAIQuery(q);
        }
    } else if (idx == 33) {
        toggleRotation();
    }
}

// ==============================================================================
// 7. QUAD-ROUTE AI COMMUNICATION ENGINE
// ==============================================================================
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

void ensureReliableDNS() {
    // Keep the mobile hotspot's native DHCP DNS relay as primary (slot 0) so cellular NAT64/DNS works!
    IPAddress gw = WiFi.gatewayIP();
    if (gw[0] != 0) {
        ip_addr_t dns0;
        IP4_ADDR(&dns0.u_addr.ip4, gw[0], gw[1], gw[2], gw[3]);
        dns0.type = IPADDR_TYPE_V4;
        dns_setserver(0, &dns0);
    }
    ip_addr_t dns1;
    IP4_ADDR(&dns1.u_addr.ip4, 8, 8, 8, 8); // Google DNS as backup (slot 1)
    dns1.type = IPADDR_TYPE_V4;
    dns_setserver(1, &dns1);
}

bool isSatelliteQuery(const String& q) {
    String s = q;
    s.toLowerCase();
    return (s.indexOf("satellite") >= 0 || s.indexOf("iss") >= 0 ||
            s.indexOf("norad") >= 0 || s.indexOf("orbit") >= 0 ||
            s.indexOf("space station") >= 0 || s.indexOf("space weather") >= 0 ||
            s.indexOf("solar storm") >= 0 || s.indexOf("telemetry") >= 0);
}

String fetchLiveSatelliteTelemetryESP32() {
    if (WiFi.status() != WL_CONNECTED) return "";
    ensureReliableDNS();
    WiFiClientSecure sec;
    sec.setInsecure();
    HTTPClient https;
    String out = "";
    if (https.begin(sec, "https://api.wheretheiss.at/v1/satellites/25544")) {
        https.setTimeout(6000);
        int code = https.GET();
        if (code == 200) {
            String payload = https.getString();
            JsonDocument doc;
            if (!deserializeJson(doc, payload)) {
                double lat = doc["latitude"] | 0.0;
                double lon = doc["longitude"] | 0.0;
                double alt = doc["altitude"] | 420.0;
                double vel = doc["velocity"] | 27580.0;
                String vis = doc["visibility"] | "daylight";
                vis.toUpperCase();
                char buf[220];
                snprintf(buf, sizeof(buf),
                    "LIVE SATELLITE [ISS NORAD-25544]: Pos %.2f%c, %.2f%c | Alt %.1fkm | Speed %.0fkm/h | Orbit: %s",
                    fabs(lat), (lat >= 0 ? 'N' : 'S'),
                    fabs(lon), (lon >= 0 ? 'E' : 'W'),
                    alt, vel, vis.c_str());
                out = String(buf);
            }
        }
        https.end();
    }
    return out;
}

String fetchPollinationsESP32(const String& sysPrompt, const String& userPrompt) {
    if (WiFi.status() != WL_CONNECTED) return "";
    ensureReliableDNS();
    WiFiClientSecure sec;
    sec.setInsecure();
    HTTPClient https;
    String out = "";
    if (https.begin(sec, "https://text.pollinations.ai/openai")) {
        https.addHeader("Content-Type", "application/json");
        https.setTimeout(10000);

        JsonDocument reqDoc;
        reqDoc["model"] = "openai";
        reqDoc["stream"] = false;
        JsonArray msgs = reqDoc["messages"].to<JsonArray>();
        JsonObject sObj = msgs.add<JsonObject>();
        sObj["role"] = "system";
        sObj["content"] = sysPrompt;
        JsonObject uObj = msgs.add<JsonObject>();
        uObj["role"] = "user";
        uObj["content"] = userPrompt;

        String body;
        serializeJson(reqDoc, body);
        int code = https.POST(body);
        Serial.printf("[Pollinations AI] HTTP %d\n", code);
        if (code == 200) {
            String resp = https.getString();
            resp.trim();
            JsonDocument resDoc;
            if (!deserializeJson(resDoc, resp)) {
                out = sanitizeAscii(resDoc["choices"][0]["message"]["content"] | "");
            } else {
                out = sanitizeAscii(resp);
            }
        }
        https.end();
    }
    return out;
}

String fetchWikipediaWorldKnowledgeESP32(const String& rawPrompt) {
    if (WiFi.status() != WL_CONNECTED) return "";
    ensureReliableDNS();
    String q = rawPrompt;
    q.replace("?", "");
    q.trim();

    WiFiClientSecure sec;
    sec.setInsecure();
    HTTPClient https;
    String searchUrl = "https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=" + urlEncode(q) + "&utf8=&format=json&srlimit=1";
    String topTitle = "";
    if (https.begin(sec, searchUrl)) {
        https.addHeader("User-Agent", "GenesisOmniESP32/2.0");
        https.setTimeout(6000);
        if (https.GET() == 200) {
            String body = https.getString();
            JsonDocument doc;
            if (!deserializeJson(doc, body)) {
                topTitle = doc["query"]["search"][0]["title"] | "";
            }
        }
        https.end();
    }
    if (topTitle.length() == 0) return "";

    String sumTitle = topTitle;
    sumTitle.replace(" ", "_");
    String sumUrl = "https://en.wikipedia.org/api/rest_v1/page/summary/" + urlEncode(sumTitle);
    String extract = "";
    if (https.begin(sec, sumUrl)) {
        https.addHeader("User-Agent", "GenesisOmniESP32/2.0");
        https.setTimeout(6000);
        if (https.GET() == 200) {
            String body = https.getString();
            JsonDocument filter;
            filter["extract"] = true;
            JsonDocument doc;
            if (!deserializeJson(doc, body, DeserializationOption::Filter(filter))) {
                extract = sanitizeAscii(doc["extract"] | "");
            }
        }
        https.end();
    }
    if (extract.length() > 210) {
        int dot = extract.indexOf(". ", 110);
        if (dot > 0 && dot < 220) extract = extract.substring(0, dot + 1);
        else extract = extract.substring(0, 210) + "...";
    }
    return extract;
}

volatile bool browserPushedAnswer = false;

bool isInstantIdentityOrCapabilityQuery(const String& rawPrompt, String& fastOut) {
    String lower = rawPrompt;
    lower.toLowerCase();
    lower.replace("?", "");
    lower.replace("!", "");
    lower.trim();

    if (lower.indexOf("what can you do") >= 0 || lower.indexOf("what you can do") >= 0 ||
        lower.indexOf("what do you do") >= 0 || lower.indexOf("capabilities") >= 0 ||
        lower.indexOf("features") >= 0 || lower == "help") {
        fastOut = "I can answer any world knowledge, science, coding, history, or math question, track live ISS satellite telemetry (NORAD-25544) & NOAA space weather, and remember facts for you!";
        return true;
    }
    if (lower.indexOf("who are you") >= 0 || lower.indexOf("what are you") >= 0 ||
        lower.indexOf("your name") >= 0 || lower.indexOf("created you") >= 0 ||
        lower.indexOf("made you") >= 0 || lower.indexOf("who built you") >= 0) {
        fastOut = "I am GENESIS GPT-4o OMNI, a sovereign artificial intelligence created and architected by Ishit Jain, running on your 240MHz RISC-V ESP32-C5 with a 320x240 touchscreen HUD.";
        return true;
    }
    if (lower.indexOf("how are you") >= 0 || lower.indexOf("how r u") >= 0 ||
        lower.indexOf("whats up") >= 0 || lower.indexOf("what's up") >= 0) {
        fastOut = "All cognitive, satellite telemetry, and world-knowledge systems are 100% online at 240MHz! Ask me any question about science, space, math, coding, or the world.";
        return true;
    }
    if (lower == "hi" || lower == "hello" || lower == "hey" ||
        lower == "good morning" || lower == "good evening") {
        fastOut = "Hello Ishit Jain! GENESIS GPT-4o OMNI is online and ready. Ask me any science, coding, math, history, satellite, or world question!";
        return true;
    }
    return false;
}

String chatHistQ[3] = {"", "", ""};
String chatHistA[3] = {"", "", ""};
int chatHistCount = 0;

void pushChatTurn(const String& q, const String& a) {
    if (q.length() == 0 || a.length() == 0) return;
    if (chatHistCount < 3) {
        chatHistQ[chatHistCount] = q;
        chatHistA[chatHistCount] = a;
        chatHistCount++;
    } else {
        chatHistQ[0] = chatHistQ[1]; chatHistA[0] = chatHistA[1];
        chatHistQ[1] = chatHistQ[2]; chatHistA[1] = chatHistA[2];
        chatHistQ[2] = q;            chatHistA[2] = a;
    }
}

void askGenesisAI(String prompt) {
    prompt.trim();
    if (prompt.length() == 0) return;

    aiBusy = true;
    browserPushedAnswer = false;
    updateLedFlicker(true);
    totalQueries++;
    lastPrompt = prompt;
    lastAnswer = "Synthesizing answer..."; // Never leave a previous query's answer in lastAnswer!
    typingBuffer = ""; // Always clear typingBuffer so ASK > shows the active question!
    liveTypingMode = false;
    drawGenesisHUD("THINKING");

    bool success = false;
    String answer = "";
    bool satQuery = isSatelliteQuery(prompt);

    // 1. Check Persistent NVS Memory Feed/Recall ("remember...", "my name is...")
    if (checkAndProcessFeeding(prompt, answer)) {
        success = true;
        lastAISource = "nvs_memory";
    }

    // 2. Check instant math calculation first if pure arithmetic
    if (!success) {
        String fastMath = evaluateAdvancedMathAndUnits(prompt);
        if (fastMath.length() > 0) {
            answer = fastMath;
            success = true;
            lastAISource = "math_engine";
        }
    }

    // 3. Check instant conversational / capability / identity queries (< 2ms, works 100% offline & online!)
    if (!success) {
        String fastConv = "";
        if (isInstantIdentityOrCapabilityQuery(prompt, fastConv)) {
            answer = fastConv;
            success = true;
            lastAISource = "sovereign_kb";
        }
    }

    // 4. Route 1: Local PC OmniModel AI Gateway over Wi-Fi (Fastest HTTP route, < 2s!)
    if (!success && !browserPushedAnswer && WiFi.status() == WL_CONNECTED && localGatewayUrl.length() > 8) {
        WiFiClient client;
        client.setConnectionTimeout(900);
        HTTPClient http;
        http.setConnectTimeout(900);
        http.setTimeout(5800);
        String ep = localGatewayUrl + "?format=text&max_words=52&q=" + urlEncode(prompt);
        if (http.begin(client, ep)) {
            int httpCode = http.GET();
            Serial.printf("[Gateway] HTTP %d\n", httpCode);
            if (httpCode == 200) {
                String resp = sanitizeAscii(http.getString());
                if (resp.length() > 2 && resp.indexOf("DOCTYPE") < 0 && resp.indexOf("All providers failed") < 0 && resp.indexOf("Provider Error") < 0) {
                    answer = resp;
                    success = true;
                    lastAISource = satQuery ? "sat_live" : "gateway_ai";
                }
            }
            http.end();
        }
    }

    // 5. Direct Live Satellite Orbital Telemetry if asking for satellite/ISS/orbit data over Wi-Fi/Hotspot
    if (!success && !browserPushedAnswer && satQuery && WiFi.status() == WL_CONNECTED) {
        String liveSatData = fetchLiveSatelliteTelemetryESP32();
        if (liveSatData.length() > 10) {
            answer = liveSatData;
            success = true;
            lastAISource = "sat_live";
        }
    }

    String memContext = getMemoryContextString();
    String frontierSystem = "You are GENESIS GPT-4o OMNI, an omniscient ChatGPT-class AI assistant created by Ishit Jain. You can answer any question on science, coding, math, history, geography, translations, stories, advice, and satellite telemetry. Respond directly and accurately in plain ASCII text under 50 words without markdown or asterisks." + (memContext.length() > 0 ? (" User Facts: " + memContext) : "");

    // 6. Route 2: Direct OpenRouter Multi-Model Cloud LLM API over Mobile Hotspot / Wi-Fi (with Multi-Turn Memory!)
    if (!success && !browserPushedAnswer && WiFi.status() == WL_CONNECTED && openRouterApiKey.length() > 10) {
        ensureReliableDNS();
        WiFiClientSecure secureClient;
        secureClient.setInsecure();
        HTTPClient https;
        if (https.begin(secureClient, "https://openrouter.ai/api/v1/chat/completions")) {
            https.addHeader("Content-Type", "application/json");
            https.addHeader("Authorization", "Bearer " + openRouterApiKey);
            https.setConnectTimeout(3500);
            https.setTimeout(7500);

            JsonDocument reqDoc;
            JsonArray modelsArr = reqDoc["models"].to<JsonArray>();
            modelsArr.add("nvidia/nemotron-3-ultra-550b-a55b:free");
            modelsArr.add("liquid/lfm-2.5-2.6b:free");
            modelsArr.add("openrouter/free");
            JsonObject reas = reqDoc["reasoning"].to<JsonObject>();
            reas["exclude"] = true;

            JsonArray msgs = reqDoc["messages"].to<JsonArray>();
            JsonObject sysM = msgs.add<JsonObject>();
            sysM["role"] = "system";
            sysM["content"] = frontierSystem;
            for (int h = max(0, chatHistCount - 2); h < chatHistCount; h++) {
                JsonObject uH = msgs.add<JsonObject>();
                uH["role"] = "user";
                uH["content"] = chatHistQ[h];
                JsonObject aH = msgs.add<JsonObject>();
                aH["role"] = "assistant";
                aH["content"] = chatHistA[h];
            }
            JsonObject usrM = msgs.add<JsonObject>();
            usrM["role"] = "user";
            usrM["content"] = prompt;

            String body;
            serializeJson(reqDoc, body);
            int code = https.POST(body);
            Serial.printf("[OpenRouter Direct] HTTP %d\n", code);
            if (code == 200) {
                String payload = https.getString();
                payload.trim();
                JsonDocument filter;
                filter["choices"][0]["message"]["content"] = true;
                JsonDocument resDoc;
                if (!deserializeJson(resDoc, payload, DeserializationOption::Filter(filter))) {
                    String content = resDoc["choices"][0]["message"]["content"].as<String>();
                    content = sanitizeAscii(content);
                    if (content.length() > 1 && content != "null") {
                        answer = content;
                        success = true;
                        lastAISource = "cloud_gpt";
                    }
                }
            }
            https.end();
        }
    }

    // 7. Route 3: Direct Wikipedia Global World Knowledge API (6.8M+ Live Articles on ESP32-C5)
    if (!success && !browserPushedAnswer && WiFi.status() == WL_CONNECTED) {
        String wikiAns = fetchWikipediaWorldKnowledgeESP32(prompt);
        if (wikiAns.length() > 10) {
            answer = wikiAns;
            success = true;
            lastAISource = "wiki_world";
        }
    }

    // 8. If connected via ESP32-C5-AI SoftAP (192.168.4.1) with a Mobile Phone, give the phone's 4G/5G browser up to 4.5s to push its Cloud GPT answer!
    if (!success && !browserPushedAnswer && WiFi.status() != WL_CONNECTED && WiFi.softAPgetStationNum() > 0) {
        unsigned long waitT0 = millis();
        while (!browserPushedAnswer && (millis() - waitT0 < 4500)) {
            vTaskDelay(pdMS_TO_TICKS(50));
        }
    }

    // If the mobile phone browser pushed a live 4G/5G answer while we were checking, keep that pushed answer!
    if (browserPushedAnswer) {
        pushChatTurn(lastPrompt, lastAnswer);
        aiBusy = (aiQueue && uxQueueMessagesWaiting(aiQueue) > 0);
        return;
    }

    // 9. Route 4: On-Chip Sovereign Knowledge Base (100+ PROGMEM Domains + Survival + NVS)
    if (!success) {
        answer = sanitizeAscii(getGenesisOfflineAnswer(prompt));
        lastAISource = "sovereign_kb";
    }

    lastAnswer = answer;
    pushChatTurn(lastPrompt, lastAnswer);
    if (nvsReady) {
        prefs.putString("lastQ", lastPrompt);
        prefs.putString("lastA", lastAnswer);
        prefs.putUInt("qCount", totalQueries);
    }

    Serial.printf("\n[GENESIS GPT (%s)]\n  Q: %s\n  A: %s\n", lastAISource.c_str(), lastPrompt.c_str(), lastAnswer.c_str());
    drawGenesisHUD("GENESIS GPT");
    aiBusy = (aiQueue && uxQueueMessagesWaiting(aiQueue) > 0);
}

volatile uint32_t queuedQuerySeq = 0;
volatile uint32_t completedQuerySeq = 0;

void enqueueAIQuery(const String& q) {
    aiBusy = true;
    queuedQuerySeq++;
    if (aiQueue) {
        AIRequest req;
        strncpy(req.prompt, q.c_str(), sizeof(req.prompt) - 1);
        req.prompt[sizeof(req.prompt) - 1] = '\0';
        xQueueSend(aiQueue, &req, 0);
    } else {
        askGenesisAI(q);
        completedQuerySeq++;
    }
}

// ==============================================================================
// 8. WEB SERVER & DUAL MOBILE-NET + WI-FI TOUCH KEYBOARD UI (192.168.4.1)
// ==============================================================================
void handleRoot() {
    String staIp = (WiFi.status() == WL_CONNECTED) ? ("WiFi: " + WiFi.localIP().toString()) : "Dual Net + AP: 192.168.4.1";
    String html = String("<!DOCTYPE html><html lang='en'><head><meta charset='UTF-8'>") +
"<meta name='viewport' content='width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no'>" +
"<title>GENESIS GPT-4o OMNI | ESP32-C5</title>" +
"<style>" +
":root{--cyan:#00f0ff;--gold:#fbbf24;--emerald:#10b981;--bg:#030712;--card:#0b1324;}" +
"*{box-sizing:border-box;margin:0;padding:0;font-family:system-ui,-apple-system,sans-serif;}" +
"body{background:radial-gradient(circle at top,#0f172a,#030712);color:#f8fafc;min-height:100vh;display:flex;flex-direction:column;align-items:center;padding:12px;}" +
".wrap{width:100%;max-width:480px;display:flex;flex-direction:column;gap:10px;}" +
".hdr{background:var(--card);border:1.5px solid var(--cyan);border-radius:14px;padding:12px 14px;display:flex;justify-content:space-between;align-items:center;box-shadow:0 0 20px rgba(0,240,255,0.2);}" +
".title{font-size:18px;font-weight:900;color:var(--cyan);letter-spacing:0.5px;}" +
".sub{font-size:11px;color:#94a3b8;margin-top:2px;}" +
".scr{background:#020617;border:2px solid #0284c7;border-radius:12px;padding:12px;}" +
".qbox{background:#062c22;border:1px solid var(--emerald);color:#a7f3d0;padding:8px 10px;border-radius:8px;font-size:13px;font-weight:700;margin-bottom:8px;}" +
".abox{background:#091124;border:1px solid #1e3a8a;color:#fff;padding:10px;border-radius:8px;font-size:14px;line-height:1.45;min-height:70px;}" +
".kb{display:grid;grid-template-columns:repeat(10,1fr);gap:4px;background:#050b18;padding:8px;border-radius:10px;border:1px solid #1e293b;}" +
".k{background:#111c33;border:1px solid #334155;color:#fff;border-radius:6px;padding:9px 0;font-size:12px;font-weight:700;text-align:center;cursor:pointer;user-select:none;}" +
".k:active{background:var(--cyan);color:#000;}" +
".act{grid-column:span 10;display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-top:4px;}" +
".abtn{padding:10px 4px;border-radius:8px;font-size:12px;font-weight:800;text-align:center;cursor:pointer;border:1.5px solid var(--cyan);background:#0c1930;color:var(--cyan);}" +
".inp-row{display:flex;gap:6px;}" +
".inp{flex:1;background:#0f172a;border:1.5px solid #334155;border-radius:10px;padding:12px;color:#fff;font-size:14px;outline:none;}" +
".inp:focus{border-color:var(--cyan);}" +
".sbtn{background:linear-gradient(135deg,var(--cyan),#0284c7);color:#000;font-weight:900;border:none;border-radius:10px;padding:0 14px;font-size:13px;cursor:pointer;}" +
".mbtn{background:#1e293b;color:var(--gold);border:1.5px solid var(--gold);border-radius:10px;padding:0 12px;font-size:14px;font-weight:800;cursor:pointer;}" +
".chips{display:flex;flex-wrap:wrap;gap:6px;}" +
".chip{background:#0f172a;border:1px solid #334155;color:#38bdf8;padding:6px 10px;border-radius:99px;font-size:11px;font-weight:600;cursor:pointer;}" +
".log{background:#050b18;border:1px solid #1e293b;border-radius:10px;padding:10px;max-height:220px;overflow-y:auto;display:flex;flex-direction:column;gap:8px;font-size:13px;}" +
".msg-u{color:#a7f3d0;font-weight:700;}" +
".msg-a{color:#e2e8f0;line-height:1.4;padding-bottom:6px;border-bottom:1px solid #0f172a;}" +
"</style></head><body><div class='wrap'>" +
"<div class='hdr'><div><div class='title'>GENESIS GPT-4o OMNI</div><div class='sub'>Full ChatGPT + Live Sat &bull; " + staIp + "</div></div><div style='display:flex;gap:6px'><button class='abtn' style='padding:6px 8px;border-color:#10b981;color:#10b981' onclick='newChat()'>NEW CHAT</button><button class='abtn' style='padding:6px 8px' onclick='tapKey(33)'>ROTATE</button></div></div>" +
"<div class='scr'>" +
"  <div class='qbox' id='dq'>ASK &gt; " + sanitizeAscii(lastPrompt) + "</div>" +
"  <div class='abox' id='da'>" + sanitizeAscii(lastAnswer) + "</div>" +
"</div>" +
"<form id='askF' class='inp-row'>" +
"  <input type='text' id='qInp' class='inp' placeholder='Ask anything like ChatGPT (Code, Science, Math, World)...' autocomplete='off'>" +
"  <button type='button' id='micBtn' class='mbtn' onclick='startVoice()' title='Voice Input'>MIC</button>" +
"  <button type='submit' id='sBtn' class='sbtn'>ASK GPT</button>" +
"</form>" +
"<div class='kb' id='kbGrid'></div>" +
"<div class='chips'>" +
"  <span class='chip' onclick='qAsk(\"What can you do?\")'>What can you do?</span>" +
"  <span class='chip' onclick='qAsk(\"Give me live satellite telemetry and ISS position\")'>Live Satellite ISS</span>" +
"  <span class='chip' onclick='qAsk(\"How does AI work?\")'>How does AI work?</span>" +
"  <span class='chip' onclick='qAsk(\"Write a Python function to check prime numbers\")'>Python Code</span>" +
"  <span class='chip' onclick='qAsk(\"Tell me an amazing science fact\")'>Science Fact</span>" +
"  <span class='chip' onclick='qAsk(\"Calculate 48 * 25 + 120\")'>Math Solver</span>" +
"</div>" +
"<div class='log' id='chatLog'><div class='msg-u'>You: " + sanitizeAscii(lastPrompt) + "</div><div class='msg-a'>GENESIS GPT: " + sanitizeAscii(lastAnswer) + "</div></div>" +
"</div><script>" +
"const OR_KEY='" + openRouterApiKey + "';" +
"const keys=['Q','W','E','R','T','Y','U','I','O','P','A','S','D','F','G','H','J','K','L','?','Z','X','C','V','B','N','M','SPC','DEL','CLR'];" +
"const kb=document.getElementById('kbGrid'),dq=document.getElementById('dq'),da=document.getElementById('da'),inp=document.getElementById('qInp'),f=document.getElementById('askF'),cLog=document.getElementById('chatLog');" +
"let lastBridgedQ='',chatHist=[];" +
"function appendChat(q,a){if(!q||!a)return;chatHist.push({role:'user',content:q},{role:'assistant',content:a});if(chatHist.length>6)chatHist=chatHist.slice(-6);const d=document.createElement('div');d.innerHTML=`<div class='msg-u'>You: ${q}</div><div class='msg-a'>GENESIS GPT: ${a}</div>`;cLog.prepend(d);}" +
"async function newChat(){chatHist=[];cLog.innerHTML='';qAsk('reset');}" +
"function startVoice(){const SR=window.SpeechRecognition||window.webkitSpeechRecognition;if(!SR){alert('Voice input requires Chrome/Edge/Safari.');return;}const rec=new SR();rec.lang='en-US';rec.onresult=(e)=>{const t=e.results[0][0].transcript;if(t)qAsk(t);};rec.start();}" +
"keys.forEach((k,i)=>{const b=document.createElement('div');b.className='k';b.innerText=k;b.onclick=()=>tapKey(i);kb.appendChild(b);});" +
"const act=document.createElement('div');act.className='act';" +
"[['ASK AI',30,'#10b981'],['SPACE',31,'#00f0ff'],['SEND >',32,'#fbbf24'],['ROTATE',33,'#f472b6']].forEach(([l,idx,c])=>{" +
"  const b=document.createElement('div');b.className='abtn';b.style.borderColor=c;b.style.color=c;b.innerText=l;b.onclick=()=>tapKey(idx);act.appendChild(b);" +
"});kb.appendChild(act);" +
"async function browserDirectAI(q){" +
"  const lq=q.toLowerCase();" +
"  if(lq.includes('satellite')||lq.includes('iss')||lq.includes('orbit')||lq.includes('norad')){" +
"    try{const sr=await fetch('https://api.wheretheiss.at/v1/satellites/25544');if(sr.ok){const sd=await sr.json();const lat=Math.abs(sd.latitude).toFixed(2)+(sd.latitude>=0?'N':'S');const lon=Math.abs(sd.longitude).toFixed(2)+(sd.longitude>=0?'E':'W');return `LIVE SATELLITE [ISS NORAD-25544]: Pos ${lat}, ${lon} | Alt ${sd.altitude.toFixed(1)}km | Speed ${sd.velocity.toFixed(0)}km/h | Orbit: ${String(sd.visibility).toUpperCase()}`;}}catch(e){}" +
"  }" +
"  try{" +
"    const msgs=[{role:'system',content:'You are GENESIS GPT-4o OMNI, an omniscient ChatGPT-class AI assistant created by Ishit Jain. Answer any question on science, coding, math, history, translations, stories, or advice accurately in plain ASCII under 50 words without markdown or asterisks. Current Time: '+new Date().toLocaleString()}].concat(chatHist).concat([{role:'user',content:q}]);" +
"    const orr=await fetch('https://openrouter.ai/api/v1/chat/completions',{method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer '+OR_KEY},body:JSON.stringify({models:['nvidia/nemotron-3-ultra-550b-a55b:free','liquid/lfm-2.5-2.6b:free','openrouter/free'],reasoning:{exclude:true},messages:msgs})});" +
"    if(orr.ok){const ord=await orr.json();const txt=(ord.choices&&ord.choices[0]&&ord.choices[0].message&&ord.choices[0].message.content)||'';if(txt.trim().length>2)return txt.trim().replace(/[*#`]/g,'');}" +
"  }catch(e){}" +
"  try{" +
"    const wr=await fetch('https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch='+encodeURIComponent(q)+'&format=json&origin=*&srlimit=1');" +
"    if(wr.ok){const wd=await wr.json();const t=wd.query&&wd.query.search&&wd.query.search[0]&&wd.query.search[0].title;if(t){const sr=await fetch('https://en.wikipedia.org/api/rest_v1/page/summary/'+encodeURIComponent(t));if(sr.ok){const sd=await sr.json();if(sd.extract)return sd.extract.slice(0,240);}}}" +
"  }catch(e){}" +
"  return '';" +
"}" +
"async function bridgeMobileNet(q){" +
"  if(!q||q===lastBridgedQ)return;lastBridgedQ=q;" +
"  const bAns=await browserDirectAI(q);" +
"  if(bAns){da.innerText=bAns;appendChat(q,bAns);try{await fetch('/push_answer?q='+encodeURIComponent(q)+'&a='+encodeURIComponent(bAns)+'&src=mobile_net');}catch(e){}}" +
"}" +
"async function tapKey(idx){" +
"  const curText=(dq.innerText||'').replace('ASK > ','').replace('_','').trim();" +
"  const r=await fetch('/key?idx='+idx);const d=await r.json();" +
"  if(d.prompt!==undefined)dq.innerText='ASK > '+(d.prompt||'_');" +
"  if(idx===30||idx===32){da.innerText='Synthesizing GPT response...';if(curText.length>1)bridgeMobileNet(curText);setTimeout(syncStat,1000);setTimeout(syncStat,2500);setTimeout(syncStat,4500);}" +
"}" +
"async function syncStat(){try{const r=await fetch('/status');const d=await r.json();if(d.typing&&d.typing.length>0){dq.innerText='ASK > '+d.typing;}else{dq.innerText='ASK > '+d.question;}if(d.busy&&d.question&&d.question!==lastBridgedQ){bridgeMobileNet(d.question);}if(d.answer&&d.answer!=='Synthesizing answer...')da.innerText=d.answer;}catch(e){}}" +
"setInterval(syncStat,1800);" +
"function qAsk(t){inp.value=t;f.dispatchEvent(new Event('submit'));}" +
"f.onsubmit=async(e)=>{e.preventDefault();const q=inp.value.trim();if(!q)return;dq.innerText='ASK > '+q;da.innerText='Synthesizing GPT response...';inp.value='';" +
"let cloudWon=false;" +
"browserDirectAI(q).then(async(bAns)=>{if(bAns){cloudWon=true;lastBridgedQ=q;da.innerText=bAns;appendChat(q,bAns);try{await fetch('/push_answer?q='+encodeURIComponent(q)+'&a='+encodeURIComponent(bAns)+'&src=mobile_net');}catch(e){}}});" +
"try{const r=await fetch('/ask?q='+encodeURIComponent(q));const d=await r.json();if(!cloudWon&&d.answer&&!d.answer.includes('Synthesizing')){dq.innerText='ASK > '+d.question;da.innerText=d.answer;appendChat(d.question,d.answer);}}catch(e){}};" +
"</script></body></html>";
    webServer.send(200, "text/html", html);
}

void handleAsk() {
    if (!webServer.hasArg("q")) {
        webServer.send(400, "text/plain", "Missing q parameter");
        return;
    }
    String q = webServer.arg("q");
    // Always execute on Task_AI (which has a 24KB stack for mbedTLS!) and wait for exact sequence completion!
    uint32_t targetSeq = queuedQuerySeq + 1;
    enqueueAIQuery(q);
    unsigned long t0 = millis();
    while ((completedQuerySeq < targetSeq || aiBusy) && (millis() - t0 < 22000)) {
        vTaskDelay(pdMS_TO_TICKS(60));
    }

    JsonDocument doc;
    doc["status"]   = "ok";
    doc["question"] = sanitizeAscii(lastPrompt);
    doc["answer"]   = sanitizeAscii(lastAnswer);
    doc["source"]   = lastAISource;
    doc["ram_kb"]   = ESP.getFreeHeap() / 1024;
    String out;
    serializeJson(doc, out);
    webServer.send(200, "application/json", out);
}

void handleStatus() {
    JsonDocument doc;
    doc["status"]   = "online";
    doc["busy"]     = aiBusy;
    doc["question"] = sanitizeAscii(lastPrompt);
    doc["answer"]   = sanitizeAscii(lastAnswer);
    doc["typing"]   = typingBuffer;
    doc["kb_idx"]   = kbSelectedIndex;
    doc["queries"]  = totalQueries;
    doc["ram_kb"]   = ESP.getFreeHeap() / 1024;
    String out;
    serializeJson(doc, out);
    webServer.send(200, "application/json", out);
}

// ==============================================================================
// 9. FREERTOS MULTITASKING ENGINE
// ==============================================================================
void taskWiFiManager(void* pvParameters) {
    unsigned long lastCheck = 0;
    bool wasConnected = (WiFi.status() == WL_CONNECTED);
    for (;;) {
        ArduinoOTA.handle();
        bool nowConnected = (WiFi.status() == WL_CONNECTED);
        if (nowConnected && !wasConnected) {
            wasConnected = true;
            Serial.printf("[WiFi] Connected to %s | IP: %s\n", WIFI_SSID, WiFi.localIP().toString().c_str());
        } else if (!nowConnected && wasConnected) {
            wasConnected = false;
        }
        // If a mobile phone is connected to ESP32-C5-AI (192.168.4.1) while hotspot is off,
        // lock the radio onto the SoftAP channel (no channel hopping) so 192.168.4.1 never drops!
        if (WiFi.softAPgetStationNum() > 0 && !nowConnected) {
            WiFi.setAutoReconnect(false);
        } else if (WiFi.softAPgetStationNum() == 0 && !nowConnected) {
            WiFi.setAutoReconnect(true);
            if (millis() - lastCheck > 20000) {
                lastCheck = millis();
                WiFi.reconnect();
            }
        }
        vTaskDelay(pdMS_TO_TICKS(250));
    }
}

void taskAICommunication(void* pvParameters) {
    AIRequest req;
    for (;;) {
        if (aiQueue && xQueueReceive(aiQueue, &req, pdMS_TO_TICKS(100)) == pdTRUE) {
            askGenesisAI(String(req.prompt));
            completedQuerySeq++;
            aiBusy = (uxQueueMessagesWaiting(aiQueue) > 0);
        }
        vTaskDelay(pdMS_TO_TICKS(20));
    }
}

// Configure a pin for Open-Drain Sub-Nanosecond Capacitive Screen/Hand Sensing
inline void setupHandTouchPin(uint8_t pin) {
    gpio_num_t gp = (gpio_num_t)pin;
    gpio_reset_pin(gp);
    gpio_set_direction(gp, GPIO_MODE_INPUT_OUTPUT_OD);
    gpio_set_pull_mode(gp, GPIO_PULLUP_ONLY);
    gpio_set_level(gp, 1);
}

// Measures 128 sub-microsecond RC rise curves (1 pF ~= 150 counts!) for Through-Glass & Hand Sensing
inline int measurePinTouchCycles(uint8_t pin, int pulses = 128) {
    gpio_num_t gp = (gpio_num_t)pin;
    if (gpio_get_level(gp) == 0) return 50000; // Direct GND / Button press

    int total = 0;
    for (int s = 0; s < pulses; s++) {
        gpio_set_level(gp, 0);
        ets_delay_us(2);

        portDISABLE_INTERRUPTS();
        gpio_set_level(gp, 1);
        int c = 0;
        while (gpio_get_level(gp) == 0 && c < 300) {
            c++;
        }
        portENABLE_INTERRUPTS();
        total += c;
    }
    return total;
}

void drawTouchBadge(bool handActive) {
    if (!screenReady) return;
    if (spiMutex && xSemaphoreTake(spiMutex, pdMS_TO_TICKS(40)) != pdTRUE) return;
    int W = tft.width();
    tft.setTextWrap(false);
    tft.setTextSize(1);
    tft.fillRect(W - 58, 2, 56, 9, 0x0085);
    tft.setCursor(W - 56, 2);
    if (handActive) {
        tft.setTextColor(0xFFE0);
        tft.print("[TOUCH!] ");
    } else {
        tft.setTextColor(0x07E0);
        tft.print("TOUCH ON ");
    }
    if (spiMutex) xSemaphoreGive(spiMutex);
}

int findKeyIndexForChar(char c) {
    if (c >= 'a' && c <= 'z') c = c - 32;
    for (int i = 0; i < 27; i++) {
        if (KB_LABELS[i][0] == c) return i;
    }
    if (c == ' ') return 27;
    return -1;
}

void taskTouchHandling(void* pvParameters) {
    // Dedicated rock-solid Physical BOOT Button (GPIO 28)
    // Floating unconnected pins are disabled so Wi-Fi RF bursts never phantom-type random letters!
    pinMode(28, INPUT_PULLUP);

    bool bootWasPressed = false;
    unsigned long bootDownMs = 0;
    bool bootSentOnHold = false;

    for (;;) {
        bool bootLow = (digitalRead(28) == LOW);

        if (bootLow && !bootWasPressed) {
            bootWasPressed = true;
            bootSentOnHold = false;
            bootDownMs = millis();
            rgbLedWrite(RGB_BUILTIN, 0, 220, 255); // Cyan LED = Button Down
            drawTouchBadge(true);
        } else if (bootLow && bootWasPressed) {
            unsigned long heldMs = millis() - bootDownMs;

            // Visual feedback at 250ms that releasing now will TYPE the highlighted key
            if (heldMs >= 250 && heldMs < 750 && !bootSentOnHold && !aiBusy) {
                rgbLedWrite(RGB_BUILTIN, 0, 255, 60); // Green LED = Release now to Type Key
            }

            // Hold >= 750ms -> IMMEDIATELY SEND / ASK AI (without typing a stray letter first!)
            if (heldMs >= 750 && !bootSentOnHold && !aiBusy) {
                bootSentOnHold = true;
                rgbLedWrite(RGB_BUILTIN, 255, 180, 0); // Gold LED = Sending to GENESIS AI!
                flashKeyTyped(32);
                pressKeyboardKey(32); // Trigger [SEND >]
            }
        } else if (!bootLow && bootWasPressed) {
            unsigned long heldMs = millis() - bootDownMs;
            bootWasPressed = false;
            rgbLedWrite(RGB_BUILTIN, 0, 0, 0);
            drawTouchBadge(false);

            if (!bootSentOnHold && !aiBusy) {
                if (heldMs >= 250 && heldMs < 750) {
                    // Medium Press (250ms..750ms) -> TYPE the highlighted key into ASK >
                    liveTypingMode = true;
                    flashKeyTyped(kbSelectedIndex);
                    pressKeyboardKey(kbSelectedIndex);
                    vTaskDelay(pdMS_TO_TICKS(80));
                    updateKeyboardHighlight(kbSelectedIndex, kbSelectedIndex);
                    Serial.printf("[BOOT TYPE] Typed Key #%d: [%s]\n", kbSelectedIndex, KB_LABELS[kbSelectedIndex]);
                } else if (heldMs >= 15 && heldMs < 250) {
                    // Short Click (< 250ms) -> Move highlight to NEXT key on keyboard!
                    liveTypingMode = true;
                    int oldIdx = kbSelectedIndex;
                    kbSelectedIndex = (kbSelectedIndex + 1) % 34;
                    updateKeyboardHighlight(oldIdx, kbSelectedIndex);
                    Serial.printf("[BOOT CLICK] Selected Key #%d: [%s]\n", kbSelectedIndex, KB_LABELS[kbSelectedIndex]);
                }
            }
            vTaskDelay(pdMS_TO_TICKS(25));
        }

        vTaskDelay(pdMS_TO_TICKS(12));
    }
}

void taskSystemMonitor(void* pvParameters) {
    for (;;) {
        updateLedFlicker(aiBusy);
        vTaskDelay(pdMS_TO_TICKS(90));
    }
}

// ==============================================================================
// 10. SYSTEM SETUP & INITIALIZATION
// ==============================================================================
void setup() {
    Serial.begin(115200);
    delay(300);

    pinMode(TFT_BL, OUTPUT);
    digitalWrite(TFT_BL, HIGH);

    for (int i = 0; i < 6; i++) {
        rgbLedWrite(RGB_BUILTIN, (i % 2) * 120, 120, (i % 2) * 60);
        delay(50);
    }

    Serial.println("\n============================================================");
    Serial.println("  GENESIS GPT-4o OMNI - 320x240 FULL LANDSCAPE + KEYBOARD");
    Serial.println("============================================================");

    WiFi.mode(WIFI_AP_STA);
    WiFi.setSleep(false); // Disable Wi-Fi modem sleep for 0ms packet latency!
    WiFi.softAP(AP_SSID, AP_PASSWORD);
    // Disable DHCP Default Router (Option 3) & DNS (Option 6) on ESP32-C5-AI so mobile phones keep 4G/5G Mobile Data active!
    esp_netif_t* ap_netif = WiFi.AP.netif();
    if (ap_netif) {
        esp_netif_dhcps_stop(ap_netif);
        dhcps_offer_t offer_router = 0;
        dhcps_offer_t offer_dns = 0;
        esp_netif_dhcps_option(ap_netif, ESP_NETIF_OP_SET, ESP_NETIF_ROUTER_SOLICITATION_ADDRESS, &offer_router, sizeof(offer_router));
        esp_netif_dhcps_option(ap_netif, ESP_NETIF_OP_SET, ESP_NETIF_DOMAIN_NAME_SERVER, &offer_dns, sizeof(offer_dns));
        esp_netif_dhcps_start(ap_netif);
    }

    initMemoryEngine();
    webServer.on("/", handleRoot);
    webServer.on("/ask", handleAsk);
    webServer.on("/status", handleStatus);
    webServer.on("/push_answer", [](){
        if (webServer.hasArg("q") && webServer.hasArg("a")) {
            lastPrompt = sanitizeAscii(webServer.arg("q"));
            lastAnswer = sanitizeAscii(webServer.arg("a"));
            lastAISource = webServer.hasArg("src") ? webServer.arg("src") : "cloud_gpt";
            typingBuffer = "";
            liveTypingMode = false;
            browserPushedAnswer = true;
            aiBusy = false;
            completedQuerySeq = queuedQuerySeq;
            if (nvsReady) {
                prefs.putString("lastQ", lastPrompt);
                prefs.putString("lastA", lastAnswer);
            }
            drawGenesisHUD("GENESIS GPT");
        }
        webServer.send(200, "application/json", "{\"status\":\"ok\"}");
    });
    webServer.on("/clear_memory", [](){
        clearAllKnowledge();
        webServer.send(200, "application/json", "{\"status\":\"cleared\"}");
    });
    webServer.on("/key", [](){
        if (webServer.hasArg("idx")) {
            int idx = webServer.arg("idx").toInt();
            int oldIdx = kbSelectedIndex;
            kbSelectedIndex = constrain(idx, 0, 33);
            updateKeyboardHighlight(oldIdx, kbSelectedIndex);
            pressKeyboardKey(kbSelectedIndex);
        }
        webServer.send(200, "application/json", "{\"prompt\":\"" + typingBuffer + "\",\"answer\":\"" + sanitizeAscii(lastAnswer) + "\"}");
    });
    webServer.on("/rotate", [](){
        toggleRotation();
        webServer.send(200, "application/json", "{\"rotation\":" + String(currentRotation) + "}");
    });
    webServer.enableCORS(true);
    webServer.begin();
    MDNS.begin("genesis");

    spiMutex = xSemaphoreCreateMutex();
    aiQueue  = xQueueCreate(6, sizeof(AIRequest));
    if (prefs.begin("genesis_ai", false)) {
        nvsReady     = true;
        totalQueries = prefs.getUInt("qCount", 1);
    }

    // Initialize SPI & 2.4" Display -> TFT_RST (Pin 2) resets and stays HIGH (3.3V) so screen stays ON!
    SPI.begin(TFT_SCK, -1, TFT_MOSI); // Free Pin 9 (MISO/SDO wire) for T_CLK Touchscreen!
    tft.begin();
    tft.purgeAllGRAM();
    currentRotation = 0;
    screenReady = true;

    initTouchEngine();
    touchReady = true;

    drawGenesisHUD("GENESIS GPT");

    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    int attempts = 0;
    WiFi.setAutoReconnect(true);
    while (WiFi.status() != WL_CONNECTED && attempts < 30) {
        updateLedFlicker(false);
        webServer.handleClient();
        delay(150);
        attempts++;
    }

    ArduinoOTA.setHostname("ESP32-C5-GENESIS-AI");
    ArduinoOTA.begin();

    xTaskCreate(taskWiFiManager,     "Task_WiFi",    4096, NULL, 1, NULL);
    xTaskCreate(taskAICommunication, "Task_AI",      24576, NULL, 1, NULL);
    xTaskCreate(taskTouchHandling,   "Task_Touch",   3072, NULL, 1, NULL);
    xTaskCreate(taskSystemMonitor,   "Task_Monitor", 2048, NULL, 1, NULL);

    drawGenesisHUD("GENESIS GPT");
    Serial.println(">>> GENESIS GPT-4o OMNI ONLINE AND READY!");
}

// ==============================================================================
// 11. MAIN LOOP
// ==============================================================================
void loop() {
    updateLedFlicker(aiBusy);
    webServer.handleClient();

    if (!aiBusy && Serial.available()) {
        bool shouldSend = false;
        int lastKeyIdx = kbSelectedIndex;
        while (Serial.available()) {
            char c = (char)Serial.read();
            if (c == '\n' || c == '\r') {
                if (typingBuffer.length() > 0) {
                    shouldSend = true;
                }
            } else if (c == 8 || c == 127) { // Backspace
                if (typingBuffer.length() > 0) {
                    typingBuffer.remove(typingBuffer.length() - 1);
                }
                lastKeyIdx = 28; // [DEL]
                liveTypingMode = true;
            } else if (c >= 32 && c <= 126) {
                typingBuffer += c;
                int kIdx = findKeyIndexForChar(c);
                if (kIdx >= 0) lastKeyIdx = kIdx;
                liveTypingMode = true;
            }
        }
        int oldIdx = kbSelectedIndex;
        kbSelectedIndex = lastKeyIdx;
        updateKeyboardHighlight(oldIdx, kbSelectedIndex);

        if (shouldSend && typingBuffer.length() > 0) {
            String q = typingBuffer;
            typingBuffer = "";
            flashKeyTyped(32);
            enqueueAIQuery(q);
        }
    }
    delay(5);
}
