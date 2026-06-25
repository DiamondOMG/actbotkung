#include <Arduino.h>
#include <BleCombo.h>

#define LED_PIN 8 // Onboard LED of ESP32-C3 Super Mini (Active Low)

// สร้าง Instance ของ Keyboard และ Mouse โดยแชร์ BLE Connection เดียวกันผ่าน NimBLE
BleComboKeyboard bleKeyboard("ActbotKung BLE", "OMG", 100);
BleComboMouse bleMouse(&bleKeyboard);

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, HIGH); // Turn off LED initially (Active Low)
  delay(3000);

  Serial.println("Starting NimBLE Combo Device (Mouse & Keyboard)");

  // กะพริบไฟ 3 ครั้งบ่งบอกสถานะเริ่มต้นการบูต
  for (int i = 0; i < 3; i++) {
    digitalWrite(LED_PIN, LOW); delay(100);
    digitalWrite(LED_PIN, HIGH); delay(100);
  }

  bleKeyboard.begin();
  // bleMouse ไม่ต้องเรียก begin() แยกต่างหากเพราะแชร์ connection ร่วมกับ bleKeyboard

  Serial.println("BLE Setup Complete!");

  // เปิดไฟค้าง 1 วินาทีบอกสถานะว่า BLE เริ่มต้นเสร็จสิ้นโดยไม่ค้าง
  digitalWrite(LED_PIN, LOW);
  delay(1000);
  digitalWrite(LED_PIN, HIGH);
}


void blinkLED(int duration_ms) {
  digitalWrite(LED_PIN, LOW); // Turn on
  delay(duration_ms);
  digitalWrite(LED_PIN, HIGH); // Turn off
}

void processCommand(String command) {
  command.trim();
  if (command.length() == 0) return;

  Serial.print("Received command: ");
  Serial.println(command);
  blinkLED(50); // Flash LED on command receipt

  bool connected = bleKeyboard.isConnected();

  // --- [หมวดควบคุม TV ผ่าน BLE Mouse/Keyboard จำลอง] ---
  if (command.startsWith("TV:")) {
    String action = command.substring(3);
    if (!connected) {
      Serial.println("Error: BLE not connected!");
      return;
    }

    if (action == "power") {
      Serial.println("Executing TV Power command");
    } 
    else if (action == "volume_up") {
      bleKeyboard.write(KEY_MEDIA_VOLUME_UP);
      Serial.println("Executing TV Volume Up");
    } 
    else if (action == "volume_down") {
      bleKeyboard.write(KEY_MEDIA_VOLUME_DOWN);
      Serial.println("Executing TV Volume Down");
    }
    else if (action == "mute") {
      bleKeyboard.write(KEY_MEDIA_MUTE);
      Serial.println("Executing TV Mute");
    }
    else if (action == "click") {
      bleMouse.click(MOUSE_LEFT);
      Serial.println("Executing TV Click");
    }
    else if (action == "disconnect") {
      bleKeyboard.end(); // ปิดสแต็กเพื่อสั่งตัดการเชื่อมต่อทันที
      delay(500);
      bleKeyboard.begin(); // เปิดสแต็กใหม่เพื่อรอรับการเชื่อมต่อรอบใหม่
      Serial.println("Executing BLE Disconnect");
    }
  }
  // --- [หมวดจำลอง BLE Mouse ขยับเมาส์ระยะไกล] ---
  else if (command.startsWith("BLE_MOUSE:")) {
    if (!connected) {
      Serial.println("Error: BLE not connected!");
      return;
    }
    
    String action = command.substring(10);
    if (action.startsWith("move,")) {
      // รูปแบบ: BLE_MOUSE:move,x,y (เช่น BLE_MOUSE:move,10,-5)
      String coords = action.substring(5); // ตัด "move,"
      int commaPos = coords.indexOf(',');
      if (commaPos != -1) {
        int x_val = coords.substring(0, commaPos).toInt();
        int y_val = coords.substring(commaPos + 1).toInt();
        bleMouse.move(x_val, y_val);
        Serial.printf("BLE Mouse Move: %d, %d\n", x_val, y_val);
      }
    } 
    else if (action == "click") {
      bleMouse.click(MOUSE_LEFT);
      Serial.println("BLE Mouse Click Left");
    } 
    else if (action == "right_click") {
      bleMouse.click(MOUSE_RIGHT);
      Serial.println("BLE Mouse Click Right");
    }
  }
  // --- [คำสั่งเช็คสถานะ BLE] ---
  else if (command == "STATUS") {
    bool ble_connected = bleKeyboard.isConnected();
    Serial.printf("BLE_STATUS:%s\n", ble_connected ? "connected" : "disconnected");
  }
  else {
    Serial.println("Unknown command pattern.");
  }
}

void loop() {
  static unsigned long last_check = 0;
  bool connected = bleKeyboard.isConnected();

  if (millis() - last_check > 2000) {
    last_check = millis();
    if (!connected) {
      // กะพริบสั้นๆ แสดงสถานะรอเชื่อมต่อ
      digitalWrite(LED_PIN, LOW); delay(50); digitalWrite(LED_PIN, HIGH); delay(100);
      digitalWrite(LED_PIN, LOW); delay(50); digitalWrite(LED_PIN, HIGH);
    } else {
      // ไฟติดสว่างแสดงสถานะเชื่อมต่อสำเร็จ
      digitalWrite(LED_PIN, LOW); 
    }
  }

  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    processCommand(command);
  }
}
