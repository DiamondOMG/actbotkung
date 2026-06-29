#include <Arduino.h>
#include <BleCombo.h>

#define LED_PIN 8

BleCombo ble_combo("ACTBOTKUNG", "Espressif", 100);

bool was_connected = false;
unsigned long last_blink_time = 0;
bool led_state = false;

void process_command(String command_str) {
    // Handle STATUS command
    if (command_str.equalsIgnoreCase("STATUS")) {
        Serial.printf("BLE_STATUS:%s\n", ble_combo.isConnected() ? "connected" : "disconnected");
        return;
    }

    // Check BLE connection before processing HID actions
    if (!ble_combo.isConnected()) {
        Serial.println("ERR: Bluetooth is not connected yet.");
        return;
    }

    // Handle TV Command
    if (command_str.startsWith("TV:") || command_str.startsWith("tv:") || 
        command_str.startsWith("TV ") || command_str.startsWith("tv ")) {
        String action = command_str.substring(3);
        action.trim();

        if (action.equalsIgnoreCase("volume_up")) {
            ble_combo.write(KEY_MEDIA_VOLUME_UP);
            Serial.println("OK: TV Volume Up");
        } else if (action.equalsIgnoreCase("volume_down")) {
            ble_combo.write(KEY_MEDIA_VOLUME_DOWN);
            Serial.println("OK: TV Volume Down");
        } else if (action.equalsIgnoreCase("mute")) {
            ble_combo.write(KEY_MEDIA_MUTE);
            Serial.println("OK: TV Mute");
        } else if (action.equalsIgnoreCase("play_pause")) {
            ble_combo.write(KEY_MEDIA_PLAY_PAUSE);
            Serial.println("OK: TV Play/Pause");
        } else if (action.equalsIgnoreCase("click")) {
            ble_combo.click(MOUSE_LEFT);
            Serial.println("OK: TV Click (Mouse Left)");
        } else {
            Serial.printf("ERR: Unknown TV action '%s'. Use: volume_up, volume_down, mute, play_pause, click\n", action.c_str());
        }
        return;
    }

    // Handle Raw Mouse/Keyboard Command
    char command_type = command_str.charAt(0);
    char dummy_char, button_char;
    int mouse_x, mouse_y, scroll_wheel;

    switch (command_type) {
        case 'M':
        case 'm':
            if (sscanf(command_str.c_str(), "%c %d %d", &dummy_char, &mouse_x, &mouse_y) == 3) {
                ble_combo.move(mouse_x, mouse_y);
                Serial.printf("OK: Moved X:%d Y:%d\n", mouse_x, mouse_y);
            } else {
                Serial.println("ERR: Invalid Move format. Use: M <x> <y>");
            }
            break;

        case 'C':
        case 'c':
            if (sscanf(command_str.c_str(), "%c %c", &dummy_char, &button_char) == 2) {
                if (button_char == 'L' || button_char == 'l') { ble_combo.click(MOUSE_LEFT); Serial.println("OK: Click Left"); }
                else if (button_char == 'R' || button_char == 'r') { ble_combo.click(MOUSE_RIGHT); Serial.println("OK: Click Right"); }
                else if (button_char == 'M' || button_char == 'm') { ble_combo.click(MOUSE_MIDDLE); Serial.println("OK: Click Middle"); }
                else { Serial.println("ERR: Invalid button. Use L, R, or M"); }
            }
            break;

        case 'S':
        case 's':
            if (sscanf(command_str.c_str(), "%c %d", &dummy_char, &scroll_wheel) == 2) {
                ble_combo.move(0, 0, scroll_wheel);
                Serial.printf("OK: Scrolled %d\n", scroll_wheel);
            }
            break;
            
        case 'P':
        case 'p':
            if (sscanf(command_str.c_str(), "%c %c", &dummy_char, &button_char) == 2) {
                if (button_char == 'L' || button_char == 'l') { ble_combo.press(MOUSE_LEFT); Serial.println("OK: Press Left"); }
                else if (button_char == 'R' || button_char == 'r') { ble_combo.press(MOUSE_RIGHT); Serial.println("OK: Press Right"); }
            }
            break;
            
        case 'R':
        case 'r':
            if (sscanf(command_str.c_str(), "%c %c", &dummy_char, &button_char) == 2) {
                if (button_char == 'L' || button_char == 'l') { ble_combo.release(MOUSE_LEFT); Serial.println("OK: Release Left"); }
                else if (button_char == 'R' || button_char == 'r') { ble_combo.release(MOUSE_RIGHT); Serial.println("OK: Release Right"); }
            }
            break;

        default:
            Serial.println("ERR: Unknown command");
            break;
    }
}

void setup() {
    Serial.begin(115200);
    pinMode(LED_PIN, OUTPUT);
    digitalWrite(LED_PIN, HIGH); // LED off (active LOW)

    delay(6000); // Wait for flash monitor
    
    Serial.println("Starting BLE Combo (Keyboard + Mouse)...");
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

    // Process Serial Input
    if (Serial.available() > 0) {
        String input_command = Serial.readStringUntil('\n');
        input_command.trim();
        if (input_command.length() > 0) {
            process_command(input_command);
        }
    }
}
