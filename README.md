# Tag Ollama - 画像解析ツール

Tag Ollamaは、Ollamaを使用して画像を解析し、その内容を自然言語で説明するPythonアプリケーションです。
フォルダ内の画像を一括で処理し、各画像の説明を生成することができます。

## 機能

- GUIインターフェースによる簡単な操作
- 複数の画像フォーマットをサポート（jpg, jpeg, png, gif, bmp, webp）
- 日本語・英語での出力に対応
- カスタマイズ可能な説明の詳細度（簡潔、標準、詳細）
- カスタムプロンプトのサポート
- バッチ処理による複数画像の一括解析
- リアルタイムの進捗表示
- 詳細なログ出力

## 必要条件

- Python 3.10以上
- Ollama（gemma:27bなどのマルチモーダルモデルがインストールされていること）

## セットアップ

1. リポジトリのクローン:
```bash
git clone https://github.com/AiWithYou/tagollama.git
cd tagollama
```

2. 仮想環境の作成と有効化:
```bash
python -m venv venv
# Windowsの場合
venv\Scripts\activate
# macOS/Linuxの場合
source venv/bin/activate
```

3. 依存パッケージのインストール:
```bash
pip install -r requirements.txt
```

4. Ollamaのインストールと設定:
- [Ollama公式サイト](https://ollama.ai/)からOllamaをインストール
- 必要なモデルをダウンロード:
```bash
ollama pull gemma:27b
```

## 使用方法

1. アプリケーションの起動:
```bash
python main.py
```

2. GUIで以下の設定を行う:
   - Ollamaモデルの選択（デフォルト: gemma3:27b）
   - 出力言語の選択（日本語/英語）
   - 説明の詳細度の選択（簡潔/標準/詳細）
   - 必要に応じてカスタムプロンプトを入力
   - 処理する画像が含まれるフォルダを選択

3. 「画像分析実行」ボタンをクリックして処理を開始

4. 処理結果は各画像と同じフォルダに、同名のテキストファイル（.txt）として保存されます

## カスタムプロンプト

カスタムプロンプトを使用することで、画像解析の出力をカスタマイズできます。
プロンプトが空の場合、選択された詳細度に応じたデフォルトのプロンプトが使用されます。

## サポートされている画像フォーマット

- JPEG (.jpg, .jpeg)
- PNG (.png)
- GIF (.gif)
- BMP (.bmp)
- WebP (.webp)

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。