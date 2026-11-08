// GENESIS AI display module: boot logo, init checklist, ready screen, LLM-style chat UI.
// 2.4" ILI9341, 320x240 landscape. DISPLAY ONLY - there is intentionally NO touch code here:
// no XPT2046, no touch interrupt, no touch GPIO. GPIO 9 (SDO wire) is left unassigned.
#pragma once
#include <Arduino.h>
#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ILI9341.h>
#include <math.h>

// Existing wiring (unchanged): SCK=10 MOSI=8 CS=6 DC=7 RST=2 (RST stays HIGH after setup, never re-pulsed)
#define TFT_SCK   10
#define TFT_MOSI  8
#define TFT_CS    6
#define TFT_DC    7
#define TFT_RST   2

// Calibrated panel driver (same logic as the working firmware): 320x240 landscape, MADCTL 0x48.
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

// Chat layout constants (text size 2 = 12x16 px per char -> 26 columns x 9 rows)
#define CHAT_COLS      26
#define CHAT_ROWS      9
#define ANS_Y0         54
#define ANS_LINE_H     17
#define BAR_H          24
#define BOTTOM_Y       216

// ------------------------------------------------------------------ drawing helpers
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

// Polyline along an ellipse from t0..t1 (radians). delayMs>0 gives a draw-on animation.
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

// Full GENESIS logo: ring + two crossed orbits + glowing core (no bitmap, drawn with primitives).
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
    // three "satellites" on the orbits
    int x, y;
    ellipsePoint(cx, cy, R, R * 0.38f, 35, 0.9f, x, y);   tft.fillCircle(x, y, max(2, R / 14), Col::TEXT);
    ellipsePoint(cx, cy, R, R * 0.38f, -35, 3.9f, x, y);  tft.fillCircle(x, y, max(2, R / 14), Col::TEXT);
    ellipsePoint(cx, cy, R, R, 0, 5.2f, x, y);            tft.fillCircle(x, y, max(2, R / 14), Col::CYAN);
}

// ------------------------------------------------------------------------- SCREEN 1: BOOT
static void screenBoot() {
    tft.fillScreen(Col::BG);
    const int cx = 160, cy = 82, R = 54;
    drawLogo(cx, cy, R, true);
    // title, letter by letter
    const char* title = "GENESIS AI";
    int tw = 10 * 18, x0 = 160 - tw / 2, y0 = 152;
    tft.setTextSize(3);
    for (int i = 0; title[i]; i++) {
        tft.setTextColor(Col::TEXT);
        tft.setCursor(x0 + i * 18, y0);
        tft.print(title[i]);
        delay(55);
    }
    // underline grows from the centre
    for (int w = 4; w <= 150; w += 6) {
        tft.drawFastHLine(160 - w, 182, w * 2, Col::CYAN);
        tft.drawFastHLine(160 - w, 183, w * 2, Col::BLUE);
        delay(6);
    }
    textCenter("PERSONAL AI ASSISTANT", 160, 194, 1, Col::DIM);
    textCenter("ESP32-C5  |  CLOUD INTELLIGENCE", 160, 222, 1, Col::LINE);
    delay(500);
}

// ------------------------------------------------------------------ SCREEN 2: INITIALIZATION
#define INIT_ROWS 5
static const char* INIT_LABELS[INIT_ROWS] = {"ESP32-C5", "Wi-Fi", "Backend", "Local AI", "Cloud AI"};
static const int INIT_Y0 = 36, INIT_H = 40;

static void screenInitDraw() {
    tft.fillScreen(Col::BG);
    tft.fillRect(0, 0, 320, 28, Col::PANEL);
    tft.drawFastHLine(0, 28, 320, Col::LINE);
    drawLogo(16, 14, 9, false);
    tft.setTextSize(2); tft.setTextColor(Col::CYAN); tft.setCursor(34, 6); tft.print("GENESIS AI");
    tft.setTextSize(1); tft.setTextColor(Col::DIM); tft.setCursor(176, 10); tft.print("INITIALIZING");
    for (int i = 0; i < INIT_ROWS; i++) {
        int y = INIT_Y0 + i * INIT_H;
        tft.setTextSize(2); tft.setTextColor(Col::TEXT); tft.setCursor(8, y); tft.print(INIT_LABELS[i]);
        tft.drawFastHLine(8, y + INIT_H - 6, 304, Col::PANEL);
    }
}

// status: short word ("..", "OK", "FAIL", "WARN"); detail: one dim line (max ~51 chars at size 1).
static void screenInitRow(int i, const char* status, uint16_t color, const String& detail) {
    int y = INIT_Y0 + i * INIT_H;
    tft.fillRect(200, y, 120, 17, Col::BG);
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

static void screenInitSpin(int i, uint8_t frame) {
    static const char sp[] = "|/-\\";
    int y = INIT_Y0 + i * INIT_H;
    tft.fillRect(288, y, 24, 17, Col::BG);
    tft.setTextSize(2); tft.setTextColor(Col::CYAN);
    tft.setCursor(294, y); tft.print(sp[frame & 3]);
}

static void screenInitFooter(const String& msg, uint16_t color) {
    tft.fillRect(0, 232, 320, 8, Col::BG);
    tft.setTextSize(1); tft.setTextColor(color);
    tft.setCursor(8, 232); tft.print(msg);
}

// ------------------------------------------------------------------------- SCREEN 3: READY
static void screenReady(const String& brain, const String& provider, const String& model, bool isOnline) {
    tft.fillScreen(Col::BG);
    drawLogo(160, 58, 34, false);
    textCenter("GENESIS AI", 160, 104, 3, Col::TEXT);

    uint16_t dotCol = isOnline ? Col::OK : Col::CYAN;
    const char* modeText = isOnline ? "ONLINE MODE" : "OFFLINE MODE";

    tft.fillCircle(82, 142, 6, dotCol);
    tft.setTextSize(2); tft.setTextColor(dotCol); tft.setCursor(96, 136); tft.print(modeText);

    String m = model; if (m.length() > 24) m = m.substring(0, 24);
    String bTag = (brain == "LOCAL") ? "LOCAL: " : "CLOUD: ";
    textCenter(bTag + m, 160, 168, 2, Col::TEXT);

    if (isOnline) {
        textCenter("Dual Brain: Cloud + Local Ready", 160, 194, 1, Col::OK);
    } else {
        textCenter("Local Brain Active (No Internet)", 160, 194, 1, Col::CYAN);
    }
    textCenter("Ready to assist", 160, 214, 2, Col::DIM);
}

// ------------------------------------------------------------------ SCREEN 4: CHAT INTERFACE
static void chatWifiBars(int rssi, uint16_t color) {
    int level = rssi > -55 ? 4 : rssi > -65 ? 3 : rssi > -75 ? 2 : rssi > -85 ? 1 : 0;
    for (int i = 0; i < 4; i++) {
        int h = 3 + i * 3;
        tft.fillRect(262 + i * 5, 18 - h, 3, h, i < level ? color : Col::LINE);
    }
}

static void chatDrawChrome() {
    tft.fillScreen(Col::BG);
    tft.fillRect(0, 0, 320, BAR_H, Col::PANEL);
    tft.drawFastHLine(0, BAR_H, 320, Col::LINE);
    drawLogo(14, 12, 8, false);
    tft.setTextSize(2); tft.setTextColor(Col::CYAN); tft.setCursor(30, 4); tft.print("GENESIS AI");
    tft.fillRect(0, BOTTOM_Y, 320, 24, Col::PANEL);
    tft.drawFastHLine(0, BOTTOM_Y, 320, Col::LINE);
}

// state label right-aligned in the top bar; dot color indicates brain/connectivity
static void chatTopBar(const String& label, uint16_t labelColor, uint16_t dotColor, int rssi) {
    tft.fillRect(140, 1, 180, BAR_H - 1, Col::PANEL);
    tft.setTextSize(1); tft.setTextColor(labelColor);
    int w = label.length() * 6;
    tft.setCursor(256 - w, 8); tft.print(label);
    chatWifiBars(rssi, (dotColor != Col::BAD) ? Col::CYAN : Col::LINE);
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

static void chatWelcome(const String& url) {
    chatClearBody();
    drawLogo(160, 76, 28, false);
    textCenter("How can I help?", 160, 118, 2, Col::TEXT);
    textCenter("Ask from your phone:", 160, 146, 1, Col::DIM);
    textCenter(url, 160, 160, 1, Col::CYAN);
}

// "YOU" bubble with up to two lines of the question (51 chars per line at size 1).
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

// Draw one page of text (lines separated by '\n'); animate = typewriter reveal.
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
        if (animate && c != ' ') delay(5);
    }
}

// Thinking indicator: label + three bouncing dots, redrawn in a small region only.
static void chatThinking(uint8_t frame, const String& label) {
    const int y0 = 96;
    tft.fillRect(40, y0, 240, 60, Col::BG);
    textCenter(label, 160, y0, 2, Col::DIM);
    for (int i = 0; i < 3; i++) {
        int lift = ((frame + 3 - i) % 3 == 0) ? 8 : 0;
        tft.fillCircle(140 + i * 20, y0 + 40 - lift, 5, lift ? Col::CYAN : Col::LINE);
    }
}
