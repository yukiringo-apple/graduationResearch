// /static/index.js
async function sendText() {
  const input = document.getElementById("inputText").value;

  // 入力チェック：空白や未入力の場合
  if (!input.trim()) {
    document.getElementById("result").innerText = "文字を入力してください。";
    return;
  }

  // ひらがなのみかチェック
  if (!checkHiragana(input)) {
    document.getElementById("result").innerText = "ひらがなのみ入力してください。";
    return;
  }

  // データ作成
  const data = {
    text: input,
    time: new Date().toLocaleString()
  };

  // Flaskサーバーに送信
  const res = await fetch("/send", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(data)
  });

  const result = await res.json();
  document.getElementById("result").innerText = result.message;
}

function checkInput(input) {
  // ① 使用可能な文字だけかチェック（一次フィルタ）
  const allowRegex = /^[0-9a-zA-Zａ-ｚＡ-Ｚぁ-ゖ！？!?,.、。ーっ]+$/;

  if (!allowRegex.test(input)) return false;

  // ② 小文字（ぁぃぅぇぉ）の禁止
  const smallVowelRegex = /[ぁぃぅぇぉ]/;
  if (smallVowelRegex.test(input)) return false;

  // ③ 拗音の不正組み合わせを禁止
  // 許可：きぎしじちぢにひびみり + ゃゅょ のみ
  const invalidYouonRegex = /(?<![きぎしじちぢにひびぴみり])[ゃゅょ]/;
  if (invalidYouonRegex.test(input)) return false;

  return true;
}



// ▼ 入力欄に追加
function addKana(kana) {
  const input = document.getElementById("inputText");
  input.value += kana;
}

// ▼ タブ切り替え
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

// ▼ テキストからボタンを動的生成
document.querySelectorAll('.kana-grid').forEach(grid => {
  // htmlから.kana-gridの一覧をそのまま取得する
  const text = grid.textContent.trim();
  console.log("text\n", text);

  // 行ごとに分割
  const lines = text.split(/\n+/);
  console.log("lines", lines);

  // htmlファイルの元のテキストを削除
  grid.textContent = "";

  lines.forEach(line => {
    const row = document.createElement("div");
    row.className = "kana-row";

    const chars = line.split(/\s+/);
    console.log("chars", chars);

    chars.forEach(ch => {
      if (ch != "") {
        const btn = document.createElement("button");
        btn.textContent = ch;
        btn.onclick = () => addKana(ch);
        row.append(btn);
      }
    })

    grid.appendChild(row);
  })
});

document.querySelectorAll('.alpha-grid').forEach(grid => {
  const text = grid.textContent.trim();

  const lines = text.split(/\n+/);
  console.log("alpha-items\n", lines);

  grid.textContent = ""; // 一旦消す

  lines.forEach(line => {
    const row = document.createElement("div");
    row.className = "alpha-row";

    const chars = line.split(/\s+/);
    console.log("chars", chars);

    chars.forEach(ch => {
      if (ch != "") {
        const btn = document.createElement("button");
        btn.textContent = ch;
        btn.onclick = () => addKana(ch);
        row.append(btn);
      }
    })

    grid.appendChild(row);
  })
});


// ▼ 1文字削除（拗音は2文字まとめて削除）
function deleteOne() {
  const input = document.getElementById("inputText");
  let text = input.value;

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
    input.value = text.slice(0, -2); // 2文字まとめて削除
  } else {
    input.value = text.slice(0, -1); // 通常は1文字削除
  }
}

// ▼ 全消し
function clearAll() {
  const input = document.getElementById("inputText");
  input.value = "";
}

document.getElementById("inputText").addEventListener("input", function () {
  const str = this.value;
  console.log("🦐入力された値：", str);

  const strArray = str.split("");
  console.log("👀配列：", strArray);

  if (!checkInput(str)) {
    document.getElementById("result").innerText = "使用できない文字が含まれています。";
    return;
  } else {
    document.getElementById("result").innerText = "";
    return;
  }
})