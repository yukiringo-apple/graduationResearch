import serial
import time
import json
import os

COM_PORT = 'COM3'
BAUD_RATE = 115200
DELAY_DOT = 0.8

ser = None

# -- 数字判定 --
def is_number(ch):
    return ch.isdigit() or ('０' <= ch <= '９')

# 全角数字→半角
def normalize_digit(ch):
    if '０' <= ch <= '９':
        return str(ord(ch) - ord('０'))
    return ch

# -- 英字判定 --
def is_english(ch):
    return ('a' <= ch <= 'z') or ('A' <= ch <= 'Z')


# BRAILLE 読み込み
with open("brailleConverter.json", "r", encoding="utf-8") as f:
    BRAILLE = json.load(f)


# -- flatten（濁音・複合対応） --
def flatten_pattern(ch):
    pattern = BRAILLE[ch]

    if all(isinstance(x, int) for x in pattern):
        return pattern

    result = []
    for p in pattern:
        result += flatten_pattern(p)
    return result


def initialize():
    global ser
    try:
        ser = serial.Serial(COM_PORT, BAUD_RATE)
        time.sleep(2)
        print("Arduino 接続成功")
    except Exception as e:
        print("Arduino 接続失敗:", e)
        ser = None


# --- 点送信 ---
def send_dot(d):
    global ser
    if ser is None:
        print("シリアル接続なし")
        return
    if 1 <= d <= 6:
        ser.write(f"{d}\n".encode())
        print(f"Sent dot: {d}")
        time.sleep(DELAY_DOT)


# --- 1パターン送信 ---
def send_pattern(pattern):
    for idx, on in enumerate(pattern):
        if on == 1:
            dot = (idx % 6) + 1
            send_dot(dot)


# --- 1文字処理（数字・英字対応） ---
def send_char(ch, numeric_mode, english_mode):
    # --- 数字チェック ---
    if is_number(ch):
        ch = normalize_digit(ch)

        # 数字モードでなければ数符を出す
        if not numeric_mode:
            send_pattern(BRAILLE["数符"])  # 数符
            print("数符 ⠼ 出力")

        # 数字 → a〜j へ変換
        digit_to_alpha = {
            "1": "a", "2": "b", "3": "c", "4": "d", "5": "e",
            "6": "f", "7": "g", "8": "h", "9": "i", "0": "j"
        }
        send_pattern(flatten_pattern(digit_to_alpha[ch]))
        return True, False  # numeric=True, english=False


    # -------- 英字 --------
    if is_english(ch):

        # 英字モードでなければ英字符を出す
        if not english_mode:
            send_pattern(BRAILLE["外字符"])  # 英字符
            print("英字符 ⠰ 出力")
            
        # 点字を打刻
        send_pattern(flatten_pattern(ch))

        return False, True  # numeric=False, english=True


    # --- その他の文字（日本語など） ---
    if ch in BRAILLE:
        send_pattern(flatten_pattern(ch))
    else:
        print("未対応文字:", ch)

    # 英字モードも数字モードも解除
    return False, False


# --- 整文送信 ---
def send_braille_data(braille_data):

    numeric_mode = False
    english_mode = False

    for item in braille_data:
        ch = item["char"]
        numeric_mode, english_mode = send_char(ch, numeric_mode, english_mode)

    ser.write(b"HOME\n")
    time.sleep(2)
    print("原点へ戻しました")


# --- 履歴IDから送信 ---
def send_history_by_id(target_id):
    path = 'historyText.json'
    if not os.path.exists(path):
        print("履歴ファイルがありません")
        return

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for item in data:
        if item["id"] == target_id:
            send_braille_data(item["brailleData"])
            return

    print("指定IDが見つかりません")
