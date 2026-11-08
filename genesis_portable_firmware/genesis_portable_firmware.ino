// GENESIS AI — Single-Phone Portable Firmware (ESP32-C5 Standalone SoftAP).
// USB OTG Powered from Android Phone. Complete Web Dashboard Hosted Directly on Device.
// Zero Windows/PC/Ollama runtime dependencies. Display-Only ILI9341 SPI TFT.
#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <DNSServer.h>
#include <ArduinoJson.h>

#include "config.h"
#include "genesis_display.h"
#include "dashboard.h"
#include "genesis_photon_lighting.h"

GenesisTFT tft(TFT_CS, TFT_DC, TFT_RST);
WebServer server(80);
DNSServer dnsServer;

#define LOG_PRINT(...) Serial.printf(__VA_ARGS__)
#define LOG_PRINTLN(x) Serial.println(x)

// ---------------------------------------------------------------- Device State
enum DeviceState { ST_READY, ST_THINKING, ST_ANSWERED, ST_IMAGE_VIEW, ST_ERROR };

static DeviceState curState = ST_READY;
static String curQuestion = "";
static String curAnswer = "";
static String curProvider = "cellular-relay";
static String curModel = "gemini-2.5-flash";
static int curPage = 0;
static int totalPages = 1;
static std::vector<String> pageList;

// ----------------------------------------------------------- Fast Base64 Decoder
static size_t decodeB64(const char* in, size_t inLen, uint8_t* out, size_t maxOut) {
    static const int8_t T[256] = {
        -1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,
        -1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,62,-1,-1,-1,63,52,53,54,55,56,57,58,59,60,61,-1,-1,-1,-1,-1,-1,
        -1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,-1,-1,-1,-1,-1,
        -1,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,-1,-1,-1,-1,-1
    };
    size_t outLen = 0;
    uint32_t val = 0; int valb = -8;
    for (size_t i = 0; i < inLen && in[i] != '='; i++) {
        uint8_t c = (uint8_t)in[i];
        if (T[c] == -1) continue;
        val = (val << 6) | T[c];
        valb += 6;
        if (valb >= 0) {
            if (outLen < maxOut) out[outLen++] = (uint8_t)((val >> valb) & 0xFF);
            valb -= 8;
        }
    }
    return outLen;
}

static uint8_t animFrame = 0;
static uint32_t lastAnim = 0;
static uint32_t lastClientRefresh = 0;
static int lastClientCount = -1;

// ----------------------------------------------------------- Text Pagination
static void paginateText(const String& full) {
    pageList.clear();
    if (full.length() == 0) {
        pageList.push_back("");
        totalPages = 1;
        curPage = 0;
        return;
    }

    // Break text into pages that fit the 26 columns x 9 rows display (~234 chars max per page)
    int maxCharsPerPage = CHAT_COLS * CHAT_ROWS;
    int idx = 0;
    while (idx < full.length()) {
        int take = min(maxCharsPerPage, (int)full.length() - idx);
        // Try breaking at newline or space if not at end
        if (idx + take < full.length()) {
            int lastSpace = -1;
            for (int i = idx + take - 1; i >= idx + take - 30 && i > idx; i--) {
                if (full[i] == ' ' || full[i] == '\n') { lastSpace = i; break; }
            }
            if (lastSpace > idx) take = (lastSpace - idx) + 1;
        }
        pageList.push_back(full.substring(idx, idx + take));
        idx += take;
    }
    totalPages = max(1, (int)pageList.size());
    curPage = 0;
}

// ----------------------------------------------------------- Drawing & HUD
static void updateTopBar() {
    int clients = WiFi.softAPgetStationNum();
    String label;
    uint16_t labelCol = Col::OK;
    uint16_t dotCol = Col::OK;

    bool staOk = (WiFi.status() == WL_CONNECTED);
    switch (curState) {
        case ST_THINKING:
            label = "THINKING";
            labelCol = Col::CYAN;
            dotCol = Col::WARN;
            break;
        case ST_ANSWERED:
            label = "ANSWERED";
            labelCol = Col::OK;
            dotCol = Col::OK;
            break;
        case ST_IMAGE_VIEW:
            label = "IMAGE STUDIO";
            labelCol = Col::CYAN;
            dotCol = Col::OK;
            break;
        case ST_ERROR:
            label = "ERROR";
            labelCol = Col::BAD;
            dotCol = Col::BAD;
            break;
        default:
            if (staOk) {
                label = "HOTSPOT OK";
                labelCol = Col::OK;
                dotCol = Col::OK;
            } else if (clients > 0) {
                label = "PHONE CONNECTED";
                labelCol = Col::OK;
                dotCol = Col::OK;
            } else {
                label = "PORTABLE AP";
                labelCol = Col::CYAN;
                dotCol = Col::CYAN;
            }
            break;
    }
    chatTopBar(label, labelCol, dotCol, clients);
}

static void updateBottomBar() {
    if (curState == ST_ANSWERED && totalPages > 1) {
        chatBottom("Page " + String(curPage + 1) + "/" + String(totalPages) + "  " + curModel + "  BOOT: page", Col::CYAN);
    } else if (curState == ST_ANSWERED) {
        chatBottom(curModel + " via " + curProvider + "  BOOT: page", Col::DIM);
    } else {
        chatBottom("GENESIS AI   BOOT hold: new", Col::DIM);
    }
}

static void renderCurrentPage(bool animate = false) {
    if (pageList.empty()) return;
    chatQuestion(curQuestion);
    chatAnswer(pageList[curPage], curState == ST_ERROR ? Col::BAD : Col::TEXT, animate);
    updateTopBar();
    updateBottomBar();
}

// ----------------------------------------------------------- Web Server Endpoints
static void handleRoot() {
    server.sendHeader("Access-Control-Allow-Origin", "*");
    server.send_P(200, "text/html", DASHBOARD_HTML);
}

static void handleStatus() {
    JsonDocument doc;
    doc["device"] = "ESP32-C5";
    doc["uptime_s"] = millis() / 1000;
    doc["heap"] = ESP.getFreeHeap();
    doc["clients"] = WiFi.softAPgetStationNum();
    doc["ssid"] = SOFTAP_SSID;
    doc["ip"] = SOFTAP_IP.toString();
    doc["state"] = (curState == ST_THINKING) ? "THINKING" : (curState == ST_ANSWERED ? "ANSWERED" : "READY");

    String out;
    serializeJson(doc, out);
    server.sendHeader("Access-Control-Allow-Origin", "*");
    server.send(200, "application/json", out);
}

static void handleFeedGet() {
    JsonDocument doc;
    doc["state"] = (curState == ST_THINKING) ? "THINKING" : (curState == ST_ANSWERED ? "ANSWERED" : "READY");
    doc["question"] = curQuestion;
    doc["text"] = (!pageList.empty()) ? pageList[curPage] : "";
    doc["page"] = curPage;
    doc["total_pages"] = totalPages;
    doc["provider"] = curProvider;
    doc["model"] = curModel;

    String out;
    serializeJson(doc, out);
    server.sendHeader("Access-Control-Allow-Origin", "*");
    server.send(200, "application/json", out);
}

static void applyFeedUpdate(const String& stateStr, const String& q, const String& provider, const String& model, const String& newText) {
    curQuestion = q;
    curProvider = provider;
    if (curProvider == "cellular-relay" || curProvider == "relay" || curProvider == "gateway" || curProvider.length() == 0) {
        curProvider = "Gemini";
    }
    curModel = model;
    if (curModel == "omni" || curModel == "gemini-2.5-flash" || curModel.length() == 0) {
        curModel = "gemini-3.5-flash";
    }

    if (stateStr == "THINKING") {
        curState = ST_THINKING;
        chatQuestion(curQuestion);
        chatClearAnswer();
        updateTopBar();
        updateBottomBar();
    } else if (stateStr == "ERROR") {
        curState = ST_ERROR;
        curAnswer = newText;
        paginateText(curAnswer);
        renderCurrentPage(false);
    } else { // ANSWERED
        curState = ST_ANSWERED;
        curAnswer = newText;
        paginateText(curAnswer);
        renderCurrentPage(true);
    }
}

static String serialInBuf = "";

static void handleSerialInput() {
    while (Serial.available()) {
        char c = (char)Serial.read();
        if (c == '\n') {
            serialInBuf.trim();
            int startIdx = serialInBuf.indexOf('{');
            int endIdx = serialInBuf.lastIndexOf('}');
            if (startIdx >= 0 && endIdx > startIdx) {
                String jsonStr = serialInBuf.substring(startIdx, endIdx + 1);
                JsonDocument doc;
                DeserializationError err = deserializeJson(doc, jsonStr);
                if (!err) {
                    String stateStr = doc["state"] | "ANSWERED";
                    String q = doc["question"] | "";
                    String provider = doc["provider"] | "laptop";
                    String model = doc["model"] | "omni";
                    String text = doc["text"] | "";
                    applyFeedUpdate(stateStr, q, provider, model, text);
                    LOG_PRINT("[Bridge] Applied update: state=%s, q=%s\n", stateStr.c_str(), q.substring(0, 30).c_str());
                } else {
                    LOG_PRINT("[Bridge] JSON err: %s\n", err.c_str());
                }
            }
            serialInBuf = "";
        } else if (c != '\r') {
            if (serialInBuf.length() < 8192) {
                serialInBuf += c;
            }
        }
    }
}

static void handleFeedPost() {
    if (!server.hasArg("plain")) {
        server.send(400, "text/plain", "Missing body");
        return;
    }
    JsonDocument doc;
    DeserializationError err = deserializeJson(doc, server.arg("plain"));
    if (err) {
        server.send(400, "text/plain", "JSON parse error");
        return;
    }

    String stateStr = doc["state"] | "ANSWERED";
    String q = doc["question"].as<String>();
    String provider = doc["provider"] | "cellular-relay";
    String model = doc["model"] | "gemini-2.5-flash";
    String newText = doc["text"].as<String>();

    applyFeedUpdate(stateStr, q, provider, model, newText);

    server.sendHeader("Access-Control-Allow-Origin", "*");
    server.send(200, "application/json", "{\"ok\":true}");
}

static void handlePagePost() {
    if (totalPages > 1) {
        curPage = (curPage + 1) % totalPages;
        renderCurrentPage(false);
    }
    server.sendHeader("Access-Control-Allow-Origin", "*");
    server.send(200, "application/json", "{\"ok\":true,\"page\":" + String(curPage) + "}");
}

static void handleClearPost() {
    curState = ST_READY;
    curQuestion = "";
    curAnswer = "";
    pageList.clear();
    curPage = 0;
    totalPages = 1;
    chatWelcome(String("http://") + SOFTAP_IP.toString());
    updateTopBar();
    updateBottomBar();
    server.sendHeader("Access-Control-Allow-Origin", "*");
    server.send(200, "application/json", "{\"ok\":true}");
}

static void handleGenerate204() {
    server.sendHeader("Access-Control-Allow-Origin", "*");
    server.send(204, "text/plain", "");
}

static void handleAppleProbe() {
    server.sendHeader("Access-Control-Allow-Origin", "*");
    server.send(200, "text/html", "<HTML><HEAD><TITLE>Success</TITLE></HEAD><BODY>Success</BODY></HTML>");
}

static void handleNcsiProbe() {
    server.sendHeader("Access-Control-Allow-Origin", "*");
    server.send(200, "text/plain", "Microsoft NCSI");
}

static void handleNotFound() {
    String host = server.hostHeader();
    if (host.indexOf("192.168.4.1") >= 0 || host.indexOf("genesis") >= 0) {
        handleRoot();
    } else {
        server.send(404, "text/plain", "Not Found");
    }
}

// ----------------------------------------------------------- TFT Image Studio Endpoints
static void handleTftImageStart() {
    if (!server.hasArg("plain")) {
        server.send(400, "text/plain", "Missing body");
        return;
    }
    JsonDocument doc;
    DeserializationError err = deserializeJson(doc, server.arg("plain"));
    if (err) {
        server.send(400, "text/plain", "JSON parse error");
        return;
    }

    curState = ST_IMAGE_VIEW;
    curQuestion = doc["prompt"] | "AI Image";
    String style = doc["style"] | "Photoreal";
    String aspect = doc["aspect"] | "1:1";
    int x = doc["x"] | 80;
    int y = doc["y"] | 58;
    int w = doc["w"] | 160;
    int h = doc["h"] | 120;

    imageStudioFrame(curQuestion, style, aspect, x, y, w, h);
    updateTopBar();
    chatBottom(style + "  |  " + aspect + "  |  Streaming to TFT...", Col::CYAN);

    server.sendHeader("Access-Control-Allow-Origin", "*");
    server.send(200, "application/json", "{\"ok\":true}");
}

static void handleTftImageChunk() {
    if (!server.hasArg("plain")) {
        server.send(400, "text/plain", "Missing body");
        return;
    }
    JsonDocument doc;
    DeserializationError err = deserializeJson(doc, server.arg("plain"));
    if (err) {
        server.send(400, "text/plain", "JSON parse error");
        return;
    }

    int x = doc["x"] | 0;
    int y = doc["y"] | 0;
    int w = doc["w"] | 0;
    int h = doc["h"] | 0;
    const char* b64 = doc["data"] | "";

    static uint8_t chunkBuf[5120];
    size_t len = decodeB64(b64, strlen(b64), chunkBuf, sizeof(chunkBuf));
    displayImageChunk(x, y, w, h, chunkBuf, len);

    server.sendHeader("Access-Control-Allow-Origin", "*");
    server.send(200, "application/json", "{\"ok\":true}");
}

static void handleTftImageFinish() {
    String style = "AI Art";
    String aspect = "TFT";
    if (server.hasArg("plain")) {
        JsonDocument doc;
        if (!deserializeJson(doc, server.arg("plain"))) {
            style = doc["style"] | "AI Art";
            aspect = doc["aspect"] | "TFT";
        }
    }
    imageStudioFinish(style, aspect);
    updateTopBar();
    chatBottom("Image Studio: Display Render Complete", Col::OK);

    server.sendHeader("Access-Control-Allow-Origin", "*");
    server.send(200, "application/json", "{\"ok\":true}");
}

// ----------------------------------------------------------- BOOT Button (GPIO 28)
static bool btnDown = false;
static bool btnLongFired = false;
static uint32_t btnT0 = 0;

static void handleButton() {
    bool low = (digitalRead(BOOT_BUTTON_PIN) == LOW);
    uint32_t now = millis();
    if (low && !btnDown) {
        btnDown = true;
        btnLongFired = false;
        btnT0 = now;
    } else if (low && btnDown && !btnLongFired && now - btnT0 >= 900) {
        btnLongFired = true;
        handleClearPost();
    } else if (!low && btnDown) {
        btnDown = false;
        uint32_t held = now - btnT0;
        if (!btnLongFired && held >= 30 && held < 900) {
            if (curState == ST_IMAGE_VIEW) {
                handleClearPost();
            } else if (curState == ST_ANSWERED && totalPages > 1) {
                handlePagePost();
            }
        }
    }
}

// ----------------------------------------------------------- Setup & Startup Sequence
void setup() {
    Serial.setRxBufferSize(8192);
    Serial.begin(115200);
    delay(200);
    LOG_PRINTLN("\n=== GENESIS AI: Single-Phone Portable Architecture ===");

    pinMode(BOOT_BUTTON_PIN, INPUT_PULLUP);
    genesisPhotonInit();

    // 1. Initialize Display
    SPI.begin(TFT_SCK, -1, TFT_MOSI);
    tft.begin();
    tft.purgeAllGRAM();

    // 2. Display GENESIS Logo (Screen 1)
    screenBoot();

    // 3. Initialize Hardware and Local Services (Screen 2)
    screenInitDraw();
    screenInitRow(0, "OK", Col::OK, String("RISC-V ") + getCpuFrequencyMhz() + "MHz  heap " + (ESP.getFreeHeap() / 1024) + "KB");

    // 4. Start Wi-Fi in Dual AP + Station Mode
    WiFi.mode(WIFI_AP_STA);
    WiFi.setBandMode(WIFI_BAND_MODE_2G_ONLY);
    WiFi.setScanMethod(WIFI_ALL_CHANNEL_SCAN);
    WiFi.setMinSecurity(WIFI_AUTH_WPA2_PSK);
    WiFi.setAutoReconnect(true);

    WiFi.onEvent([](WiFiEvent_t event, WiFiEventInfo_t info) {
        if (event == ARDUINO_EVENT_WIFI_STA_GOT_IP) {
            LOG_PRINT("[STA] CONNECTED TO HOTSPOT! IP: %s\n", WiFi.localIP().toString().c_str());
            updateTopBar();
        } else if (event == ARDUINO_EVENT_WIFI_STA_DISCONNECTED) {
            uint8_t r = info.wifi_sta_disconnected.reason;
            LOG_PRINT("[STA] Disconnected reason: %d\n", r);
            updateTopBar();
        }
    });

    // SoftAP for direct connection
    WiFi.softAPConfig(SOFTAP_IP, SOFTAP_GW, SOFTAP_NETMASK);
    bool apOk = WiFi.softAP(SOFTAP_SSID);
    LOG_PRINT("[AP] WiFi.softAP('%s') result=%d\n", SOFTAP_SSID, apOk);

    // Connect to phone hotspot "Lost Case "
    LOG_PRINT("[STA] Connecting to hotspot '%s'...\n", HOTSPOT_SSID_1);
    WiFi.begin(HOTSPOT_SSID_1, HOTSPOT_PASS);

    if (apOk) {
        screenInitRow(1, "OK", Col::OK, String(SOFTAP_SSID) + "  " + SOFTAP_IP.toString());
    } else {
        screenInitRow(1, "FAIL", Col::BAD, "SoftAP start error");
    }

    // 5. Start DNS for genesis.ai only (do NOT hijack external internet domains like googleapis.com)
    dnsServer.setErrorReplyCode(DNSReplyCode::NonExistentDomain);
    dnsServer.start(53, "genesis.ai", SOFTAP_IP);
    screenInitRow(2, "OK", Col::OK, "Port 53 Local DNS (genesis.ai)");

    // 6. Start Web Server
    server.on("/", HTTP_GET, handleRoot);
    server.on("/api/status", HTTP_GET, handleStatus);
    server.on("/api/feed", HTTP_GET, handleFeedGet);
    server.on("/api/feed", HTTP_POST, handleFeedPost);
    server.on("/api/page", HTTP_POST, handlePagePost);
    server.on("/api/clear", HTTP_POST, handleClearPost);
    server.on("/api/rgb", HTTP_GET, []() {
        String resp = "{\"status\":\"ok\",\"pin\":27,\"brightness\":" + String((int)genesisPhotonBrightness) + ",\"mode\":\"CONTINUOUS_GAMING\"}";
        server.send(200, "application/json", resp);
    });
    server.on("/api/rgb", HTTP_POST, []() {
        if (server.hasArg("brightness")) {
            genesisPhotonSetBrightness(server.arg("brightness").toInt());
        }
        String resp = "{\"status\":\"ok\",\"pin\":27,\"brightness\":" + String((int)genesisPhotonBrightness) + ",\"mode\":\"CONTINUOUS_GAMING\"}";
        server.send(200, "application/json", resp);
    });
    server.on("/api/tft/image/start", HTTP_POST, handleTftImageStart);
    server.on("/api/tft/image/chunk", HTTP_POST, handleTftImageChunk);
    server.on("/api/tft/image/finish", HTTP_POST, handleTftImageFinish);

    // Connectivity check probes (respond with success/204 so Android does NOT trap the phone in CaptivePortalLogin)
    server.on("/generate_204", HTTP_GET, handleGenerate204);
    server.on("/gen_204", HTTP_GET, handleGenerate204);
    server.on("/hotspot-detect.html", HTTP_GET, handleAppleProbe);
    server.on("/canonical.html", HTTP_GET, handleGenerate204);
    server.on("/ncsi.txt", HTTP_GET, handleNcsiProbe);
    server.onNotFound(handleNotFound);

    server.begin();
    screenInitRow(3, "OK", Col::OK, "Port 80 Embedded Dashboard Ready");

    // Clients status
    screenInitRow(4, "WAIT", Col::CYAN, "Awaiting phone connection...");
    screenInitFooter("Local SoftAP & Dashboard Ready", Col::OK);
    delay(1200);

    // 7. Ready Screen (Screen 3)
    screenReady(SOFTAP_SSID, SOFTAP_IP.toString());
    delay(1600);

    // 8. Enter Chat UI (Screen 4)
    chatDrawChrome();
    chatWelcome(String("http://") + SOFTAP_IP.toString());
    updateTopBar();
    updateBottomBar();

    LOG_PRINT("[ready] SoftAP SSID=%s IP=%s\n", SOFTAP_SSID, SOFTAP_IP.toString().c_str());
}

void loop() {
    dnsServer.processNextRequest();
    server.handleClient();
    handleButton();
    handleSerialInput();
    genesisPhotonLoop();

    uint32_t now = millis();

    // Check client count updates
    if (now - lastClientRefresh >= 2000) {
        lastClientRefresh = now;
        int c = WiFi.softAPgetStationNum();
        if (c != lastClientCount) {
            lastClientCount = c;
            updateTopBar();
            LOG_PRINT("[AP] Clients connected: %d\n", c);
        }
    }

    // Gentle Hotspot Reconnection Check (30-second interval, only if not in progress)
    static uint32_t lastStaCheck = 0;
    static int staAttempts = 0;
    if (now - lastStaCheck >= 30000) {
        lastStaCheck = now;
        if (WiFi.status() != WL_CONNECTED) {
            staAttempts++;
            const char* targetSsid = (staAttempts % 2 == 1) ? HOTSPOT_SSID_1 : HOTSPOT_SSID_2;
            LOG_PRINT("[STA] Retrying hotspot association with: '%s'\n", targetSsid);
            WiFi.begin(targetSsid, HOTSPOT_PASS);
        }
    }

    // Idle Cinematic Arc-Reactor Animation (10 FPS)
    if (curState == ST_READY && now - lastAnim >= 90) {
        lastAnim = now;
        drawCinematicReactor(160, 112, animFrame++);
    }

    // Thinking Cinematic Arc-Reactor Animation (10 FPS)
    if (curState == ST_THINKING && now - lastAnim >= 90) {
        lastAnim = now;
        String thinkMsg = (curProvider.length() > 0) ? ("Thinking via " + curProvider) : "Thinking...";
        chatThinking(animFrame++, thinkMsg);
    }

    delay(2);
}
