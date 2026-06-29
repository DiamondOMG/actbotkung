#include <Arduino.h>
#include <BleMouse.h>

BleMouse ble_mouse("ACTBOTKUNG", " Espressif", 100);

void process_command(String command_str) {
    if (!ble_mouse.isConnected()) {
        Serial.println("ERR: Bluetooth is not connected yet.");
        return;
    }

    char command_type = command_str.charAt(0);
    char dummy_char, button_char;
    int mouse_x, mouse_y, scroll_wheel;

    switch (command_type) {
        case 'M':
        case 'm':
            if (sscanf(command_str.c_str(), "%c %d %d", &dummy_char, &mouse_x, &mouse_y) == 3) {
                ble_mouse.move(mouse_x, mouse_y);
                Serial.printf("OK: Moved X:%d Y:%d\n", mouse_x, mouse_y);
            } else {
                Serial.println("ERR: Invalid Move format. Use: M <x> <y>");
            }
            break;

        case 'C':
        case 'c':
            if (sscanf(command_str.c_str(), "%c %c", &dummy_char, &button_char) == 2) {
                if (button_char == 'L' || button_char == 'l') { ble_mouse.click(MOUSE_LEFT); Serial.println("OK: Click Left"); }
                else if (button_char == 'R' || button_char == 'r') { ble_mouse.click(MOUSE_RIGHT); Serial.println("OK: Click Right"); }
                else if (button_char == 'M' || button_char == 'm') { ble_mouse.click(MOUSE_MIDDLE); Serial.println("OK: Click Middle"); }
                else { Serial.println("ERR: Invalid button. Use L, R, or M"); }
            }
            break;

        case 'S':
        case 's':
            if (sscanf(command_str.c_str(), "%c %d", &dummy_char, &scroll_wheel) == 2) {
                ble_mouse.move(0, 0, scroll_wheel);
                Serial.printf("OK: Scrolled %d\n", scroll_wheel);
            }
            break;
            
        case 'P':
        case 'p':
            if (sscanf(command_str.c_str(), "%c %c", &dummy_char, &button_char) == 2) {
                if (button_char == 'L' || button_char == 'l') { ble_mouse.press(MOUSE_LEFT); Serial.println("OK: Press Left"); }
                else if (button_char == 'R' || button_char == 'r') { ble_mouse.press(MOUSE_RIGHT); Serial.println("OK: Press Right"); }
            }
            break;
            
        case 'R':
        case 'r':
            if (sscanf(command_str.c_str(), "%c %c", &dummy_char, &button_char) == 2) {
                if (button_char == 'L' || button_char == 'l') { ble_mouse.release(MOUSE_LEFT); Serial.println("OK: Release Left"); }
                else if (button_char == 'R' || button_char == 'r') { ble_mouse.release(MOUSE_RIGHT); Serial.println("OK: Release Right"); }
            }
            break;

        default:
            Serial.println("ERR: Unknown command");
            break;
    }
}

void setup() {
    Serial.begin(115200);
    delay(6000); // ⚠️ บังคับ delay ไว้เผื่อเวลา flash_monitor
    
    Serial.println("Starting BLE Mouse2");
    ble_mouse.begin();
    Serial.println("Waiting for Bluetooth connection...");
}

void loop() {
    if (Serial.available() > 0) {
        String input_command = Serial.readStringUntil('\n');
        input_command.trim();
        if (input_command.length() > 0) {
            process_command(input_command);
        }
    }
}
