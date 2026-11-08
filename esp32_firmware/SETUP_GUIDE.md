# 🛠️ GENESIS AI 5.0 + OpenJarvis // ESP32-C5 Master Hardware & Firmware Guide

This guide documents your complete, unified **ESP32-C5** master firmware ([`esp32_firmware.ino`](file:///C:/Users/ishit%20jain/.gemini/antigravity/scratch/OmniModelGateway/esp32_firmware/esp32_firmware.ino)) with **Stanford OpenJarvis**, **20+ Unified AI Models**, **8-Task FreeRTOS Multitasking**, **Dual-Mode Wi-Fi Hotspot (`ESP32-C5-AI`)**, and **Automatic 2.4" ILI9341 Screen Hot-Plug Synchronization**.

---

## 1. 📦 Hardware Pinout Mapping (ESP32-C5)

### A. 2.4" ILI9341 SPI TFT Display + XPT2046 Touch
> **Auto-Sync Enabled**: Even when your ESP32-C5 is already powered on, as soon as you connect your 2.4-inch screen, **Task 1 (`taskDisplayUI`)** automatically detects it within seconds, initializes the ILI9341 driver, and displays your **ESP32-C5 Wi-Fi Hotspot (`ESP32-C5-AI` / `192.168.4.1`)**, **Station IP**, and **Iron Man / Quantum HUD**!

| Display / Touch Pin | Function | ESP32-C5 GPIO |
| :--- | :--- | :--- |
| **VCC** | 3.3V Power | **3V3** |
| **GND** | Ground | **GND** |
| **CS** | TFT Chip Select | **GPIO 6** |
| **RESET / RST** | TFT Reset | **GPIO 2** |
| **DC / RS** | TFT Data / Command | **GPIO 7** |
| **MOSI / SDI** | SPI MOSI | **GPIO 8** |
| **SCK / SCLK** | SPI Clock | **GPIO 10** |
| **LED / BL** | Backlight Control | **GPIO 24** (or 3V3) |
| **MISO / SDO** | SPI MISO | **GPIO 9** |
| **T_CS** | Touch Chip Select (XPT2046) | **GPIO 3** |
| **T_CLK / T_DIN / T_DO** | Shared SPI Bus | **GPIO 10 / 8 / 9** |

### B. INMP441 I2S Digital Microphone & MicroSD
| Peripheral Pin | Function | ESP32-C5 GPIO |
| :--- | :--- | :--- |
| **INMP441 SCK (BCLK)** | I2S Serial Clock | **GPIO 4** |
| **INMP441 WS (LRCLK)** | I2S Word Select | **GPIO 5** |
| **INMP441 SD (DOUT)** | I2S Serial Data | **GPIO 1** |
| **SD_CS** | MicroSD Card Chip Select | **GPIO 14** |
| **RGB_BUILTIN** | Onboard Quantum Status LED | **GPIO 27** |

---

## 2. ⚡ 8-Task Modular FreeRTOS Architecture

1. **`Task 1 -> Display/UI (taskDisplayUI)`**: Renders the circular Arc Reactor HUD, voice waveform bars, Wi-Fi 6 signal meter, RAM telemetry, and word-wrapped AI answers, plus automatic hot-plug display detection every 8 seconds.
2. **`Task 2 -> Wi-Fi Manager (taskWiFiManager)`**: Broadcasts **`ESP32-C5-AI`** (`192.168.4.1`, password `12345678`), connects to **`Lost Case `**, and handles `ArduinoOTA` wireless updates.
3. **`Task 3 -> AI Communication (taskAICommunication)`**: Connects to the Unified Omni-Model + OpenJarvis Gateway (`http://10.22.163.78:8000/api/iot/chat`) with instant fallback to the **On-Device OpenJarvis Neural Engine** (Calculator, Weather, Persistent Memory, Diagnostics).
4. **`Task 4 -> Voice Recording (taskVoiceRecording)`**: Captures INMP441 I2S audio waveform telemetry and processes voice triggers.
5. **`Task 5 -> Touch Handling (taskTouchHandling)`**: Reads `XPT2046_Touchscreen` touch events on the 4 bottom HUD buttons (`[WIFI IP]`, `[WEATHER]`, `[QUANTUM]`, `[STATUS]`).
6. **`Task 6 -> BLE Communication (taskBLECommunication)`**: Manages Bluetooth Low Energy peripheral state.
7. **`Task 7 -> Storage Manager (taskStorageManager)`**: Persists chat history and OpenJarvis memory in `Preferences` NVS and `LittleFS` flash storage.
8. **`Task 8 -> System Monitor (taskSystemMonitor)`**: Drives the continuous **Neon Cyan & Quantum Gold RGB LED Flicker** on `RGB_BUILTIN` (GPIO 27) and monitors free RAM & CPU health.
