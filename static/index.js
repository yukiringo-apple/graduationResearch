// /static/index.js
const printDialog = document.getElementById("printDialog");
const sendBtn = document.getElementById("sendBtn");
const inputText = document.getElementById("inputText");

// 送信ボタンと入力フィールドの有効/無効を切り替える関数
function setInputEnabled(enabled) {
  sendBtn.disabled = !enabled;
  inputText.readOnly = !enabled;
  // 他の入力ボタンも無効化したい場合はここに追加
  document.querySelectorAll('.tab-content button').forEach(btn => {
    btn.disabled = !enabled;
  });
  document.querySelectorAll('.edit-buttons button').forEach(btn => {
    btn.disabled = !enabled;
  });
}

// 打刻状態を定期的に確認するポーリング関数
async function pollStatus(id) {
  const resultElement = document.getElementById("result");
  const dialogMessage = document.getElementById("dialogMessage");
  let statusCheckInterval = setInterval(async () => {
    try {
      const res = await fetch(`/status/${id}`);
      const data = await res.json();

      dialogMessage.innerText = data.message; // ダイアログのメッセージを更新

      if (data.status === "done" || data.status === "error") {
        clearInterval(statusCheckInterval); // ポーリング停止
        printDialog.close(); // ダイアログを閉じる
        setInputEnabled(true); // 入力再開

        // 結果メッセージの表示
        if (data.status === "done") {
          resultElement.innerText = `✅ 打刻完了: ${data.message}`;
          resultElement.style.color = "green";
        } else {
          // ❌ エラー時の表示を分離 ❌
          // ユーザー向けメッセージを表示
          let displayMessage = `❌ エラー: ${data.message}`;

          // デバッグ用の詳細情報があれば追加（開発環境向け）
          if (data.debug_detail) {
            // 例: コンソールに出力 or 開発者向けに詳細なエラーメッセージをHTMLに追加
            console.error(`[ID: ${id}] 打刻詳細エラー: ${data.debug_detail}`);
            // ユーザーインターフェースに詳細を出したい場合は、以下のように追加します
            // displayMessage += `\n (詳細: ${data.debug_detail})`;

            // ユーザーが分かりやすいように「詳細なログはコンソールを参照してください」と案内
            // displayMessage += `\n (詳細は開発者コンソール (F12) を参照してください)`;
          }

          resultElement.innerText = displayMessage;
          resultElement.style.color = "red";
        }
      } else if (data.status === "printing") {
        // ... (既存のコード) ...
      }

    } catch (error) {
      // ... (既存の通信エラー処理) ...
    }
  }, 1000); // 1秒ごとに確認
}


async function sendText() {
  let input = inputText.value;
  const resultElement = document.getElementById("result");

  // 入力チェック：空白や未入力の場合
  if (!input.trim()) {
    resultElement.innerText = "文字を入力してください。";
    resultElement.style.color = "red";
    return;
  }

  // 入力チェック（checkInputの結果を使用）
  if (!checkInput(input)) {
    resultElement.innerText = "使用できない文字が含まれています。";
    resultElement.style.color = "red";
    return;
  }

  // 全角 -> 半角
  input = toHalfWidth(input);

  // 打刻中ダイアログ表示と入力無効化
  resultElement.innerText = "";
  printDialog.showModal();
  setInputEnabled(false);

  // データ作成
  const data = {
    text: input,
    time: new Date().toLocaleString()
  };

  // Flaskサーバーに送信
  try {
    const res = await fetch("/send", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(data)
    });

    if (!res.ok) {
      throw new Error(`サーバーエラー: ${res.status}`);
    }

    const result = await res.json();
    resultElement.innerText = result.message;
    resultElement.style.color = "#374151";

    // 打刻状態のポーリング開始
    pollStatus(result.id);

  } catch (error) {
    // 送信自体が失敗した場合
    printDialog.close();
    setInputEnabled(true);
    resultElement.innerText = `❌ 送信エラー: ${error.message}`;
    resultElement.style.color = "red";
  }
}

/*
以下、checkInput, addKana, タブ切り替え, ボタン動的生成, deleteOne, clearAll, 入力イベントリスナー, toHalfWidth は変更ありませんが、
`inputText`を使用する関数はグローバル変数を使用するように修正します。
*/

// ▼ 入力欄に追加
function addKana(kana) {
  inputText.value += kana;
}

// ▼ 1文字削除（拗音は2文字まとめて削除）
function deleteOne() {
  if (!inputText.readOnly) { // 打刻中は操作不可
    let text = inputText.value;

    if (text.length === 0) return;

    // 拗音の一覧（2文字扱い）
    const youonList = [
      "きゃ", "きゅ", "きょ", "ぎゃ", "ぎゅ", "ぎょ",
      "しゃ", "しゅ", "しょ", "じゃ", "じゅ", "じょ",
      "ちゃ", "ちゅ", "ちょ", "ぢゃ", "ぢゅ", "ぢょ",
      "にゃ", "にゅ", "にょ",
      "ひゃ", "ひゅ", "ひょ", "びゃ", "びゅ", "びょ",
      "ぴゃ", "ぴゅ", "ぴょ",
      "みゃ", "みゅ", "みょ",
      "りゃ", "りゅ", "りょ"
    ];

    // 末尾2文字が拗音か判定
    const last2 = text.slice(-2);
    if (youonList.includes(last2)) {
      inputText.value = text.slice(0, -2); // 2文字まとめて削除
    } else {
      inputText.value = text.slice(0, -1); // 通常は1文字削除
    }
  }
}

// ▼ 全消し
function clearAll() {
  if (!inputText.readOnly) { // 打刻中は操作不可
    inputText.value = "";
  }
}

// 既存のイベントリスナーで `document.getElementById("inputText")` を `inputText` に変更
inputText.addEventListener("input", function () {
  const str = this.value;
  console.log("🦐入力された値：", str);

  if (!checkInput(str)) {
    document.getElementById("result").innerText = "使用できない文字が含まれています。";
    document.getElementById("result").style.color = "red";
    return;
  } else {
    document.getElementById("result").innerText = "";
    document.getElementById("result").style.color = "#374151";
    return;
  }
})

// === checkInput と toHalfWidth は省略 (中身変更なし) ===
function checkInput(input) {
  // ① 使用可能な文字だけかチェック（一次フィルタ）
  const allowRegex = /^[0-9a-zA-Zａ-ｚＡ-Ｚぁ-ゖ！？!?,.、。ーっ]+$/;
  if (!allowRegex.test(input)) return false;

  // ② 小文字（ぁぃぅぇぉ）の禁止
  const smallVowelRegex = /[ぁぃぅぇぉ]/;
  if (smallVowelRegex.test(input)) return false;

  // ③ 拗音の不正組み合わせを禁止
  // 許可：きぎしじちぢにひびぴみり + ゃゅょ のみ
  const invalidYouonRegex = /(?<![きぎしじちぢにひびぴみり])[ゃゅょ]/;
  if (invalidYouonRegex.test(input)) return false;

  return true;
}

// 全角 -> 半角（英数字）
function toHalfWidth(str) {
  str = str.replace(/[Ａ-Ｚａ-ｚ０-９]/g, function (s) {
    return String.fromCharCode(s.charCodeAt(0) - 0xFEE0);
  });
  return str;
}

// === タブ切り替えは省略 (中身変更なし) ===
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    // タブボタンの active を切り替え
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');

    // 対象コンテンツを表示
    const target = btn.dataset.target;
    document.querySelectorAll('.tab-content').forEach(tc => tc.classList.remove('active'));
    document.getElementById(target).classList.add('active');
  });
});

// === テキストからボタンを動的生成 (デザイン統一のため、kana-gridとalpha-gridの処理を統一し、行のクラスを調整) ===

// 統一されたボタン生成ロジック
function createButtonsFromText(gridElement, isAlphaGrid) {
  const text = gridElement.textContent.trim();
  const lines = text.split(/\n+/).filter(line => line.trim() !== ''); // 空行を除去

  gridElement.textContent = ""; // 元のテキストを削除

  lines.forEach(line => {
    // デザイン統一のため、行のクラス名を変更
    const row = document.createElement("div");
    row.className = isAlphaGrid ? "input-button-row alpha-row" : "input-button-row kana-row";

    const chars = line.split(/\s+/).filter(ch => ch !== "");

    chars.forEach(ch => {
      const btn = document.createElement("button");
      btn.textContent = ch;
      btn.onclick = () => addKana(ch);
      row.append(btn);
    });

    gridElement.appendChild(row);
  });
}

document.querySelectorAll('.kana-grid').forEach(grid => {
  createButtonsFromText(grid, false);
});

document.querySelectorAll('.alpha-grid').forEach(grid => {
  createButtonsFromText(grid, true);
});