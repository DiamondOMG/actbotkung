#pragma once

#include <Arduino.h>
#include <BleCombo.h>

// อ้างอิงอ็อบเจกต์ ble_combo จาก main.cpp
extern BleCombo ble_combo;

// ขาเชื่อมต่อของ LED
#define LED_PIN 48

// ประกาศฟังก์ชันประมวลผลคำสั่ง Serial
void process_command(String command_str);
