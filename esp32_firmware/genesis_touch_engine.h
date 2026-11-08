#ifndef GENESIS_TOUCH_ENGINE_H
#define GENESIS_TOUCH_ENGINE_H

#include <Arduino.h>

struct TouchEvent {
    bool touched;
    int x;
    int y;
};

inline void initTouchEngine() {
    // Hand-touch pins are configured directly by setupHandTouchPin() in esp32_firmware.ino
}

#endif // GENESIS_TOUCH_ENGINE_H
