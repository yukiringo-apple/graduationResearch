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
    except serial.SerialException as e: # ✅ serial.SerialExceptionを補足
        # デバッグ用詳細メッセージ
        print(f"❌ Arduino 接続失敗 (SerialException): COMポート'{COM_PORT}'を確認してください。詳細: {e}")
        ser = None
    except Exception as e:
        # その他の例外
        print(f"❌ Arduino 接続失敗 (その他エラー): 詳細: {e}")
        ser = None


def send_dot(d):
    global ser
    if ser is None:
        raise RuntimeError("シリアル未接続")
    if 1 <= d <= 6:
        ser.write(f"{d}\n".encode())
        time.sleep(DELAY_DOT)


def send_pattern(pattern):
    for i, dot_on in enumerate(pattern, start=1):
        if dot_on == 1:
            send_dot(i)


def send_braille_data(braille_data):
    global ser
    # if ser is None:
        # raise RuntimeError("Arduinoが接続されていません") # 呼び出し元で処理するため削除

    # ✅ シリアル通信のエラー処理を強化
    try:
        for item in braille_data:
            send_pattern(item["pattern"])

        ser.write(b"HOME\n")
        time.sleep(2)
    except serial.SerialTimeoutException as e:
        raise RuntimeError(f"シリアル書き込みタイムアウト。\n機器の応答を確認してください。詳細: {e}")
    except Exception as e:
        raise RuntimeError(f"打刻中の予期せぬエラーが発生しました。\n詳細: {e}")


def send_history_by_id(target_id, status_dict):
    file_path = 'historyText.json'
    # ✅ ユーザー向けメッセージとデバッグ向けメッセージを格納する変数
    user_message = "不明なエラー"
    debug_detail = ""

    try:
        # 1. ファイル操作エラー
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"履歴ファイルが存在しません。\nファイルパス: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
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