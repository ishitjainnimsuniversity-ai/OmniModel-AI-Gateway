// GENESIS AI Display Module for Portable SoftAP Architecture.
// 2.4" ILI9341 SPI TFT (320x240 landscape). Display-only: ZERO touch code.
#pragma once
#include <Arduino.h>
#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ILI9341.h>
#include <math.h>
#include "config.h"

class GenesisTFT : public Adafruit_ILI9341 {
public:
    GenesisTFT(int8_t cs, int8_t dc, int8_t rst) : Adafruit_ILI9341(cs, dc, rst) {}
    void applyPanelRotation(uint8_t r) {
        r = r % 4;
        Adafruit_ILI9341::setRotation(r);
        if (r % 2 == 0) { _width = 320; _height = 240; } else { _width = 240; _height = 320; }
        setTextWrap(false);
    }
    void purgeAllGRAM() {
        for (uint8_t r = 0; r < 4; r++) { applyPanelRotation(r); fillScreen(ILI9341_BLACK); }
        applyPanelRotation(0);
    }
};

extern GenesisTFT tft;

constexpr uint16_t rgb565(uint8_t r, uint8_t g, uint8_t b) {
    return (uint16_t)(((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3));
}

namespace Col {
constexpr uint16_t BG    = rgb565(5, 11, 24);
constexpr uint16_t PANEL = rgb565(11, 20, 38);
constexpr uint16_t LINE  = rgb565(24, 48, 79);
constexpr uint16_t CYAN  = rgb565(34, 211, 238);
constexpr uint16_t BLUE  = rgb565(59, 130, 246);
constexpr uint16_t TEXT  = rgb565(230, 241, 255);
constexpr uint16_t DIM   = rgb565(125, 147, 178);
constexpr uint16_t OK    = rgb565(52, 211, 153);
constexpr uint16_t WARN  = rgb565(251, 191, 36);
constexpr uint16_t BAD   = rgb565(248, 113, 113);
}

#define CHAT_COLS      26
#define CHAT_ROWS      9
#define ANS_Y0         54
#define ANS_LINE_H     17
#define BAR_H          24
#define BOTTOM_Y       216

static void textCenter(const String& s, int cx, int y, uint8_t size, uint16_t color) {
    int16_t w = s.length() * 6 * size;
    tft.setTextSize(size);
    tft.setTextColor(color);
    tft.setCursor(cx - w / 2, y);
    tft.print(s);
}

static void ellipsePoint(int cx, int cy, float a, float b, float rotDeg, float t, int& x, int& y) {
    float ph = rotDeg * (float)M_PI / 180.0f;
    float ct = cosf(t), st = sinf(t), cp = cosf(ph), sp = sinf(ph);
    x = cx + (int)lroundf(a * ct * cp - b * st * sp);
    y = cy + (int)lroundf(a * ct * sp + b * st * cp);
}

static void ellipseArc(int cx, int cy, float a, float b, float rot, float t0, float t1,
                       int steps, uint16_t color, int delayMs, bool thick) {
    int px, py, x, y;
    ellipsePoint(cx, cy, a, b, rot, t0, px, py);
    for (int i = 1; i <= steps; i++) {
        float t = t0 + (t1 - t0) * i / steps;
        ellipsePoint(cx, cy, a, b, rot, t, x, y);
        tft.drawLine(px, py, x, y, color);
        if (thick) tft.drawLine(px + 1, py, x + 1, y, color);
        px = x; py = y;
        if (delayMs > 0) delay(delayMs);
    }
}

static void drawLogo(int cx, int cy, int R, bool animate) {
    const float TWO_PI_F = 6.2831853f;
    int steps = max(28, R);
    ellipseArc(cx, cy, R, R, 0, 0, TWO_PI_F, steps * 2, Col::CYAN, animate ? 5 : 0, true);
    ellipseArc(cx, cy, R, R * 0.38f, 35, 0, TWO_PI_F, steps * 2, Col::BLUE, animate ? 4 : 0, R > 20);
    ellipseArc(cx, cy, R, R * 0.38f, -35, 0, TWO_PI_F, steps * 2, Col::CYAN, animate ? 4 : 0, R > 20);
    int core = max(3, R / 5);
    if (animate) {
        for (int r = 1; r <= core; r++) { tft.fillCircle(cx, cy, r, Col::CYAN); delay(18); }
    } else {
        tft.fillCircle(cx, cy, core, Col::CYAN);
    }
    tft.fillCircle(cx, cy, max(1, core / 2), Col::TEXT);
    int x, y;
    ellipsePoint(cx, cy, R, R * 0.38f, 35, 0.9f, x, y);   tft.fillCircle(x, y, max(2, R / 14), Col::TEXT);
    ellipsePoint(cx, cy, R, R * 0.38f, -35, 3.9f, x, y);  tft.fillCircle(x, y, max(2, R / 14), Col::TEXT);
    ellipsePoint(cx, cy, R, R, 0, 5.2f, x, y);            tft.fillCircle(x, y, max(2, R / 14), Col::CYAN);
}

// ------------------------------------------------------------------------- SCREEN 1: BOOT
static void screenBoot() {
    tft.fillScreen(Col::BG);
    drawLogo(160, 82, 54, true);
    const char* title = "GENESIS AI";
    int tw = 10 * 18, x0 = 160 - tw / 2, y0 = 152;
    tft.setTextSize(3);
    for (int i = 0; title[i]; i++) {
        tft.setTextColor(Col::TEXT);
        tft.setCursor(x0 + i * 18, y0);
        tft.print(title[i]);
        delay(50);
    }
    for (int w = 4; w <= 150; w += 6) {
        tft.drawFastHLine(160 - w, 182, w * 2, Col::CYAN);
        tft.drawFastHLine(160 - w, 183, w * 2, Col::BLUE);
        delay(6);
    }
    textCenter("PORTABLE PHONE-POWERED AI", 160, 194, 1, Col::DIM);
    textCenter("ESP32-C5  |  CELLULAR RELAY", 160, 222, 1, Col::LINE);
    delay(400);
}

// ------------------------------------------------------------------ SCREEN 2: INITIALIZATION
#define INIT_ROWS 5
static const char* INIT_LABELS[INIT_ROWS] = {"ESP32-C5", "SoftAP", "DHCP/DNS", "Web Server", "Clients"};
static const int INIT_Y0 = 36, INIT_H = 40;

static void screenInitDraw() {
    tft.fillScreen(Col::BG);
    tft.fillRect(0, 0, 320, 28, Col::PANEL);
    tft.drawFastHLine(0, 28, 320, Col::LINE);
    drawLogo(16, 14, 9, false);
    tft.setTextSize(2); tft.setTextColor(Col::CYAN); tft.setCursor(34, 6); tft.print("GENESIS AI");
    tft.setTextSize(1); tft.setTextColor(Col::DIM); tft.setCursor(188, 10); tft.print("STANDALONE");
    for (int i = 0; i < INIT_ROWS; i++) {
        int y = INIT_Y0 + i * INIT_H;
        tft.setTextSize(2); tft.setTextColor(Col::TEXT); tft.setCursor(8, y); tft.print(INIT_LABELS[i]);
        tft.drawFastHLine(8, y + INIT_H - 6, 304, Col::PANEL);
    }
}

static void screenInitRow(int i, const char* status, uint16_t color, const String& detail) {
    int y = INIT_Y0 + i * INIT_H;
    tft.fillRect(180, y, 140, 17, Col::BG);
    tft.setTextSize(2); tft.setTextColor(color);
    int w = strlen(status) * 12;
    tft.setCursor(312 - w, y); tft.print(status);
    tft.fillRect(8, y + 19, 304, 10, Col::BG);
    tft.setTextSize(1); tft.setTextColor(color == Col::BAD ? Col::BAD : Col::DIM);
    tft.setCursor(8, y + 20);
    String d = detail;
    if (d.length() > 51) d = d.substring(0, 50) + ".";
    tft.print(d);
}

static void screenInitFooter(const String& msg, uint16_t color) {
    tft.fillRect(0, 232, 320, 8, Col::BG);
    tft.setTextSize(1); tft.setTextColor(color);
    tft.setCursor(8, 232); tft.print(msg);
}

// ------------------------------------------------------------------------- SCREEN 3: READY
static void screenReady(const String& ssid, const String& ip) {
    tft.fillScreen(Col::BG);
    drawLogo(160, 50, 30, false);
    textCenter("GENESIS AI", 160, 92, 3, Col::TEXT);

    tft.fillCircle(80, 126, 6, Col::CYAN);
    tft.setTextSize(2); tft.setTextColor(Col::CYAN); tft.setCursor(96, 120); tft.print("PORTABLE AP");

    textCenter(String("Wi-Fi: ") + ssid, 160, 150, 2, Col::TEXT);
    textCenter(String("Open: http://") + ip, 160, 174, 2, Col::OK);
    textCenter("Connect phone to start chat", 160, 206, 1, Col::DIM);
}

// ------------------------------------------------------------------ SCREEN 4: CHAT INTERFACE
static void chatDrawChrome() {
    tft.fillScreen(Col::BG);
    tft.fillRect(0, 0, 320, BAR_H, Col::PANEL);
    tft.drawFastHLine(0, BAR_H, 320, Col::LINE);
    drawLogo(14, 12, 8, false);
    tft.setTextSize(2); tft.setTextColor(Col::CYAN); tft.setCursor(30, 4); tft.print("GENESIS AI");
    tft.fillRect(0, BOTTOM_Y, 320, 24, Col::PANEL);
    tft.drawFastHLine(0, BOTTOM_Y, 320, Col::LINE);
}

static void chatTopBar(const String& label, uint16_t labelColor, uint16_t dotColor, int clients) {
    tft.fillRect(130, 1, 190, BAR_H - 1, Col::PANEL);
    tft.setTextSize(1); tft.setTextColor(Col::DIM);
    tft.setCursor(140, 8);
    tft.printf("AP:%d", clients);

    tft.setTextColor(labelColor);
    int w = label.length() * 6;
    tft.setCursor(290 - w, 8);
    tft.print(label);
    tft.fillCircle(306, 12, 5, dotColor);
}

static void chatBottom(const String& text, uint16_t color) {
    tft.fillRect(0, BOTTOM_Y + 1, 320, 23, Col::PANEL);
    tft.setTextSize(1); tft.setTextColor(color);
    String t = text; if (t.length() > 52) t = t.substring(0, 51) + ".";
    tft.setCursor(6, BOTTOM_Y + 8); tft.print(t);
}

static void chatClearBody() { tft.fillRect(0, BAR_H + 1, 320, BOTTOM_Y - BAR_H - 1, Col::BG); }
static void chatClearAnswer() { tft.fillRect(0, ANS_Y0 - 2, 320, BOTTOM_Y - ANS_Y0 + 1, Col::BG); }

// ------------------------------------------------------------- CINEMATIC QUANTUM REACTOR
static void drawCinematicReactor(int cx, int cy, uint8_t frame) {
    tft.fillRect(cx - 48, cy - 48, 96, 96, Col::BG);

    const float TWO_PI_F = 6.2831853f;
    float rot1 = (frame % 36) * (TWO_PI_F / 36.0f);
    float rot2 = -((frame * 2) % 36) * (TWO_PI_F / 36.0f);

    // 1. Outer Sci-Fi Brackets (4 curved tech arc segments)
    int rOuter = 44;
    for (int b = 0; b < 4; b++) {
        float baseA = b * (TWO_PI_F / 4.0f) + (frame % 72) * (TWO_PI_F / 144.0f);
        for (int step = 0; step < 7; step++) {
            float a = baseA + step * 0.08f;
            int x = cx + (int)lroundf(rOuter * cosf(a));
            int y = cy + (int)lroundf(rOuter * sinf(a));
            tft.drawPixel(x, y, Col::CYAN);
            tft.drawPixel(x + 1, y, Col::BLUE);
        }
    }

    // 2. Middle Rotating Gear/Spokes Ring (8 radial ticks)
    int r1 = 30, r2 = 38;
    for (int i = 0; i < 8; i++) {
        float a = rot1 + i * (TWO_PI_F / 8.0f);
        float ca = cosf(a), sa = sinf(a);
        int x1 = cx + (int)lroundf(r1 * ca);
        int y1 = cy + (int)lroundf(r1 * sa);
        int x2 = cx + (int)lroundf(r2 * ca);
        int y2 = cy + (int)lroundf(r2 * sa);
        tft.drawLine(x1, y1, x2, y2, (i % 2 == 0) ? Col::CYAN : Col::BLUE);
    }

    // 3. Middle Static Circular Rails
    tft.drawCircle(cx, cy, 29, Col::LINE);
    tft.drawCircle(cx, cy, 22, Col::PANEL);
    tft.drawCircle(cx, cy, 21, Col::LINE);

    // 4. Inner Counter-Rotating Orbiting Nodes (4 energy nodes)
    int rOrbit = 17;
    for (int j = 0; j < 4; j++) {
        float a = rot2 + j * (TWO_PI_F / 4.0f);
        int ox = cx + (int)lroundf(rOrbit * cosf(a));
        int oy = cy + (int)lroundf(rOrbit * sinf(a));
        tft.fillCircle(ox, oy, (j == 0) ? 3 : 2, (j == 0) ? Col::TEXT : Col::CYAN);
    }

    // 5. Central Pulsating Quantum Core (Iris)
    tft.drawCircle(cx, cy, 10, Col::BLUE);
    tft.drawCircle(cx, cy, 9, Col::CYAN);
    tft.fillCircle(cx, cy, 6, rgb565(15, 60, 110));
    tft.fillCircle(cx, cy, 3, Col::CYAN);
    tft.fillCircle(cx, cy, 1, Col::TEXT);
}

static void chatWelcome(const String& url, const String& staUrl = "") {
    chatClearBody();
    textCenter("GENESIS AI 5.0", 160, 32, 2, Col::CYAN);
    textCenter("SOVEREIGN QUANTUM BRAIN", 160, 52, 1, Col::DIM);

    drawCinematicReactor(160, 112, 0);

    textCenter("WIRELESS AI SYNC ONLINE", 160, 168, 1, Col::OK);
    if (staUrl.length() > 0 && staUrl != "0.0.0.0") {
        textCenter("IP: " + staUrl + "  (AP: " + url + ")", 160, 184, 1, Col::CYAN);
    } else {
        textCenter("AP: " + url + "  |  Wi-Fi Connected", 160, 184, 1, Col::CYAN);
    }
    textCenter("Mirroring Laptop & Mobile Live", 160, 200, 1, Col::DIM);
}

static void chatQuestion(const String& q) {
    tft.fillRect(0, BAR_H + 1, 320, ANS_Y0 - BAR_H - 3, Col::BG);
    tft.fillRoundRect(4, BAR_H + 4, 312, 24, 5, Col::PANEL);
    tft.drawRoundRect(4, BAR_H + 4, 312, 24, 5, Col::LINE);
    tft.setTextSize(1); tft.setTextColor(Col::CYAN);
    tft.setCursor(9, BAR_H + 8); tft.print("YOU");
    tft.setTextColor(Col::TEXT);
    String l1 = q.substring(0, 47), l2 = q.length() > 47 ? q.substring(47, 94) : "";
    if (q.length() > 94) l2 = l2.substring(0, 44) + "...";
    tft.setCursor(33, BAR_H + 8); tft.print(l1);
    if (l2.length()) { tft.setCursor(33, BAR_H + 18); tft.print(l2); }
}

static void chatAnswer(const String& text, uint16_t color, bool animate) {
    chatClearAnswer();
    tft.setTextSize(2); tft.setTextColor(color);
    int line = 0, col = 0;
    tft.setCursor(4, ANS_Y0);
    for (unsigned i = 0; i < text.length() && line < CHAT_ROWS; i++) {
        char c = text[i];
        if (c == '\n') { line++; col = 0; tft.setCursor(4, ANS_Y0 + line * ANS_LINE_H); continue; }
        if (col >= CHAT_COLS) { line++; col = 0; if (line >= CHAT_ROWS) break; tft.setCursor(4, ANS_Y0 + line * ANS_LINE_H); }
        tft.print(c);
        col++;
        if (animate && c != ' ') delay(4);
    }
}

static void chatThinking(uint8_t frame, const String& label) {
    drawCinematicReactor(160, 112, frame);
    tft.fillRect(20, 168, 280, 40, Col::BG);
    textCenter(label, 160, 172, 2, Col::TEXT);
    textCenter("NEURAL MATRIX ACTIVE", 160, 196, 1, Col::CYAN);
}

// ------------------------------------------------------------------ SCREEN 5: IMAGE STUDIO
static void imageStudioFrame(const String& prompt, const String& style, const String& aspect, int x, int y, int w, int h) {
    chatClearBody();
    // Prompt header box
    tft.fillRoundRect(4, BAR_H + 3, 312, 22, 4, Col::PANEL);
    tft.drawRoundRect(4, BAR_H + 3, 312, 22, 4, Col::LINE);
    tft.setTextSize(1); tft.setTextColor(Col::CYAN);
    tft.setCursor(8, BAR_H + 8); tft.print("AI ART:");
    tft.setTextColor(Col::TEXT);
    tft.setCursor(54, BAR_H + 8);
    String p = prompt;
    if (p.length() > 42) p = p.substring(0, 41) + ".";
    tft.print(p);

    // Outer border around image thumbnail canvas
    tft.drawRoundRect(x - 2, y - 2, w + 4, h + 4, 3, Col::LINE);
    tft.drawRoundRect(x - 1, y - 1, w + 2, h + 2, 2, Col::CYAN);
    tft.fillRect(x, y, w, h, ILI9341_BLACK);

    // Style & aspect badge at bottom of body
    tft.fillRect(0, BOTTOM_Y - 14, 320, 13, Col::BG);
    tft.setTextSize(1); tft.setTextColor(Col::DIM);
    tft.setCursor(8, BOTTOM_Y - 12);
    tft.printf("%s  |  %s  |  Rendering...", style.c_str(), aspect.c_str());
}

static void displayImageChunk(int x, int y, int w, int h, const uint8_t* rawBytes, size_t len) {
    if (len < 2 || w <= 0 || h <= 0) return;
    tft.startWrite();
    tft.setAddrWindow(x, y, w, h);
    for (size_t i = 0; i + 1 < len; i += 2) {
        uint16_t col = ((uint16_t)rawBytes[i] << 8) | rawBytes[i + 1];
        tft.writeColor(col, 1);
    }
    tft.endWrite();
}

static void imageStudioFinish(const String& style, const String& aspect) {
    tft.fillRect(0, BOTTOM_Y - 14, 320, 13, Col::BG);
    tft.setTextSize(1); tft.setTextColor(Col::OK);
    tft.setCursor(8, BOTTOM_Y - 12);
    tft.printf("%s  |  %s  |  TFT Synced [OK]", style.c_str(), aspect.c_str());
}
