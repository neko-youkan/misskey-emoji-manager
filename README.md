# Misskey Emoji Importer

ZIPファイルに入った画像を、Misskeyのカスタム絵文字として一括登録するStreamlitアプリです。

## 主な機能

- PNG / JPG / GIF / WebP / AVIFに対応
- ファイル名から絵文字名を自動生成
- ZIP内フォルダ名をカテゴリとして利用
- 共通カテゴリ・接頭辞・エイリアス・ライセンス設定
- 登録済み絵文字のスキップ
- ZIP内の名前重複チェック
- テスト実行
- 成功・失敗ログとCSV出力
- 新旧Misskey APIの自動切り替え

## 起動手順（Windows / WSL / Ubuntu）

```bash
cd misskey-emoji-importer
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

WindowsのPowerShellで直接動かす場合：

```powershell
cd misskey-emoji-importer
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

ブラウザで通常は `http://localhost:8501` が開きます。

## APIトークン

Misskeyの設定画面からAPIトークンを作成し、管理者として絵文字を登録できる権限を付けてください。
トークンはGitにコミットしたり、スクリーンショットへ写したりしないでください。

## ZIPの例

```text
neco-emojis.zip
├── neko_hello.png
├── neko_sleep.gif
└── reaction/
    ├── neko_yes.png
    └── neko_no.png
```

「フォルダ名をカテゴリにする」が有効で、共通カテゴリが空欄なら、
`reaction` フォルダ内の画像は `reaction` カテゴリになります。

## 注意

Misskey本体やフォークによって、絵文字登録APIの仕様が異なる場合があります。
このアプリは `emojis/create` を先に試し、未対応なら `admin/emoji/add` を試します。
失敗した場合は、画面の「詳細」にAPI応答が表示されます。
