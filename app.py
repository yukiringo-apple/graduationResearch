# app.py

from flask import Flask, request, jsonify, render_template
import json
import threading
import os

app = Flask(__name__)

# 点字変換ライブラリ
def convert_to_braille(text: str):
    with open("brailleConverter.json", "r", encoding="utf-8") as f:
        braille_map = json.load(f)
    result = []
    for ch in text:
        pattern = braille_map.get(ch, [0,0,0,0,0,0])
        result.append({"char": ch, "pattern": pattern})
    return result

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send', methods=['POST'])
def send_text():
    import plotter  # import はここで一度だけ

    data = request.get_json()
    text = data.get("text")
    braille_data = convert_to_braille(text)

    # 保存先
    file_path = 'historyText.json'
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                json_data = json.load(f)
            except json.JSONDecodeError:
                json_data = []
    else:
        json_data = []

    # IDを自動付与
    next_id = len(json_data) + 1
    json_data.append({
        "id": next_id,
        "text": text,
        "brailleData": braille_data,
        "lineNumber": "",
        "time": data.get("time")
    })

    # ファイル保存
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

    # Arduino送信をスレッドで実行
    threading.Thread(
        target=plotter.send_history_by_id,
        args=(next_id,),
        daemon=True
    ).start()

    return jsonify({"message": f"'{text}' を保存しました！", "id": next_id})

# デバッグ二重起動対策
if __name__ == "__main__":
    import plotter
    # WERKZEUG_RUN_MAIN = True のときだけ Arduino 初期化
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        plotter.initialize()
    app.run(debug=True)


