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
    """
    点字定義を「1マス分の点字（6要素の0/1リスト）」のリストに展開する。
    例: "か" -> [[1, 0, 0, 0, 0, 1]]
    例: "が" -> [[0, 0, 0, 0, 1, 0], [1, 0, 0, 0, 0, 1]]
    """
    # 1. ch が文字列（辞書のキー）なら、辞書から中身を取り出す
    if isinstance(ch, str):
        data = BRAILLE.get(ch)
        if data is None:
            print(f"未定義文字: {ch}")
            return []
    else:
        data = ch

    # 2. data が [1, 0, 0, 0, 0, 1] のような「点字パターンそのもの」の場合
    # すべての要素が int (0か1) なら、それをリストに包んで返す
    if isinstance(data, list) and all(isinstance(x, int) for x in data):
        return [data]

    # 3. data が ["゛", "か"] のような「要素のリスト」の場合
    result = []
    if isinstance(data, list):
        for item in data:
            # 各要素に対して再帰的に処理
            result.extend(flatten_pattern(item))
            
    return result



def initialize():
    global ser
    try:
        ser = serial.Serial(COM_PORT, BAUD_RATE)
        time.sleep(2)
        print("Arduino 接続成功")
    except serial.SerialException as e: # ✅ serial.SerialExceptionを補足
        # デバッグ用詳細メッセージ
        print(f"❌ Arduino 接続失敗 (SerialException): COMポート'{COM_PORT}'を確認してください。詳細: {e}")
        ser = None
    except Exception as e:
        # その他の例外
        print(f"❌ Arduino 接続失敗 (その他エラー): 詳細: {e}")
        ser = None


# --- 点送信 ---
def send_dot(d):
    global ser
    if ser is None:
        raise RuntimeError("シリアル未接続")
        print("シリアル接続なし")
        return
    if 1 <= d <= 6:
        ser.write(f"{d}\n".encode())
        ser.flush()           # ★必須
        wait_ack("DOT_OK")
        time.sleep(0.05) 
        print(f"Sent dot: {d}")
        time.sleep(DELAY_DOT)


# --- 1パターン送信 ---
def send_pattern(pattern):
    for dot, on in enumerate(pattern, start=1):
        if on:
            send_dot(dot)

def wait_ack(expected, timeout=5.0):
    start = time.time()
    while True:
        if time.time() - start > timeout:
            raise TimeoutError(f"ACK待ちタイムアウト: {expected}")

        line = ser.readline().decode().strip()
        if line == expected:
            return


# --- 1文字処理（数字・英字対応） ---
def send_char(ch):
    patterns = flatten_pattern(ch)
    if not patterns:
        return

    for i, p in enumerate(patterns):
        # 1マス分の点字を打つ
        for dot, on in enumerate(p, start=1):
            if on:
                send_dot(dot)

        # ★最後以外は次のマスへ
        if i < len(patterns) - 1:
            ser.write(b"CHAR_DONE\n")
            ser.flush()
            wait_ack("CHAR_OK")

    # 最後の1回だけ「この文字は終わり」
    ser.write(b"CHAR_DONE\n")
    ser.flush()
    wait_ack("CHAR_OK")




def send_braille_data(braille_data,chars_per_line=7):
    try:
        go_home()

        count = 0
        for item in braille_data:
            send_char(item["char"])
            count += 1

            if count == chars_per_line:
                send_newline()
                count = 0

        go_home()

    except serial.SerialTimeoutException as e:
        raise RuntimeError(f"シリアル書き込みタイムアウト。\n機器の応答を確認してください。詳細: {e}")
    except Exception as e:
        raise RuntimeError(f"打刻中の予期せぬエラーが発生しました。\n詳細: {e}")

    # return_to_dot1()



    # for item in braille_data:
    #     ch = item["char"]
    #     numeric_mode, english_mode = send_char_with_advance(ch, numeric_mode, english_mode)

    # 打刻後、左上の六点1番目に戻る
    # 多分要らない
    # if ser is not None:
    #     ser.write(b"DOT1\n")
    #     time.sleep(1)
    #     print("Returned to Dot 1")
        
    # return_to_dot1()  # 打刻後に六点1番目に戻る
    # 多分要らない

def return_to_dot1():
    """打刻後、六点1番目（左上）に戻る"""
    if ser is not None:
        ser.write(b"DOT1\n")  # Arduino 側で startX=0 にして左上へ
        time.sleep(1)          # 移動完了まで少し待つ
        print("Returned to Dot 1")

def go_home():
    ser.write(b"DOT1\n")
    ser.flush()
    wait_ack("HOME_OK")


def send_newline():
    ser.write(b"NEWLINE\n")
    ser.flush()
    wait_ack("LINE_OK")


# --- 履歴IDから送信 ---
def send_history_by_id(target_id):
    path = 'historyText.json'
    # ✅ ユーザー向けメッセージとデバッグ向けメッセージを格納する変数
    user_message = "不明なエラー"
    debug_detail = ""

    try:
        # 1. ファイル操作エラー        
        if not os.path.exists(path):
            print("履歴ファイルがありません")
            raise FileNotFoundError(f"履歴ファイルが存在しません。\nファイルパス: {path}")
        with open(path, 'r', encoding='utf-8') as f:
            try:
                history = json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(f"履歴ファイルの形式が不正です。\nJSONデコードエラー: {e}")

        # 2. ID検索エラー
        target_item = next((item for item in history if item["id"] == target_id), None)
        if target_item is None:
            raise ValueError(f"指定されたID '{target_id}' のデータが見つかりません。")

        # 3. シリアル通信エラー（send_braille_data内で発生）
        if ser is None:
            raise RuntimeError("Arduinoとのシリアル接続が確立されていません。")
            
        send_braille_data(target_item["brailleData"])

        # 成功時の処理
        status_dict[target_id] = {
            "status": "done",
            "message": "打刻完了",
            "debug_detail": "処理は正常に完了しました。" # ✅ デバッグ情報も追加
        }
        return
    except FileNotFoundError as e:
        user_message = "履歴ファイルが見つかりません。"
        debug_detail = str(e)
    except ValueError as e:
        user_message = "データ形式またはID検索に問題が発生しました。"
        debug_detail = str(e)
    except RuntimeError as e: # シリアル接続エラー、通信エラーなど
        user_message = "打刻機との通信中にエラーが発生しました。\n機器を確認してください。"
        debug_detail = str(e)
    except Exception as e:
        user_message = "打刻処理中に予期せぬ重大なエラーが発生しました。"
        debug_detail = str(e)

        # 失敗時の処理
    status_dict[target_id] = {
        "status": "error",
        "message": user_message, # ✅ ユーザーフレンドリーなエラー内容
        "debug_detail": debug_detail # ✅ デバッグ用の詳細情報
    }
    # 失敗時はコンソールにも詳細を出力
    print(f"❌ ID {target_id} の打刻処理エラー:\n  ユーザーメッセージ: {user_message}\n  詳細: {debug_detail}")


    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for item in data:
        if item["id"] == target_id:
            send_braille_data(item["brailleData"])
            return

    print("指定IDが見つかりません")