// GENESIS AI - ESP32-C5 firmware (display + network client).
// Boot logo -> initialization checklist (real status only) -> ONLINE -> LLM-style chat view.
// All AI work happens in the backend; this device only polls it (outbound HTTP) and shows the result.
// No cloud API keys on the device. No touchscreen code. Wi-Fi STATION mode only.
#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include "config.h"
#include "genesis_display.h"

GenesisTFT tft(TFT_CS, TFT_DC, TFT_RST);

// ------------------------------------------------------------------------- state
enum UiState { UI_CONNECTING, UI_READY, UI_THINKING, UI_SEARCHING, UI_TOOL, UI_RECEIVING, UI_ANSWERING, UI_ERROR };

static String   backendBase;
static uint32_t feedSeq = 0;
static String   devState = "READY";     // as reported by the backend feed
static String   curQuestion, curText, curProvider, curModel;
static String   curBrain = "CLOUD";     // "CLOUD" or "LOCAL"
static String   curMode  = "ONLINE";    // "ONLINE" or "OFFLINE"
static int      curPage = 0, totalPages = 1;
static bool     online = false;          // backend link is active
static bool     cloudOk = true;          // cloud AI reachable
static bool     localOk = false;         // local Ollama reachable
static int      failCount = 0;
static bool     tokenRejected = false;
static uint8_t  animFrame = 0;
static uint32_t lastPoll = 0, lastDeep = 0, lastAnim = 0, lastReconnect = 0, lastBar = 0;

// ------------------------------------------------------------------------ HTTP
struct HttpRes { int code; String body; uint32_t ms; String err; };

static HttpRes httpCall(const char* method, const String& path, uint32_t timeoutMs, bool auth = true) {
    HttpRes r{-1, "", 0, ""};
    uint32_t t0 = millis();
    WiFiClient client;
    HTTPClient http;
    http.setConnectTimeout(HTTP_CONNECT_TIMEOUT_MS);
    http.setTimeout(timeoutMs);
    http.setReuse(false);
    if (!http.begin(client, backendBase + path)) { r.err = "bad url"; return r; }
    if (auth) http.addHeader("X-Genesis-Token", GENESIS_TOKEN);
    if (strcmp(method, "POST") == 0) {
        http.addHeader("Content-Type", "application/json");
        r.code = http.POST("{}");
    } else {
        r.code = http.GET();
    }
    if (r.code > 0) r.body = http.getString();
    else r.err = HTTPClient::errorToString(r.code);
    http.end();
    r.ms = millis() - t0;
    return r;
}

// ------------------------------------------------------------------ top-bar helper
static void drawTopBar() {
    String label; uint16_t col = Col::OK;
    uint16_t dotCol = Col::OK;

    bool isLocal = (curBrain == "LOCAL" || curMode == "OFFLINE");

    if (!online) {
        label = "DISCONNECTED"; col = Col::BAD; dotCol = Col::BAD;
    } else if (devState == "THINKING") {
        label = isLocal ? "LOCAL THINKING" : "CLOUD THINKING";
        col = Col::CYAN; dotCol = Col::WARN;
    } else if (devState == "SEARCHING") {
        label = "SEARCHING"; col = Col::CYAN; dotCol = Col::WARN;
    } else if (devState == "EXECUTING TOOL") {
        label = "EXECUTING TOOL"; col = Col::CYAN; dotCol = Col::WARN;
    } else if (devState == "ERROR") {
        label = "ERROR"; col = Col::BAD; dotCol = Col::BAD;
    } else {
        if (isLocal) {
            label = "OFFLINE MODE"; col = Col::CYAN; dotCol = Col::CYAN;
        } else {
            label = "ONLINE MODE"; col = Col::OK; dotCol = Col::OK;
        }
    }
    chatTopBar(label, col, dotCol, WiFi.status() == WL_CONNECTED ? WiFi.RSSI() : -100);
}

static void topBarLabel(const char* label, uint16_t col) {
    uint16_t dotCol = (curBrain == "LOCAL") ? Col::CYAN : Col::OK;
    chatTopBar(label, col, dotCol, WiFi.status() == WL_CONNECTED ? WiFi.RSSI() : -100);
}

static void drawPageHint() {
    bool isLocal = (curBrain == "LOCAL" || curMode == "OFFLINE");
    String tag = isLocal ? "[LOCAL] " : "[CLOUD] ";
    String modelDisp = curModel.length() ? (tag + curModel) : "GENESIS AI";

    if (devState == "ANSWERED" && totalPages > 1)
        chatBottom("Page " + String(curPage + 1) + "/" + String(totalPages) + "   " + modelDisp + "   BOOT: page", isLocal ? Col::CYAN : Col::DIM);
    else if (!online)
        chatBottom("Reconnecting to " + String(BACKEND_HOST) + " ...", Col::WARN);
    else
        chatBottom(modelDisp + "   BOOT hold: new chat", isLocal ? Col::CYAN : Col::DIM);
}

// ----------------------------------------------------------- apply a feed update
static void applyFeed(JsonDocument& d) {
    devState    = d["state"].as<String>();
    curQuestion = d["question"].as<String>();
    curProvider = d["provider"].as<String>();
    curModel    = d["model"].as<String>();
    curBrain    = d["brain"] | "CLOUD";
    curMode     = d["mode"]  | "ONLINE";
    curText     = d["text"].as<String>();
    curPage     = d["page"] | 0;
    totalPages  = d["total_pages"] | 1;

    if (devState == "READY") {
        chatWelcome(String("http://") + BACKEND_HOST + ":" + BACKEND_PORT);
    } else if (devState == "ANSWERED") {
        chatQuestion(curQuestion);
        topBarLabel("RECEIVING", Col::CYAN);
        delay(120);
        topBarLabel("ANSWERING", Col::CYAN);
        chatAnswer(curText, Col::TEXT, true);
    } else if (devState == "ERROR") {
        chatQuestion(curQuestion.length() ? curQuestion : String("Request failed"));
        chatAnswer(curText.length() ? curText : String("Unknown error"), Col::BAD, false);
    } else {  // THINKING / SEARCHING / EXECUTING TOOL
        chatQuestion(curQuestion);
        chatClearAnswer();
        animFrame = 0; lastAnim = 0;
    }
    drawTopBar();
    drawPageHint();
}

static void setOnline(bool v) {
    if (online == v) return;
    online = v;
    drawTopBar();
    drawPageHint();
}

// ------------------------------------------------------------------- polling
static void pollFeed() {
    if (WiFi.status() != WL_CONNECTED) { failCount++; if (failCount >= 2) setOnline(false); return; }
    String path = "/api/device/feed?seq=" + String(feedSeq) + "&cols=" + CHAT_COLS + "&rows=" + CHAT_ROWS;
    HttpRes r = httpCall("GET", path, HTTP_FEED_TIMEOUT_MS);
    if (r.code == 401) {
        tokenRejected = true;
        chatClearBody();
        chatAnswer("Access token rejected by the backend. Update GENESIS_TOKEN in config.h.", Col::BAD, false);
        topBarLabel("AUTH ERROR", Col::BAD);
        return;
    }
    if (r.code != 200) {
        failCount++;
        Serial.printf("[feed] fail code=%d %s\n", r.code, r.err.c_str());
        if (failCount >= 3) setOnline(false);
        return;
    }
    JsonDocument doc;
    if (deserializeJson(doc, r.body)) { failCount++; return; }
    failCount = 0;
    bool wasTokenBad = tokenRejected; tokenRejected = false;
    bool recovered = !online;
    online = true;
    uint32_t newSeq = doc["seq"] | 0;
    bool changed = doc["changed"] | false;
    devState = doc["state"].as<String>();
    if (changed || wasTokenBad) {
        feedSeq = newSeq;
        if (!changed) feedSeq = 0;      // force full refresh next poll
        else { Serial.printf("[feed] seq=%u state=%s\n", newSeq, devState.c_str()); applyFeed(doc); }
    } else if (recovered) {
        drawTopBar(); drawPageHint();
    }
}

static void deepHealth() {
    HttpRes r = httpCall("GET", "/api/health?deep=1", HTTP_DEEP_TIMEOUT_MS, false);
    if (r.code != 200) return;
    JsonDocument doc;
    if (deserializeJson(doc, r.body)) return;
    bool ok = (doc["ai_ready"] | false) && (doc["cloud_reachable"] | true);
    if (ok != cloudOk) { cloudOk = ok; drawTopBar(); }
}

// ------------------------------------------------------------ BOOT button (GPIO 28)
static bool     btnDown = false, btnLongFired = false;
static uint32_t btnT0 = 0;

static void showPage(int p) {
    HttpRes r = httpCall("GET", "/api/device/feed/page?page=" + String(p) + "&cols=" + CHAT_COLS + "&rows=" + CHAT_ROWS, HTTP_FEED_TIMEOUT_MS);
    if (r.code != 200) return;
    JsonDocument doc;
    if (deserializeJson(doc, r.body)) return;
    curPage = doc["page"] | p;
    totalPages = doc["total_pages"] | totalPages;
    curText = doc["text"].as<String>();
    chatAnswer(curText, devState == "ERROR" ? Col::BAD : Col::TEXT, false);
    drawPageHint();
}

static void handleButton() {
    bool low = digitalRead(BOOT_BUTTON_PIN) == LOW;
    uint32_t now = millis();
    if (low && !btnDown) { btnDown = true; btnLongFired = false; btnT0 = now; }
    else if (low && btnDown && !btnLongFired && now - btnT0 >= 900) {
        btnLongFired = true;
        topBarLabel("NEW CHAT", Col::WARN);
        HttpRes r = httpCall("POST", "/api/device/new", HTTP_FEED_TIMEOUT_MS);
        Serial.printf("[btn] new chat -> %d\n", r.code);
        feedSeq = 0;           // force refresh
        lastPoll = 0;
    } else if (!low && btnDown) {
        btnDown = false;
        uint32_t held = now - btnT0;
        if (!btnLongFired && held >= 30 && held < 900 && devState == "ANSWERED" && totalPages > 1) {
            topBarLabel("RECEIVING", Col::CYAN);
            showPage((curPage + 1) % totalPages);
            drawTopBar();
        }
    }
}

// ------------------------------------------------------- initialization sequence
static bool stepWifi() {
    screenInitRow(1, "..", Col::CYAN, String("Connecting to ") + WIFI_SSID);
    if (WiFi.status() != WL_CONNECTED) {
        WiFi.disconnect(true);
        delay(100);
        WiFi.mode(WIFI_STA);
        WiFi.setHostname("genesis-ai");
        WiFi.setAutoReconnect(true);
        WiFi.begin(WIFI_SSID, WIFI_PASSWORD);   // DHCP + DHCP-provided DNS (no forced public DNS)
    }
    uint32_t t0 = millis(); uint8_t f = 0;
    while (WiFi.status() != WL_CONNECTED && millis() - t0 < WIFI_CONNECT_TIMEOUT_MS) {
        screenInitSpin(1, f++); delay(150);
    }
    if (WiFi.status() == WL_CONNECTED) {
        screenInitRow(1, "OK", Col::OK, String(WIFI_SSID) + " " + WiFi.localIP().toString() + " " + WiFi.RSSI() + "dBm");
        return true;
    }
    screenInitRow(1, "FAIL", Col::BAD, String("No link to hotspot (status ") + (int)WiFi.status() + ")");
    return false;
}

static bool stepBackendAndBrains(String& activeBrain, String& activeProvider, String& activeModel, bool& isOnlineMode) {
    screenInitRow(2, "..", Col::CYAN, String(BACKEND_HOST) + ":" + BACKEND_PORT);
    HttpRes r = httpCall("GET", "/api/health?deep=1", HTTP_DEEP_TIMEOUT_MS, false);
    if (r.code != 200) {
        screenInitRow(2, "FAIL", Col::BAD, String(BACKEND_HOST) + " " + (r.code > 0 ? String("HTTP ") + r.code : r.err));
        screenInitRow(3, "WAIT", Col::DIM, "Awaiting backend link...");
        screenInitRow(4, "WAIT", Col::DIM, "Awaiting backend link...");
        return false;
    }
    HttpRes a = httpCall("GET", "/api/device/feed?seq=0&cols=26&rows=9", HTTP_FEED_TIMEOUT_MS);
    if (a.code == 401) {
        screenInitRow(2, "FAIL", Col::BAD, "Access token rejected (config.h)");
        return false;
    }
    JsonDocument d;
    if (deserializeJson(d, r.body)) {
        screenInitRow(2, "FAIL", Col::BAD, "Invalid health response");
        return false;
    }
    screenInitRow(2, "OK", Col::OK, String(BACKEND_HOST) + ":" + BACKEND_PORT + "  v" + d["version"].as<String>() + " (" + r.ms + "ms)");

    // Step 3: Local AI (Ollama on Windows)
    localOk = d["local_ai_available"] | false;
    String locModel = d["local_model"].as<String>();
    if (localOk) {
        screenInitRow(3, "OK", Col::OK, "LOCAL AI AVAILABLE (" + locModel + ")");
    } else {
        screenInitRow(3, "OFF", Col::DIM, "Local Ollama service offline");
    }

    // Step 4: Cloud AI
    bool netOk = d["internet_accessible"] | false;
    bool cloudConfigured = d["cloud_ai_available"] | false;
    bool cloudReachable = d["cloud_reachable"] | false;
    String cModel = d["cloud_model"].as<String>();
    String cProvider = d["primary"]["id"].as<String>();

    if (cloudConfigured && netOk && cloudReachable) {
        screenInitRow(4, "OK", Col::OK, "CLOUD AI AVAILABLE (" + cModel + ")");
        cloudOk = true;
    } else if (!netOk) {
        screenInitRow(4, "OFF", Col::WARN, "Cloud AI offline (No Internet)");
        cloudOk = false;
    } else {
        screenInitRow(4, "WARN", Col::WARN, "Cloud error: " + d["cloud_detail"].as<String>());
        cloudOk = false;
    }

    activeBrain = d["active_brain"].as<String>();
    isOnlineMode = (d["active_mode"].as<String>() == "ONLINE");
    if (activeBrain == "LOCAL") {
        activeProvider = "ollama";
        activeModel = locModel;
    } else {
        activeProvider = cProvider;
        activeModel = cModel;
    }

    bool aiReady = localOk || cloudOk;
    return aiReady;
}

static void runInitSequence(String& activeBrain, String& activeProvider, String& activeModel, bool& isOnlineMode) {
    screenInitDraw();
    screenInitRow(0, "OK", Col::OK, String("RISC-V ") + getCpuFrequencyMhz() + "MHz  heap " + (ESP.getFreeHeap() / 1024) + "KB");
    bool wifiOk = false, brainsOk = false;
    while (true) {
        if (!wifiOk) wifiOk = stepWifi();
        if (!wifiOk) { screenInitFooter("Retrying Wi-Fi in 3s...", Col::WARN); delay(3000); continue; }

        brainsOk = stepBackendAndBrains(activeBrain, activeProvider, activeModel, isOnlineMode);
        if (brainsOk) {
            screenInitFooter(isOnlineMode ? "Dual Brain Online & Ready" : "Local Brain Ready (Offline)", Col::OK);
            delay(900);
            return;
        }

        screenInitFooter("Retrying backend in 5s...", Col::WARN);
        delay(5000);
        if (WiFi.status() != WL_CONNECTED) wifiOk = false;
    }
}

// ------------------------------------------------------------------------ setup/loop
void setup() {
    Serial.begin(115200);
    delay(200);
    Serial.println("\n=== GENESIS AI firmware (Dual Brain) ===");

    pinMode(BOOT_BUTTON_PIN, INPUT_PULLUP);

    // Display init exactly as in the calibrated, working firmware (RST pin 2 resets once here only).
    SPI.begin(TFT_SCK, -1, TFT_MOSI);
    tft.begin();
    tft.purgeAllGRAM();

    backendBase = String("http://") + BACKEND_HOST + ":" + BACKEND_PORT;

    screenBoot();                               // SCREEN 1
    String activeBrain, activeProvider, activeModel;
    bool isOnlineMode = false;
    runInitSequence(activeBrain, activeProvider, activeModel, isOnlineMode);  // SCREEN 2 (real statuses)

    online = true;
    curBrain = activeBrain;
    curModel = activeModel;
    curMode  = isOnlineMode ? "ONLINE" : "OFFLINE";

    screenReady(curBrain, activeProvider, curModel, isOnlineMode);  // SCREEN 3 (NEVER fake ONLINE!)
    delay(1800);
    chatDrawChrome();                           // SCREEN 4
    drawTopBar();
    chatWelcome(String("http://") + BACKEND_HOST + ":" + BACKEND_PORT);
    drawPageHint();
    lastDeep = millis();
    Serial.printf("[ready] brain=%s provider=%s model=%s mode=%s ip=%s\n",
                  curBrain.c_str(), activeProvider.c_str(), curModel.c_str(), curMode.c_str(), WiFi.localIP().toString().c_str());
}

void loop() {
    uint32_t now = millis();
    handleButton();

    // Wi-Fi recovery (non-blocking: WiFi.reconnect() every 8 s while down)
    if (WiFi.status() != WL_CONNECTED) {
        if (online) { online = false; drawTopBar(); drawPageHint(); }
        if (now - lastReconnect > 8000) { lastReconnect = now; WiFi.reconnect(); Serial.println("[wifi] reconnecting"); }
    }

    bool busy = (devState == "THINKING" || devState == "SEARCHING" || devState == "EXECUTING TOOL");
    uint32_t interval = !online ? 2500 : (busy ? 700 : 1500);
    if (now - lastPoll >= interval) { lastPoll = now; pollFeed(); }

    if (busy && online && now - lastAnim >= 280) {
        lastAnim = now;
        chatThinking(animFrame++, devState == "SEARCHING" ? "Searching" : devState == "EXECUTING TOOL" ? "Running tool" : "Thinking");
    }

    if (now - lastBar >= 5000) { lastBar = now; if (!busy) drawTopBar(); }   // refresh Wi-Fi bars
    if (online && now - lastDeep >= 60000) { lastDeep = now; deepHealth(); }  // cloud status (cached server-side)
    delay(8);
}
