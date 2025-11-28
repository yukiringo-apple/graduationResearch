// ===== Arduino Braille Puncher (mm単位制御) =====
#include <Arduino.h>

// ---- Stepper設定 ----
const long stepsPerRevolution = 4096;
const float mmPerRev = 20.0;           
const float stepsPerMm = stepsPerRevolution / mmPerRev;

// 点字間隔
const float pitchX = 2.5; 
const float pitchY = 2.6; 
const float charPitch = 6.0;

// ピン設定
int xPins[4] = {2, 3, 4, 5};
int yPins[4] = {A0, A1, A2, A3};
const int SOL_PIN = 6;

// 半ステップ配列
int seq[8][4] = {
  {1,0,0,0},{1,1,0,0},{0,1,0,0},{0,1,1,0},
  {0,0,1,0},{0,0,1,1},{0,0,0,1},{1,0,0,1}
};

// ホームスイッチ
const int X_HOME_PIN = 7; // INPUT_PULLUP
const int Y_HOME_PIN = 8;

// 現在位置（mm）
float currentX = 0.0;
float currentY = 0.0;
float startX = 0.0;

// ステップインデックス
int xStepIndex = 0;
int yStepIndex = 0;

// 安全delay
void safeDelayMs(unsigned long ms){
  unsigned long start = millis();
  while(millis()-start < ms) delay(1);
}

// ステッパ制御
void stepMotor(int motorPins[], int idx){
  for(int i=0;i<4;i++) digitalWrite(motorPins[i], seq[idx][i]);
}

// X軸ステップ
void stepX(long steps, int delayMs=2){
  int dir = (steps >= 0) ? 1 : -1;
  long n = abs(steps);
  Serial.print("stepX: "); Serial.println(steps);
  for(long i=0;i<n;i++){
    xStepIndex = (dir == 1) ? (xStepIndex + 1) % 8 : (xStepIndex - 1 < 0 ? 7 : xStepIndex - 1);
    stepMotor(xPins, xStepIndex);
    safeDelayMs(delayMs);
  }
  currentX += (float)steps / stepsPerMm;
  Serial.print("currentX: "); Serial.println(currentX);
}

// Y軸ステップ
void stepY(long steps, int delayMs=2){
  int dir = (steps >= 0) ? 1 : -1;
  long n = abs(steps);
  Serial.print("stepY: "); Serial.println(steps);
  for(long i=0;i<n;i++){
    yStepIndex = (dir == 1) ? (yStepIndex + 1) % 8 : (yStepIndex - 1 < 0 ? 7 : yStepIndex - 1);
    stepMotor(yPins, yStepIndex);
    safeDelayMs(delayMs);
  }
  currentY += (float)steps / stepsPerMm;
  Serial.print("currentY: "); Serial.println(currentY);
}

// XY同時ステップ (Bresenham)
void stepXYSimultaneous(long stepsX, long stepsY, int delayMs){
  long ax = abs(stepsX);
  long ay = abs(stepsY);
  int dirX = (stepsX>=0)?1:-1;
  int dirY = (stepsY>=0)?1:-1;
  long steps = max(ax, ay);
  long err = 0;
  long dx = ax;
  long dy = ay;

  for(long i=0;i<steps;i++){
    bool doX=false, doY=false;
    if(ax >= ay){
      doX = (i < ax);
      err += dy;
      if(err >= ax){ doY = (i < ay); err -= ax; }
    } else {
      doY = (i < ay);
      err += dx;
      if(err >= ay){ doX = (i < ax); err -= ay; }
    }

    if(doX){
      xStepIndex = (dirX==1)?(xStepIndex+1)%8:(xStepIndex-1<0?7:xStepIndex-1);
      stepMotor(xPins, xStepIndex);
    }
    if(doY){
      yStepIndex = (dirY==1)?(yStepIndex+1)%8:(yStepIndex-1<0?7:yStepIndex-1);
      stepMotor(yPins, yStepIndex);
    }
    safeDelayMs(delayMs);
  }
  currentX += (float)stepsX/stepsPerMm;
  currentY += (float)stepsY/stepsPerMm;
}

// 高レベル移動
void moveTo(float targetX, float targetY, int delayMs=2){
  long sX = round((targetX-currentX)*stepsPerMm);
  long sY = round((targetY-currentY)*stepsPerMm);
  stepXYSimultaneous(sX, sY, delayMs);
}

// 打刻
void dot(){
  digitalWrite(SOL_PIN, HIGH);
  safeDelayMs(120);
  digitalWrite(SOL_PIN, LOW);
  safeDelayMs(50);
}

// X軸だけ原点へ
void returnXOnly() {
    unsigned long start = millis();
    while(digitalRead(X_HOME_PIN) == HIGH){
        xStepIndex = (xStepIndex-1<0?7:xStepIndex-1);
        stepMotor(xPins, xStepIndex);
        safeDelayMs(4);
        if(millis()-start > 3000) break;  // 3秒で強制停止
    }
    currentX = 0;
    startX = 0;
    Serial.println("X_HOME_DONE");
}


void returnYOnly() {
    unsigned long start = millis();
    while(digitalRead(Y_HOME_PIN) == HIGH){
        yStepIndex = (yStepIndex-1<0?7:yStepIndex-1);
        stepMotor(yPins, yStepIndex);
        safeDelayMs(4);
        if(millis()-start > 3000) break;  // 3秒で強制停止
    }
    currentY = 0;
    Serial.println("Y_HOME_DONE");
}



// XY両方原点へ
void returnHomeXY(){
  returnXOnly();
returnYOnly();

}

// ドット番号→座標
float moveToDot(int dotNumber, bool useStartX=true){
  float tx=0, ty=0;
  switch(dotNumber){
    case 1: tx=0;       ty=0; break;
    case 2: tx=0;       ty=pitchY; break;
    case 3: tx=0;       ty=pitchY*2; break;
    case 4: tx=pitchX;  ty=0; break;
    case 5: tx=pitchX;  ty=pitchY; break;
    case 6: tx=pitchX;  ty=pitchY*2; break;
  }
  float targetX = tx + (useStartX ? startX : 0);
  moveTo(targetX, ty);
}

const float DOT1_OFFSET_X = -0.5;  // 左上の手前 0.5mm
const float DOT1_OFFSET_Y = -0.5;

void returnToDot1(){
    // 1番点座標に移動（X/Y共に startX/startYを無視）
    moveToDot(1, false); 
    
    // X/Y軸ともに少し手前で止める
    moveTo(currentX + DOT1_OFFSET_X, currentY + DOT1_OFFSET_Y);
    
    // 文字列開始位置リセット
    startX = 0;
    currentX = 0;
    currentY = 0;
    
    Serial.println("Returned to Dot1 (with offset)");
}

// 文字間移動
void advanceChar() {
    startX += charPitch;
    Serial.print("Advanced to X: ");
    Serial.println(startX);
}


// 原点復帰（XY両方）
void returnHome() {
    moveTo(0,0);
    startX = 0;
}


void doHome(){
    // ---- X軸 ----
    if(currentX != 0){
        while(digitalRead(X_HOME_PIN) == HIGH){
            xStepIndex = (xStepIndex - 1 < 0 ? 7 : xStepIndex - 1);
            stepMotor(xPins, xStepIndex);
            safeDelayMs(4);
        }
        currentX = 0;
        startX = 0;
    }

    // ---- Y軸 ----
    if(currentY != 0){
        while(digitalRead(Y_HOME_PIN) == HIGH){
            yStepIndex = (yStepIndex - 1 < 0 ? 7 : yStepIndex - 1);
            stepMotor(yPins, yStepIndex);
            safeDelayMs(4);
        }
        currentY = 0;
    }

    Serial.println("HOMING_DONE");
}



// setup
void setup(){
  for(int i=0;i<4;i++){
    pinMode(xPins[i], OUTPUT);
    pinMode(yPins[i], OUTPUT);
  }
  pinMode(SOL_PIN, OUTPUT);
  pinMode(X_HOME_PIN, INPUT_PULLUP);
  pinMode(Y_HOME_PIN, INPUT_PULLUP);
  digitalWrite(SOL_PIN, LOW);
  Serial.begin(115200);
  Serial.println("READY");
}

// loop
void loop() {
  if(Serial.available()){
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if(cmd=="HOME") doHome();
    else if(cmd=="X_HOME") returnXOnly();
    else if(cmd=="Y_HOME") returnYOnly();
    else if(cmd=="DOT1") returnToDot1();   // ←追加
    else if(cmd=="CHAR_DONE") advanceChar();
    else if(cmd=="ALL_DONE") returnHome();
    else {
      int d = cmd.toInt();
      if(d>=1 && d<=6){ moveToDot(d); dot(); }
    }
  }
}
