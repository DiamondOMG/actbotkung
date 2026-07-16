#include <Arduino.h>
#include <BleCombo.h>
#include <BLEDevice.h>
#include "command_handler.h"

BleCombo ble_combo("ACTBOTKUNG2", "Espressif", 100);

bool was_connected = false;
unsigned long last_blink_time = 0;
bool led_state = false;

void setup() {
    Serial.begin(115200);
    pinMode(LED_PIN, OUTPUT);
    digitalWrite(LED_PIN, HIGH); // LED off (active LOW)

    delay(6000); // Wait for flash monitor
    
    Serial.println("=========================================");
    Serial.println("Starting BLE Combo (Keyboard + Mouse)...");
    
    // ตรวจสอบและพิมพ์ข้อมูล PSRAM / Heap
    if (psramFound()) {
        Serial.println("PSRAM status: FOUND");
        Serial.printf("PSRAM Total Size: %.2f MB\n", ESP.getPsramSize() / (1024.0 * 1024.0));
        Serial.printf("PSRAM Free Size : %.2f MB\n", ESP.getFreePsram() / (1024.0 * 1024.0));
    } else {
        Serial.println("PSRAM status: NOT FOUND (Disabled/Unavailable)");
    }
    Serial.printf("Internal Free Heap: %.2f KB\n", ESP.getFreeHeap() / 1024.0);
    Serial.println("=========================================");

    ble_combo.begin();
    Serial.println("Waiting for Bluetooth connection...");
}

void loop() {
    bool current_connected = ble_combo.isConnected();

    // Track state change
    if (current_connected != was_connected) {
        was_connected = current_connected;
        if (current_connected) {
            Serial.println("BLE_STATUS:connected");
        } else {
            Serial.println("BLE_STATUS:disconnected");
            digitalWrite(LED_PIN, HIGH); // LED off
            
            // ป้องกันปัญหา Bluedroid stack ค้างด้วยการหน่วงเวลาแล้วสั่งเริ่มโฆษณา (Advertising) ใหม่แบบ Static
            delay(1000);
            Serial.println("Restarting BLE advertising...");
            BLEDevice::startAdvertising();
        }
    }

    // Blink LED when connected
    if (current_connected) {
        unsigned long current_time = millis();
        if (current_time - last_blink_time >= 500) {
            last_blink_time = current_time;
            led_state = !led_state;
            digitalWrite(LED_PIN, led_state ? LOW : HIGH);
        }
    }

    // Process Serial Input (Non-blocking)
    static String input_buffer = "";
    while (Serial.available() > 0) {
        char c = Serial.read();
        if (c == '\n') {
            input_buffer.trim();
            if (input_buffer.length() > 0) {
                process_command(input_buffer);
            }
            input_buffer = "";
        } else {
            input_buffer += c;
        }
    }
}
