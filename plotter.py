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


def send_dot(d):
    global ser
    if ser is None:
        return
    if 1 <= d <= 6:
        ser.write(f"{d}\n".encode())
        time.sleep(DELAY_DOT)


def send_pattern(pattern):
    for i, dot_on in enumerate(pattern, start=1):
        if dot_on == 1:
            send_dot(i)


def send_braille_data(braille_data):
    global ser
    if ser is None:
        return False

    for item in braille_data:
        send_pattern(item["pattern"])

    ser.write(b"HOME\n")
    time.sleep(2)
    return True


def send_history_by_id(target_id, status_dict):
    file_path = 'historyText.json'

    if not os.path.exists(file_path):
        status_dict[target_id] = "error"
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        history = json.load(f)

    for item in history:
        if item["id"] == target_id:
            send_braille_data(item["brailleData"])
            status_dict[target_id] = "done"   # ✅ 完了通知
            return

    status_dict[target_id] = "error"
