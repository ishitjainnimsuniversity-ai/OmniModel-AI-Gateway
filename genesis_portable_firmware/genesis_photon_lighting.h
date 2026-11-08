// ==============================================================================
// GENESIS AI — PHOTON CONTINUOUS ULTRA-VIBRANT CHROMA LIGHT MODE
// Dedicated RGB Engine for Espressif ESP32-C5-DevKitC-1 Onboard WS2812B (GPIO 27)
// Full Spectrum: Crimson Red -> Amber Gold -> Emerald Green -> Quantum Cyan -> Electric Blue -> Cyber Violet
// ==============================================================================
#pragma once
#include <Arduino.h>
#include <esp32-hal-rgb-led.h>

#ifndef RGB_LED_PIN
#define RGB_LED_PIN 27
#endif

// Master configuration
static volatile uint8_t genesisPhotonBrightness = 45; // 45% vibrant gaming brightness
static volatile bool genesisPhotonEnabled = true;

// Keyframe RGB Color Definition
struct PhotonColor {
    uint8_t r;
    uint8_t g;
    uint8_t b;
};

// Full Chroma Spectrum of "Most Beautiful Lights"
// Red, Amber, Green, Cyan, Royal Blue, Cyber Violet
static const PhotonColor CHROMA_PALETTE[] = {
    { 255,   0,  55 }, // 0. Crimson Cyber Red     (#FF0037)
    { 255, 110,   0 }, // 1. Solar Amber Gold      (#FF6E00)
    {   0, 240,  90 }, // 2. Emerald Neon Green     (#00F05A)
    {   0, 235, 255 }, // 3. Quantum Vivid Cyan     (#00EBFF)
    {   0,  95, 255 }, // 4. Electric Royal Blue    (#005FFF)
    { 175,   0, 255 }  // 5. Arcane Cyber Violet    (#AF00FF)
};

static const int NUM_CHROMA_STAGES = 6;
static const uint32_t STAGE_DURATION_MS = 1300; // 1.3s per transition
static const uint32_t TOTAL_CYCLE_MS = NUM_CHROMA_STAGES * STAGE_DURATION_MS; // 7.8s full loop

// Non-blocking Step Function
inline void genesisPhotonStep() {
    if (!genesisPhotonEnabled) {
        rgbLedWrite(RGB_LED_PIN, 0, 0, 0);
        return;
    }

    uint32_t now = millis();
    uint32_t phase = now % TOTAL_CYCLE_MS;

    int stage = phase / STAGE_DURATION_MS;
    int nextStage = (stage + 1) % NUM_CHROMA_STAGES;

    uint32_t stageProgressMs = phase % STAGE_DURATION_MS;
    float p = (float)stageProgressMs / (float)STAGE_DURATION_MS;

    // Cosine ease interpolation: 0.5 * (1 - cos(pi * p))
    // Produces buttery-smooth, organic gaming transitions
    float ease = (1.0f - cosf(p * 3.14159265f)) * 0.5f;

    const PhotonColor& fromCol = CHROMA_PALETTE[stage];
    const PhotonColor& toCol   = CHROMA_PALETTE[nextStage];

    float curR = (float)fromCol.r + ((float)toCol.r - (float)fromCol.r) * ease;
    float curG = (float)fromCol.g + ((float)toCol.g - (float)fromCol.g) * ease;
    float curB = (float)fromCol.b + ((float)toCol.b - (float)fromCol.b) * ease;

    // Gaming PC Breathing Modulation:
    // Smooth sinusoidal pulsation between 80% and 100% of nominal brightness
    // Cycle period ~2600ms
    float breathSine = sinf((float)now * 0.00241f); // 2*pi / 2600
    float breath = 0.80f + 0.20f * (0.5f * (1.0f + breathSine));

    // Master brightness scaling (clamped 0..100%)
    float masterScale = (float)genesisPhotonBrightness / 100.0f;
    float finalScale = masterScale * breath;

    uint8_t outR = (uint8_t)constrain((int)(curR * finalScale + 0.5f), 0, 255);
    uint8_t outG = (uint8_t)constrain((int)(curG * finalScale + 0.5f), 0, 255);
    uint8_t outB = (uint8_t)constrain((int)(curB * finalScale + 0.5f), 0, 255);

    rgbLedWrite(RGB_LED_PIN, outR, outG, outB);
}

// Background FreeRTOS Task
static TaskHandle_t s_photonTaskHandle = NULL;

static void genesisPhotonTask(void* pvParameters) {
    (void)pvParameters;
    for (;;) {
        genesisPhotonStep();
        vTaskDelay(pdMS_TO_TICKS(25)); // 40 FPS, yields CPU to Wi-Fi & WebServer
    }
}

// Initializer: Called once during setup()
inline void genesisPhotonInit() {
    // Immediate illumination on startup (starts with vibrant Red at nominal brightness)
    uint8_t initR = (uint8_t)(CHROMA_PALETTE[0].r * (genesisPhotonBrightness / 100.0f));
    uint8_t initG = (uint8_t)(CHROMA_PALETTE[0].g * (genesisPhotonBrightness / 100.0f));
    uint8_t initB = (uint8_t)(CHROMA_PALETTE[0].b * (genesisPhotonBrightness / 100.0f));
    rgbLedWrite(RGB_LED_PIN, initR, initG, initB);

    // Launch FreeRTOS background task on Core 0 (Priority 1 = Idle/Ambient priority)
    // Ensures LED updates independently of main loop, network, or display redrawing
    BaseType_t res = xTaskCreate(
        genesisPhotonTask,
        "photon_rgb",
        2048,
        NULL,
        1,
        &s_photonTaskHandle
    );

    if (res != pdPASS) {
        Serial.println("[PhotonRGB] FreeRTOS task creation deferred to main loop fallback");
        s_photonTaskHandle = NULL;
    } else {
        Serial.println("[PhotonRGB] Ultra-Vibrant Full Chroma Light Engine started on GPIO 27 (40 FPS FreeRTOS)");
    }
}

// Loop tick: acts as seamless fallback if FreeRTOS task wasn't created
inline void genesisPhotonLoop() {
    if (s_photonTaskHandle == NULL) {
        static uint32_t lastStep = 0;
        uint32_t now = millis();
        if (now - lastStep >= 25) { // 40 FPS
            lastStep = now;
            genesisPhotonStep();
        }
    }
}

// Runtime Brightness Control (0 - 100)
inline void genesisPhotonSetBrightness(uint8_t percent) {
    genesisPhotonBrightness = constrain(percent, 0, 100);
}
