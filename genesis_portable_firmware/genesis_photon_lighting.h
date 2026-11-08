// ==============================================================================
// GENESIS AI — PHOTON CONTINUOUS GAMING LIGHT MODE
// Dedicated RGB Engine for Espressif ESP32-C5-DevKitC-1 Onboard WS2812B (GPIO 27)
// ==============================================================================
#pragma once
#include <Arduino.h>
#include <esp32-hal-rgb-led.h>

#ifndef RGB_LED_PIN
#define RGB_LED_PIN 27
#endif

// Master configuration
static volatile uint8_t genesisPhotonBrightness = 40; // 40% default gaming brightness
static volatile bool genesisPhotonEnabled = true;

// Keyframe RGB Colors
// 1. Electric Blue:   #006BFF -> (0, 107, 255)
// 2. Cyan:            #00E5FF -> (0, 229, 255)
// 3. Emerald Green:   #00D878 -> (0, 216, 120)
struct PhotonColor {
    uint8_t r;
    uint8_t g;
    uint8_t b;
};

static const PhotonColor COLOR_ELECTRIC_BLUE = { 0, 107, 255 };
static const PhotonColor COLOR_CYAN          = { 0, 229, 255 };
static const PhotonColor COLOR_EMERALD_GREEN = { 0, 216, 120 };

// Cycle Timing: 6000ms total loop (2000ms per stage)
static const uint32_t STAGE_DURATION_MS = 2000;
static const uint32_t TOTAL_CYCLE_MS    = 6000;

// Non-blocking Step Function
inline void genesisPhotonStep() {
    if (!genesisPhotonEnabled) {
        rgbLedWrite(RGB_LED_PIN, 0, 0, 0);
        return;
    }

    uint32_t now = millis();
    uint32_t phase = now % TOTAL_CYCLE_MS;

    PhotonColor fromCol, toCol;
    float p = 0.0f;

    if (phase < STAGE_DURATION_MS) {
        // Stage 0: Electric Blue -> Cyan
        fromCol = COLOR_ELECTRIC_BLUE;
        toCol   = COLOR_CYAN;
        p = (float)phase / (float)STAGE_DURATION_MS;
    } else if (phase < (STAGE_DURATION_MS * 2)) {
        // Stage 1: Cyan -> Emerald Green
        fromCol = COLOR_CYAN;
        toCol   = COLOR_EMERALD_GREEN;
        p = (float)(phase - STAGE_DURATION_MS) / (float)STAGE_DURATION_MS;
    } else {
        // Stage 2: Emerald Green -> Electric Blue
        fromCol = COLOR_EMERALD_GREEN;
        toCol   = COLOR_ELECTRIC_BLUE;
        p = (float)(phase - (STAGE_DURATION_MS * 2)) / (float)STAGE_DURATION_MS;
    }

    // Cosine ease interpolation: 0.5 * (1 - cos(pi * p))
    // Produces buttery-smooth, organic gaming PC transitions
    float ease = (1.0f - cosf(p * 3.14159265f)) * 0.5f;

    float curR = (float)fromCol.r + ((float)toCol.r - (float)fromCol.r) * ease;
    float curG = (float)fromCol.g + ((float)toCol.g - (float)fromCol.g) * ease;
    float curB = (float)fromCol.b + ((float)toCol.b - (float)fromCol.b) * ease;

    // Gaming PC Breathing Modulation:
    // Smooth sinusoidal pulsation between 75% and 100% of nominal brightness
    // Cycle period ~2800ms
    float breathSine = sinf((float)now * 0.00224f); // 2*pi / 2800 ~ 0.00224
    float breath = 0.76f + 0.24f * (0.5f * (1.0f + breathSine));

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
        vTaskDelay(pdMS_TO_TICKS(25)); // 40 FPS, completely yields CPU to Wi-Fi
    }
}

// Initializer: Called once during setup()
inline void genesisPhotonInit() {
    // Immediate illumination on startup (Electric Blue at 40%)
    uint8_t initR = (uint8_t)(COLOR_ELECTRIC_BLUE.r * (genesisPhotonBrightness / 100.0f));
    uint8_t initG = (uint8_t)(COLOR_ELECTRIC_BLUE.g * (genesisPhotonBrightness / 100.0f));
    uint8_t initB = (uint8_t)(COLOR_ELECTRIC_BLUE.b * (genesisPhotonBrightness / 100.0f));
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
        Serial.println("[PhotonRGB] Continuous Gaming Light Engine started on GPIO 27 (40 FPS FreeRTOS)");
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
