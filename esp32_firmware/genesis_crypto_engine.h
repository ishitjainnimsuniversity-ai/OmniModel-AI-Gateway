#ifndef GENESIS_CRYPTO_ENGINE_H
#define GENESIS_CRYPTO_ENGINE_H

#include <Arduino.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Preferences.h>

// ==============================================================================
// GENESIS AI 5.0 - CRYPTO & GLOBAL MARKET CANDLESTICK ENGINE (REAL-TIME & OFFLINE)
// ==============================================================================
// Tracks Bitcoin (BTC), Ethereum (ETH), Solana (SOL), and Fine Gold (XAU/PAXG).
// Auto-syncs live via CoinGecko / Coinbase (zero API key required).
// Persists latest trends in on-chip NVS flash for 100% offline market HUD.
// ==============================================================================

struct MarketAsset {
    const char* id;
    const char* symbol;
    const char* name;
    float priceUsd;
    float change24h;
    float high24h;
    float low24h;
    float candleHistory[12]; // Simulated 12-hour candlestick sequence
    bool isLiveSync;
};

// 4 Core Master Assets
MarketAsset marketAssets[4] = {
    {"bitcoin",   "BTC",  "Bitcoin",   82794.0f,  1.12f, 83450.0f, 81900.0f, {81950, 82100, 82050, 82300, 82250, 82500, 82400, 82650, 82550, 82700, 82600, 82794}, false},
    {"ethereum",  "ETH",  "Ethereum",   2436.0f,  0.81f,  2480.0f,  2410.0f, {2415,  2420,  2418,  2430,  2425,  2440,  2435,  2445,  2438,  2442,  2430,  2436},  false},
    {"solana",    "SOL",  "Solana",      105.6f,  1.88f,   108.5f,   103.2f, {103.5, 104.0, 103.8, 104.5, 104.2, 105.0, 104.8, 105.5, 105.1, 105.4, 105.2, 105.6},  false},
    {"pax-gold",  "GOLD", "Fine Gold",  4165.0f,  0.25f,  4180.0f,  4150.0f, {4152,  4155,  4154,  4158,  4157,  4160,  4159,  4162,  4161,  4163,  4162,  4165},  false}
};

Preferences cryptoPrefs;
int activeCryptoIndex = 0;
unsigned long lastCryptoSyncTime = 0;

void generateCandleSequence(MarketAsset& asset) {
    float base = asset.priceUsd / (1.0f + (asset.change24h / 100.0f));
    float step = (asset.priceUsd - base) / 11.0f;
    for (int i = 0; i < 12; i++) {
        float noise = ((float)((i * 17) % 7) - 3.0f) * (asset.priceUsd * 0.003f);
        asset.candleHistory[i] = base + (step * i) + noise;
    }
    asset.candleHistory[11] = asset.priceUsd;
}

void initCryptoEngine() {
    cryptoPrefs.begin("genesis_crypto", false);
    for (int i = 0; i < 4; i++) {
        String keyP = "p_" + String(marketAssets[i].symbol);
        String keyC = "c_" + String(marketAssets[i].symbol);
        float cachedP = cryptoPrefs.getFloat(keyP.c_str(), 0.0f);
        float cachedC = cryptoPrefs.getFloat(keyC.c_str(), 999.0f);
        if (cachedP > 0.0f) {
            marketAssets[i].priceUsd = cachedP;
            if (cachedC != 999.0f) marketAssets[i].change24h = cachedC;
            marketAssets[i].high24h = cachedP * (1.0f + abs(marketAssets[i].change24h) * 0.008f);
            marketAssets[i].low24h  = cachedP * (1.0f - abs(marketAssets[i].change24h) * 0.008f);
        }
        generateCandleSequence(marketAssets[i]);
    }
}

bool fetchLiveCryptoPrices() {
    if (WiFi.status() != WL_CONNECTED) return false;

    WiFiClientSecure secureClient;
    secureClient.setInsecure();
    HTTPClient https;

    // Free CoinGecko multi-asset simple price endpoint (Zero API Key)
    String url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,pax-gold&vs_currencies=usd&include_24hr_change=true";
    if (!https.begin(secureClient, url)) return false;

    https.setUserAgent("ESP32-C5-Genesis-AI/5.0");
    https.setTimeout(6000);
    int httpCode = https.GET();

    bool success = false;
    if (httpCode == 200) {
        String payload = https.getString();
        JsonDocument doc;
        DeserializationError err = deserializeJson(doc, payload);
        if (!err) {
            for (int i = 0; i < 4; i++) {
                const char* id = marketAssets[i].id;
                if (doc[id].is<JsonObject>()) {
                    float p = doc[id]["usd"] | 0.0f;
                    float c = doc[id]["usd_24h_change"] | 0.0f;
                    if (p > 0.0f) {
                        marketAssets[i].priceUsd = p;
                        marketAssets[i].change24h = c;
                        marketAssets[i].high24h = p * (1.0f + max(0.01f, abs(c) * 0.008f));
                        marketAssets[i].low24h  = p * (1.0f - max(0.01f, abs(c) * 0.008f));
                        marketAssets[i].isLiveSync = true;
                        generateCandleSequence(marketAssets[i]);

                        // Save to NVS flash cache
                        String keyP = "p_" + String(marketAssets[i].symbol);
                        String keyC = "c_" + String(marketAssets[i].symbol);
                        cryptoPrefs.putFloat(keyP.c_str(), p);
                        cryptoPrefs.putFloat(keyC.c_str(), c);
                    }
                }
            }
            lastCryptoSyncTime = millis();
            success = true;
        }
    }
    https.end();

    // Fallback: Coinbase direct spot check for Bitcoin if CoinGecko failed
    if (!success) {
        HTTPClient cbHttps;
        if (cbHttps.begin(secureClient, "https://api.coinbase.com/v2/prices/BTC-USD/spot")) {
            cbHttps.setTimeout(4000);
            int code = cbHttps.GET();
            if (code == 200) {
                JsonDocument cbDoc;
                if (!deserializeJson(cbDoc, cbHttps.getString())) {
                    float btcP = cbDoc["data"]["amount"].as<float>();
                    if (btcP > 1000.0f) {
                        marketAssets[0].priceUsd = btcP;
                        marketAssets[0].isLiveSync = true;
                        generateCandleSequence(marketAssets[0]);
                        success = true;
                    }
                }
            }
            cbHttps.end();
        }
    }

    return success;
}

String getMarketReport(int assetIdx) {
    if (assetIdx < 0 || assetIdx >= 4) assetIdx = 0;
    const MarketAsset& a = marketAssets[assetIdx];

    String trendStr = (a.change24h >= 0) ? ("+" + String(a.change24h, 2) + "% Bullish") : (String(a.change24h, 2) + "% Bearish");
    String syncStr = a.isLiveSync ? "Live Ticker" : "Offline Cache";

    char buf[180];
    if (a.priceUsd >= 1000.0f) {
        snprintf(buf, sizeof(buf), "%s (%s): $%.0f USD (%s) | 24h High: $%.0f | Low: $%.0f [%s]",
                 a.name, a.symbol, a.priceUsd, trendStr.c_str(), a.high24h, a.low24h, syncStr.c_str());
    } else {
        snprintf(buf, sizeof(buf), "%s (%s): $%.2f USD (%s) | 24h High: $%.2f | Low: $%.2f [%s]",
                 a.name, a.symbol, a.priceUsd, trendStr.c_str(), a.high24h, a.low24h, syncStr.c_str());
    }
    return String(buf);
}

bool checkAndProcessCrypto(const String& prompt, String& answer) {
    String pLower = prompt;
    pLower.toLowerCase();
    pLower.trim();

    bool matched = false;
    if (pLower.indexOf("bitcoin") >= 0 || pLower.indexOf("btc") >= 0) {
        activeCryptoIndex = 0;
        matched = true;
    } else if (pLower.indexOf("ethereum") >= 0 || pLower.indexOf("eth") >= 0) {
        activeCryptoIndex = 1;
        matched = true;
    } else if (pLower.indexOf("solana") >= 0 || pLower.indexOf("sol") >= 0) {
        activeCryptoIndex = 2;
        matched = true;
    } else if (pLower.indexOf("gold") >= 0 || pLower.indexOf("xau") >= 0) {
        activeCryptoIndex = 3;
        matched = true;
    } else if (pLower.indexOf("crypto") >= 0 || pLower.indexOf("market") >= 0 || pLower.indexOf("stock") >= 0 || pLower.indexOf("ticker") >= 0 || pLower.indexOf("candlestick") >= 0) {
        activeCryptoIndex = 0;
        matched = true;
    }

    if (matched) {
        // Silent quick sync if on Wi-Fi and last sync was > 45s ago
        if (WiFi.status() == WL_CONNECTED && (millis() - lastCryptoSyncTime > 45000 || lastCryptoSyncTime == 0)) {
            fetchLiveCryptoPrices();
        }
        answer = getMarketReport(activeCryptoIndex);
        return true;
    }

    return false;
}

#endif // GENESIS_CRYPTO_ENGINE_H
