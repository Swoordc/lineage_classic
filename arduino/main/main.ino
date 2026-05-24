#include <Keyboard.h>
#include <Mouse.h>

void setup() {
  Serial.begin(9600);
  Keyboard.begin();
  Mouse.begin();
  
  pinMode(LED_BUILTIN, OUTPUT);
  for (int i = 0; i < 3; i++) {
    digitalWrite(LED_BUILTIN, HIGH);
    delay(100);
    digitalWrite(LED_BUILTIN, LOW);
    delay(100);
  }
  
  Serial.println("Arduino Ready (Keyboard + Mouse)");
}

void loop() {
  if (Serial.available() >= 1) {
    char cmd = Serial.read();
    
    switch (cmd) {
      // ========== 键盘命令（原有功能） ==========
      case 'p':   // 按下按键
        if (Serial.available()) {
          uint8_t key = Serial.read();
          Keyboard.press(key);
        }
        break;
      case 'r':   // 释放按键
        if (Serial.available()) {
          uint8_t key = Serial.read();
          Keyboard.release(key);
        }
        break;
      case 'c':   // 点击按键（按下+释放）
        if (Serial.available()) {
          uint8_t key = Serial.read();
          Keyboard.press(key);
          delay(30);
          Keyboard.release(key);
        }
        break;
        
      // ========== 鼠标命令（新增功能） ==========
      case 'm':   // 鼠标左键点击（按下+释放）
        Mouse.click(MOUSE_LEFT);
        break;
      case 'd':   // 鼠标左键按下
        Mouse.press(MOUSE_LEFT);
        break;
      case 'u':   // 鼠标左键释放
        Mouse.release(MOUSE_LEFT);
        break;
    }
  }
}