/*
 * Lineage Classic - Arduino HID Keyboard
 *
 * 接收串口指令模拟 F1-F12 按键。
 * 协议: 2 字节 — [命令] [键码]
 *   命令: 'c'=点击, 'p'=按下, 'r'=释放
 *   键码: 0xC2(F1) ~ 0xCD(F12)
 *
 * 需要 ATmega32U4 系列的板子 (Leonardo / Micro / Pro Micro)
 */

#include <Keyboard.h>

// F1-F12 键码映射 (匹配 Python 端 KEY_CODES)
uint8_t codeToKey(uint8_t code) {
  switch (code) {
    case 0xC2: return KEY_F1;
    case 0xC3: return KEY_F2;
    case 0xC4: return KEY_F3;
    case 0xC5: return KEY_F4;
    case 0xC6: return KEY_F5;
    case 0xC7: return KEY_F6;
    case 0xC8: return KEY_F7;
    case 0xC9: return KEY_F8;
    case 0xCA: return KEY_F9;
    case 0xCB: return KEY_F10;
    case 0xCC: return KEY_F11;
    case 0xCD: return KEY_F12;
    default:  return 0;
  }
}

void setup() {
  Serial.begin(9600);
  Keyboard.begin();
}

void loop() {
  if (Serial.available() >= 2) {
    char cmd = Serial.read();
    uint8_t key = codeToKey(Serial.read());

    if (key == 0) return;

    switch (cmd) {
      case 'c':  // 点击 (按下 + 释放)
        Keyboard.press(key);
        delay(50);
        Keyboard.release(key);
        break;
      case 'p':  // 按下 (不释放)
        Keyboard.press(key);
        break;
      case 'r':  // 释放
        Keyboard.release(key);
        break;
    }
  }
}
