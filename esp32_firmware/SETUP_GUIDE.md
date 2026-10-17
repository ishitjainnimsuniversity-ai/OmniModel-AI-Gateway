# 🛠️ Complete ESP32 + MSP2402 (ILI9341 2.4" SPI) Preparation & Flash Guide

This complete checklist enables you to **prepare, import libraries, configure your Arduino environment, and flash your ESP32 right now** — even before the physical screen arrives in the mail!

---

## 1. 📦 Hardware Checklist Needed

### A. What you already have:
1. **ESP32 Board** (e.g., ESP32-C3 / ESP32-WROOM-32 / ESP32-S3 / ESP32-C6).
2. **MSP2402 / QD241801 2.4-inch ILI9341 SPI Screen** (on order/in transit).

### B. Accessories to prepare right now:
1. **USB Data Cable**: Make sure it is a high-quality **Data Cable** (Micro-USB or USB-C, depending on your ESP32 port), NOT a charge-only cable.
2. **DuPont Jumper Wires**:
   - **14x Female-to-Female** (or Female-to-Male if using a breadboard) jumper wires.
   - 9 wires for the ILI9341 Display (VCC, GND, CS, RESET, DC, MOSI, SCK, LED, MISO).
   - 5 wires for the XPT2046 Touch Screen (T_CLK, T_CS, T_DIN, T_DO, T_IRQ).
3. **Half-size Breadboard** *(Optional but makes wiring much easier)*.

---

## 2. 💻 Software & Drivers Checklist

### Step 1: Install Arduino IDE 2.x
- Download from official site: [https://www.arduino.cc/en/software](https://www.arduino.cc/en/software)

### Step 2: Install USB-to-UART Driver (If your PC doesn't detect the ESP32)
Depending on the USB chip on your ESP32 board:
- **CH340 / CH341**: [WCH Official Driver](http://www.wch-ic.com/downloads/CH341SER_EXE.html)
- **CP2102 / CP2104**: [Silicon Labs CP210x Driver](https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers)
- If your board is an **ESP32-C3 / ESP32-S3** with native USB, no driver is usually needed on Windows 10/11.

---

## 3. ⚙️ Arduino IDE Setup

### Step 1: Add ESP32 Board URL
1. Open Arduino IDE.
2. Go to **File -> Preferences**.
3. In **Additional boards manager URLs**, paste:
   ```text
   https://espressif.github.io/arduino-esp32/package_esp32_index.json
   ```
4. Click **OK**.

### Step 2: Install the ESP32 Board Package
1. Go to **Tools -> Board -> Boards Manager** (or click the Board icon on the left panel).
2. Search for **`esp32`** by **Espressif Systems**.
3. Click **Install** (Version 2.0.14 or 3.x).

### Step 3: Install Required Libraries
Open **Tools -> Manage Libraries** (or `Ctrl+Shift+I`):
1. Search **`TFT_eSPI`** by Bodmer -> Click **Install**.
2. Search **`ArduinoJson`** by Benoît Blanchon -> Click **Install** (v7.x or v6.x).

---

## 4. 📁 Configure `TFT_eSPI` Library (Crucial Step!)

To tell the `TFT_eSPI` library to use the **ILI9341** display and your exact ESP32 pins:

1. Open your computer's file explorer and locate your Arduino libraries folder:
   - On Windows: `C:\Users\<YourUser>\Documents\Arduino\libraries\TFT_eSPI\`
2. In this folder, locate the file named **`User_Setup.h`**.
3. Replace its contents with the pre-configured [User_Setup.h](./User_Setup.h) file provided in this folder!

---

## 5. 🔌 Wiring Pinout Table (When Screen Arrives)

When the **MSP2402 / QD241801** display arrives, wire it according to this table:

| MSP2402 Pin Label | Pin Function | Standard ESP32 (WROOM-32) | ESP32-C3 | Wire Color Suggestion |
| :--- | :--- | :--- | :--- | :--- |
| **VCC** | Power (3.3V or 5V) | `3V3` or `5V` (Check display LDO) | `3V3` | 🔴 Red |
| **GND** | Ground | `GND` | `GND` | ⚫ Black |
| **CS** | LCD Chip Select | `GPIO 15` | `GPIO 7` | 🟠 Orange |
| **RESET** | LCD Reset | `GPIO 4` | `GPIO 10` | 🟡 Yellow |
| **DC / RS** | Data / Command | `GPIO 2` | `GPIO 6` | 🟢 Green |
| **MOSI / SDI** | SPI Data In | `GPIO 23` | `GPIO 4` | 🔵 Blue |
| **SCK / SCLK** | SPI Clock | `GPIO 18` | `GPIO 5` | 🟣 Purple |
| **LED / BL** | Backlight Control | `3V3` (or GPIO 21) | `3V3` | ⚪ White |
| **MISO / SDO** | SPI Data Out | `GPIO 19` | `GPIO 3` | 🔘 Grey |
| **T_CLK** | Touch Clock | `GPIO 18` (Shared SCK) | `GPIO 5` | Shared |
| **T_CS** | Touch Chip Select | `GPIO 5` | `GPIO 1` | 🟤 Brown |
| **T_DIN** | Touch Data In | `GPIO 23` (Shared MOSI) | `GPIO 4` | Shared |
| **T_DO** | Touch Data Out | `GPIO 19` (Shared MISO) | `GPIO 3` | Shared |
| **T_IRQ** | Touch Interrupt | `GPIO 22` (Optional) | `GPIO 0` | Optional |

---

## 6. 🚀 How to Flash and Test Right Now (Pre-Screen Test)

You do **NOT** have to wait for the screen to test your ESP32 with GENESIS AI 5.0!

1. Open [esp32_firmware.ino](./esp32_firmware.ino) in Arduino IDE.
2. In the code, set your WiFi credentials:
   ```cpp
   const char* WIFI_SSID     = "Your_WiFi_Name";
   const char* WIFI_PASSWORD = "Your_WiFi_Password";
   ```
3. Set your Gateway URL:
   ```cpp
   // If testing via your live Vercel gateway:
   const char* GATEWAY_IOT_URL = "https://OmniModel-AI-Gateway.vercel.app/api/iot/chat";
   
   // Or if testing via your local PC server:
   // const char* GATEWAY_IOT_URL = "http://192.168.1.xxx:8000/api/iot/chat";
   ```
4. Plug your **ESP32** into your PC via USB.
5. In Arduino IDE:
   - Select Board: **Tools -> Board -> ESP32 Arduino -> ESP32 Dev Module** (or **ESP32C3 Dev Module**).
   - Select Port: **Tools -> Port -> COMx** (the COM port of your ESP32).
6. Click **Upload** (Arrow icon).
7. Once flashing is done, open **Tools -> Serial Monitor** and set baud rate to **`115200`**.
8. You will see:
   ```text
   🚀 GENESIS AI 5.0 - ESP32 Hardware Client Starting
   Connecting to WiFi...
   ✅ WiFi Connected! IP: 192.168.1.84
   📡 Contacting Gateway: https://...
   ✨ [GENESIS AI Answer]: Quantum computing uses qubits in superposition to solve problems...
   💬 Enter any question in the Serial Monitor and press Enter:
   ```
9. You can type any question into the Serial Monitor box and press Enter — your ESP32 will talk to GENESIS AI and display the reply in the console!
10. **When your 2.4" screen arrives:** Simply plug the jumper wires into the ESP32 according to the table above. The exact same firmware will automatically output the text onto your ILI9341 screen!
