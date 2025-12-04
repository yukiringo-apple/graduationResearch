# plotter.py

import serial
import time
import json
import os

COM_PORT = 'COM3'
BAUD_RATE = 115200
DELAY_DOT = 0.8

ser = None

def initialize():
    global ser
    try:
        ser = serial.Serial(COM_PORT, BAUD_RATE)
        time.sleep(2)
        print("Arduino 接続成功")
    except Exception as e:
        print("Arduino 接続失敗:", e)
        ser = None

# 点字ドット送信
def send_dot(d):
    global ser
    if ser is None:
        print("シリアル接続なし: send_dot停止")
        return
    if 1 <= d <= 6:
        ser.write(f"{d}\n".encode())
        print(f"Sent dot: {d}")
        time.sleep(DELAY_DOT)

def send_pattern(pattern):
    for i, dot_on in enumerate(pattern, start=1):
        if dot_on == 1:
            send_dot(i)

def send_braille_data(braille_data):
    global ser
    if ser is None:
        print("シリアル接続なし: send_braille_data停止")
        return
    for item in braille_data:
        send_pattern(item["pattern"])
    # 原点に戻す
    ser.write(b"HOME\n")
    time.sleep(2)
    print("原点に戻しました")
    return True

# 履歴ID指定で打刻
def send_history_by_id(target_id):
    file_path = 'historyText.json'
    if not os.path.exists(file_path):
        print("履歴ファイルなし")
        return
    with open(file_path, 'r', encoding='utf-8') as f:
        history = json.load(f)
    for item in history:
        if item["id"] == target_id:
            braille_data = item["brailleData"]
            send_braille_data(braille_data)
            return
    print("指定IDが見つかりません")
