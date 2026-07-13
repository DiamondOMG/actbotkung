#include "command_handler.h"

// ฟังก์ชันจำลองขยับเมาส์เป็นวงกลมในระดับฮาร์ดแวร์เพื่อทดสอบความลื่นไหลโดยตรง
static void run_circle_test() {
    int radius = 100;
    int steps = 60;
    int delay_ms = 25; // 25ms ต่อเฟรม (40Hz)

    float prev_x = radius * cos(0);
    float prev_y = radius * sin(0);

    for (int i = 0; i <= steps * 5; i++) { // หมุน 5 รอบ
        float angle = (i * 360.0 / steps);
        float rad = angle * M_PI / 180.0;

        float curr_x = radius * cos(rad);
        float curr_y = radius * sin(rad);

        int dx = (int)(curr_x - prev_x);
        int dy = (int)(curr_y - prev_y);

        prev_x = curr_x;
        prev_y = curr_y;

        if (dx != 0 || dy != 0) {
            ble_combo.move(dx, dy);
        }
        delay(delay_ms);
    }
}

void process_command(String command_str) {
    // Handle TEST command
    if (command_str.equalsIgnoreCase("TEST")) {
        Serial.println("OK: Running internal circle test (5 rounds)...");
        run_circle_test();
        Serial.println("OK: Test finished.");
        return;
    }

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
