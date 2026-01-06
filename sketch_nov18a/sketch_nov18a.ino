#include <Arduino.h>

// ---- Stepper設定 ----
const long stepsPerRevolution = 4096;
const float mmPerRev = 20.0;
const float stepsPerMm = stepsPerRevolution / mmPerRev;

// ---- 点字間隔 ----
const float pitchX = 1.4;
const float pitchY = 1.3;
const float charPitch = 3.0;
const float linePitch = 7.0; 

// ---- Z軸の上下幅 ----
const float Z_DOWN_MM = -10.0;
const float Z_UP_MM   = 10.0; 

// ---- ピン設定 ----
int xPins[4] = {2, 3, 4, 5};
int yPins[4] = {A0, A1, A2, A3};
int zPins[4] = {13, 12, 9, 11};

// ---- 半ステップ配列 ----
int seq[8][4] = {
  {1,0,0,0},{1,1,0,0},{0,1,0,0},{0,1,1,0},
  {0,0,1,0},{0,0,1,1},{0,0,0,1},{1,0,0,1}
};

// ---- 現在位置（mm）----
float currentX = 0.0;
float currentY = 0.0;
float startX   = 0.0;
float lineBaseY = 0.0;

// ---- 1行の最大文字数 ----
const int MAX_CHARS_PER_LINE = 6;

// ---- 現在の行の文字数 ----
int charCount = 0;

// ---- ステップインデックス ----
int xStepIndex = 0;
int yStepIndex = 0;
int zStepIndex = 0;

// ---- 左上微小オフセット ----
const float DOT1_OFFSET_X = -0.5;
const float DOT1_OFFSET_Y = -0.5;

// ===================================================

// 指定された時間分、処理を待機する
void safeDelayMs(unsigned long ms){
  // Ardinoを起動したら起動時間の計測を開始
  unsigned long start = millis();
  // 指定時間になるまで待機
  while(millis() - start < ms) delay(1);
}

// 指定されたモーターに駆動用の信号を送信
void stepMotor(int motorPins[], int idx){
  // 実際にモーターの磁石を一段階駆動
  for(int i=0;i<4;i++) digitalWrite(motorPins[i], seq[idx][i]);
}

// ---------------- X / Y / Z ----------------
// 指定されたステップ数だけモーターを駆動させる
void stepX(long steps, int delayMs=3){
  // 正転か反転なのかを判断(X軸だけは他のモーターと回る向きが違うため1と―1を入れ替えている)
  int dir = (steps >= 0) ? -1 : 1;
  for(long i=0;i<abs(steps);i++){
    // ステッピングモータの回転方法を決定、0から7パターンの信号パターンをループ
    xStepIndex = (dir==1)?(xStepIndex+1)%8:(xStepIndex+7)%8;
    // ピン番号と0～7のステップ数を送信
    stepMotor(xPins, xStepIndex);
    // 指定時間分待機
    safeDelayMs(delayMs);
  }
  // 動いた分の距離を加算して現在地を更新
  currentX += (float)steps / stepsPerMm;
}

// 指定されたステップ数だけモーターを駆動させる
void stepY(long steps, int delayMs=2){
  // 正転か反転なのかを判断
  int dir = (steps >= 0) ? 1 : -1;
  for(long i=0;i<abs(steps);i++){
    // ステッピングモータの回転方法を決定、0から7パターンの信号パターンをループ
    yStepIndex = (dir==1)?(yStepIndex+1)%8:(yStepIndex+7)%8;
    // ピン番号と0～7のステップ数を送信
    stepMotor(yPins, yStepIndex);
    // 指定時間分待機
    safeDelayMs(delayMs);
  }
  // 動いた分の距離を加算して現在地を更新
  currentY += (float)steps / stepsPerMm;
}

// 指定されたステップ数だけモーターを駆動させる
void stepZ(long steps, int delayMs=1){
  // 正転か反転なのかを判断
  int dir = (steps >= 0) ? 1 : -1;
  for(long i=0;i<abs(steps);i++){
    // ステッピングモータの回転方法を決定、0から7パターンの信号パターンをループ
    zStepIndex = (dir==1)?(zStepIndex+1)%8:(zStepIndex+7)%8;
    // ピン番号と0～7のステップ数を送信
    stepMotor(zPins, zStepIndex);
    // 指定時間分待機
    delay(delayMs);
  }
}

// 指定した絶対座標にX軸→Y軸の順に駆動
void moveTo(float x, float y){
  // X軸の移動
  long stepsX = round((x - currentX) * stepsPerMm);
  if(stepsX != 0) {
    stepX(stepsX, 3); // 少し余裕を持たせて delayMs=3
    delay(100);       // ★追加：X移動後の振動待ち（100ms）
  }

  // Y軸の移動
  long stepsY = round((y - currentY) * stepsPerMm);
  if(stepsY != 0) {
    stepY(stepsY, 3); // 少し余裕を持たせて delayMs=3
    delay(100);       // ★追加：Y移動後の振動待ち（100ms）
  }
}

// 点字のパターンに合わせて駆動
void dot(){
  // 指定した数値をステップ数に変換し、関数に渡す
  stepZ(Z_DOWN_MM * stepsPerMm);
  delay(100);
  // 指定した数値をステップ数に変換し、関数に渡す
  stepZ(Z_UP_MM * stepsPerMm);
  delay(100);
}

// 改行
void newLine(){
  moveTo(0, currentY);
  stepY(round(linePitch * stepsPerMm), 2);

  lineBaseY = currentY;   // ★ 行の基準Yを更新
  startX = 0;

  Serial.println("NEW_LINE");
}


// 点字(縦3点×横2列の計6点)のレイアウトを管理
void moveToDot(int d){
  float x = startX;
  float y = lineBaseY;   // ★ currentY を使わない

  if(d >= 4) x += pitchX;

  if(d == 2 || d == 5) y += pitchY;
  if(d == 3 || d == 6) y += pitchY * 2;

  moveTo(x, y);
}

// 次の文字の位置を管理
void advanceChar(){
  // ★ 文字終了時にYを行基準へ戻す
  moveTo(currentX, lineBaseY);

  charCount++;

  if(charCount >= MAX_CHARS_PER_LINE){
    newLine();
    charCount = 0;
  }else{
    startX += charPitch;
  }
}



// 最初の文字の一番目の部分を原点として復帰
void returnToDot1(){
  moveTo(DOT1_OFFSET_X, DOT1_OFFSET_Y);
  currentX = DOT1_OFFSET_X;
  currentY = DOT1_OFFSET_Y;

  lineBaseY = currentY;   // ★ 追加
  startX = 0;
  charCount = 0;

  Serial.println("RESET_TO_DOT1");
}



// ===================================================

void setup(){
  for(int i=0;i<4;i++){
    pinMode(xPins[i],OUTPUT);
    pinMode(yPins[i],OUTPUT);
    pinMode(zPins[i],OUTPUT);
  }
  Serial.begin(115200);
  Serial.println("READY");
}

void loop(){
  if(Serial.available()){
    String cmd=Serial.readStringUntil('\n');
    cmd.trim();

    // 次の文字移動する場合
    if(cmd=="CHAR_DONE") advanceChar();
    // 改行
    else if(cmd == "NEWLINE")newLine();
    // 原点復帰の場合
    else if(cmd=="DOT1") returnToDot1();
    else if(cmd == "SUBCELL_NEXT"){
    // 濁点 → 本体文字用に少し右へ
    startX += charPitch * -0.9;  // 好みで調整
    }
    // デバッグ用　X軸の単体駆動
    else if(cmd == "R" || cmd == "r"){               // 右へ 10mm
      stepX(-10 * stepsPerMm);
    }
    // デバッグ用　X軸の単体駆動
    else if(cmd == "L" || cmd == "l"){          // 左へ 10mm
      stepX(5 * stepsPerMm);
    }
        // デバッグ用　Y軸の単体駆動
    else if(cmd == "T" || cmd == "t"){               // 上へ 10mm
      stepY(-5 * stepsPerMm);
    }
    // デバッグ用　Y軸の単体駆動
    else if(cmd == "D" || cmd == "d"){          // 下へ 10mm
      stepY(10 * stepsPerMm);
    }
    else{
      int d=cmd.toInt();
      if(d>=1&&d<=6){
        moveToDot(d);
        dot();
      }
    }
  }
}




