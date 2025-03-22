import os
import base64
import requests
import subprocess
import time
from pathlib import Path
from PIL import Image
import io
import logging
import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext
from threading import Thread
import re

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ImageAnalyzer:
    def __init__(self, model="gemma3:27b", use_japanese=False, detail_level="standard", custom_prompt=None, clean_custom_response=True):
        self.model = model
        self.use_japanese = use_japanese
        self.detail_level = detail_level
        self.custom_prompt = custom_prompt
        self.clean_custom_response = clean_custom_response
        self.api_url = "http://localhost:11434/api/generate"
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}

    def start_ollama(self):
        """Ollamaを起動する"""
        try:
            # Ollamaの状態をチェック
            try:
                response = requests.get("http://localhost:11434/api/tags")
                if response.status_code == 200:
                    logger.info("Ollamaは既に起動しています")
                    return True
            except requests.exceptions.ConnectionError:
                pass

            logger.info("Ollamaを起動しています...")
            # PowerShellでバックグラウンド実行
            subprocess.Popen(['powershell', 'Start-Process', 'ollama', 'serve'], 
                           creationflags=subprocess.CREATE_NO_WINDOW)

            # Ollamaが起動するまで待機
            max_attempts = 30
            for _ in range(max_attempts):
                try:
                    response = requests.get("http://localhost:11434/api/tags")
                    if response.status_code == 200:
                        logger.info("Ollama起動完了")
                        return True
                except requests.exceptions.ConnectionError:
                    time.sleep(1)
                    continue

            logger.error("Ollamaの起動がタイムアウトしました")
            return False
        except Exception as e:
            logger.error(f"Ollamaの起動中にエラーが発生しました: {str(e)}")
            return False

    def encode_image(self, image_path):
        """画像をBase64エンコードする"""
        try:
            with Image.open(image_path) as img:
                img_buffer = io.BytesIO()
                img.save(img_buffer, format=img.format)
                img_str = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
                return img_str
        except Exception as e:
            logger.error(f"画像のエンコード中にエラーが発生しました: {str(e)}")
            raise

    def get_prompt(self):
        """プロンプトを生成"""
        if self.custom_prompt:
            prompt = self.custom_prompt.strip()
            if self.clean_custom_response:
                # 使用言語に応じて追加指示文を付与
                if self.use_japanese:
                    prompt += " 主要な要素や行動に焦点を当て、余計な前置きは不要です。"
                else:
                    prompt += " Focus on key elements and actions, and omit unnecessary introductory phrases."
            return prompt

        if self.use_japanese:
            if self.detail_level == "brief":
                return "この画像を1文で簡潔に説明してください。余計な前置きは不要です。"
            elif self.detail_level == "standard":
                return "この画像を2〜3文で説明してください。主要な要素や行動に焦点を当て、余計な前置きは不要です。"
            else:  # detailed
                return "この画像を4〜5文で詳しく説明してください。視覚的な要素、行動、雰囲気などを含めて説明し、余計な前置きは不要です。"
        else:
            if self.detail_level == "brief":
                return "Describe this image in a single concise sentence, without any introductory phrases."
            elif self.detail_level == "standard":
                return "Describe this image in 2-3 sentences, focusing on key elements and actions. No introductory phrases."
            else:  # detailed
                return "Describe this image in 4-5 sentences, including visual elements, actions, and atmosphere. No introductory phrases."
    
    
    def clean_response(self, response):
        """レスポンスから不要なテキストを削除し、画像の説明のみを残す"""
        # 1. 初期クリーニング：不要な前置き表現の削除
        patterns = [
            r"^Here’s a description of the image in 2, ",
            r"^説明[:：]\s*",
            r"^Here's .*?:",
            r"^This image shows",
            r"^The image shows",
            r"^In this image,",
            r"^The image depicts",
            r"^This image depicts",
            r"^The photo shows",
            r"^The picture shows",
            r"^I will describe",
            r"^I'll describe",
            r"^Let me describe",
            r"^I can see",
            r"^画像には",
            r"^この画像には",
            r"^この画像は",
            r"^写真には",
            r"^画像は",
            r"^この画像を.*?で説明します。?\n?",
            r"^以下.*?で説明します。?\n?",
            r"^、"
        ]
        
        text = response.strip()
        for pattern in patterns:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE).strip()
    
        # 2. 追加のクリーニング：一般的な接続表現や余計な表現の削除
        additional_patterns = [
            r"^また、?",
            r"^そして、?",
            r"^なお、?",
            r"^さらに、?",
            r"^加えて、?",
            r"^特に、?",
            r"^具体的には、?",
            r"^Additionally,\s*",
            r"^Moreover,\s*",
            r"^Furthermore,\s*",
            r"^Also,\s*",
            r"^And\s*",
            r"^Specifically,\s*",
            r"^There\s+(?:is|are)\s+",
            r"^We\s+can\s+see\s+",
            r"^You\s+can\s+see\s+",
            r"^It\s+appears\s+",
            r"これは",
            r"それは",
            r"以下は",
            r"次のような",
            r"(?:以下の)?(?:画像に適用できる)?(?:Danbooru|だんぼーる|ダンボール|ダンボーる)?タグ(?:です|となります)。?\n?",
            r"タグ(?:一覧|リスト)：\n?",
            r"^[*＊・]",  # 行頭の箇条書き記号
            r"^、",      # 行頭の読点
            r"主な(?:特徴|要素)(?:：|は)(?:以下の)?(?:通り|とおり)(?:です)?。?\n?",
        ]
        
        for pattern in additional_patterns:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE).strip()
    
        # 3. テキストを1行に整形：改行や箇条書き記号をカンマに変換
        text = re.sub(r'[・\-•*＊\n] ?', ', ', text)
        parts = [part.strip() for part in text.split(',')]
        parts = [part for part in parts if part and not part.startswith('、')]
        text = ', '.join(parts)
    
        # 4. カテゴリラベルの削除：例 "General:" や "Style/Art:" など
        segments = [seg.strip() for seg in text.split(',')]
        cleaned_segments = []
        for seg in segments:
            # セグメントが英数字、"/", "-"、スペースのみで構成され、末尾がコロンの場合はラベルと判断
            if re.match(r'^[A-Za-z0-9/\- ]+:$', seg):
                continue
            cleaned_segments.append(seg)
        text = ', '.join(cleaned_segments)
    
        # 5. メタ情報の削除：タグ生成に関する補足文など不要な文を除去
        segments = [seg.strip() for seg in text.split(',')]
        filtered_segments = []
        for seg in segments:
            lower_seg = seg.lower()
            if lower_seg.startswith("i've prioritized tags") or \
               lower_seg.startswith("possible additional tags") or \
               lower_seg.startswith("optional additional tags") or \
               lower_seg.startswith("additional suggestions") or \
               lower_seg.startswith("generated tags") or \
               lower_seg.startswith("based on danbooru tagging conventions") or \
               lower_seg.startswith("i have included tags that describe") or \
               lower_seg.startswith("i selected tags to best capture") or \
               lower_seg.startswith("i generated these tags using") or \
               lower_seg.startswith("generated by ai") or \
               lower_seg.startswith("metadata"):
                continue
            filtered_segments.append(seg)
        text = ', '.join(filtered_segments)
        
        return text.strip()


    def analyze_image(self, image_path):
        """画像を分析して結果を返す"""
        try:
            # Ollamaが起動していない場合は起動を試みる
            try:
                response = requests.get("http://localhost:11434/api/tags")
            except requests.exceptions.ConnectionError:
                if not self.start_ollama():
                    raise Exception("Ollamaの起動に失敗しました")

            base64_image = self.encode_image(image_path)

            payload = {
                "model": self.model,
                "prompt": self.get_prompt(),
                "stream": False,
                "images": [base64_image]
            }

            response = requests.post(self.api_url, json=payload)
            response.raise_for_status()

            result = response.json()
            response_text = result.get('response', 'No analysis available')

            # チェックボックス clean_custom_response の値に応じて
            if not self.clean_custom_response:
                # チェックが外れている場合はそのまま返す
                return response_text
            else:
                # チェックが入っている場合は必ずクリーン処理を実施
                return self.clean_response(response_text)

        except requests.exceptions.RequestException as e:
            logger.error(f"API通信中にエラーが発生しました: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"画像分析中にエラーが発生しました: {str(e)}")
            raise


    def process_directory(self, directory_path, progress_callback=None, stop_check=None):
        """指定されたディレクトリ内の全画像を処理する"""
        directory = Path(directory_path)
        if not directory.exists():
            raise ValueError(f"指定されたディレクトリが存在しません: {directory_path}")

        # 処理対象の画像ファイル数をカウント
        image_files = [f for f in directory.iterdir() if f.suffix.lower() in self.supported_formats]
        total_files = len(image_files)
        
        if total_files == 0:
            raise ValueError("指定されたディレクトリに画像ファイルが見つかりません。")
        
        processed_count = 0
        error_count = 0

        for image_path in image_files:
            if stop_check and stop_check():
                logger.info("処理が停止されました")
                break
                
            try:
                logger.info(f"処理中: {image_path.name}")
                
                # 画像を分析
                analysis_result = self.analyze_image(image_path)
                
                # 結果をテキストファイルに保存
                text_path = image_path.with_suffix('.txt')
                with open(text_path, 'w', encoding='utf-8') as f:
                    f.write(analysis_result)
                
                logger.info(f"分析完了: {text_path}")
                processed_count += 1

                # プログレスバーの更新
                if progress_callback:
                    progress = (processed_count + error_count) / total_files * 100
                    progress_callback(progress)

            except Exception as e:
                logger.error(f"ファイル {image_path.name} の処理中にエラーが発生しました: {str(e)}")
                error_count += 1

        return processed_count, error_count

class ImageAnalyzerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("画像分析ツール")
        self.root.geometry("800x700")  # 高さを増やして新しい要素を収容
        self.stop_analysis = False
        
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # モデル選択
        model_frame = ttk.LabelFrame(main_frame, text="モデル設定", padding=10)
        model_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(model_frame, text="Ollamaモデル:").pack(side="left")
        self.model_var = tk.StringVar(value="gemma3:27b")
        self.model_entry = ttk.Entry(model_frame, textvariable=self.model_var, width=30)
        self.model_entry.pack(side="left", padx=5)

        # 言語選択
        self.use_japanese_var = tk.BooleanVar(value=False)
        self.japanese_checkbox = ttk.Checkbutton(
            model_frame,
            text="日本語で出力",
            variable=self.use_japanese_var
        )
        self.japanese_checkbox.pack(side="left", padx=(20, 0))

        # カスタムプロンプト
        prompt_frame = ttk.LabelFrame(main_frame, text="カスタムプロンプト（空白時はデフォルトプロンプトを使用）", padding=10)
        prompt_frame.pack(fill="x", pady=(0, 10))
        
        self.custom_prompt = scrolledtext.ScrolledText(
            prompt_frame,
            wrap=tk.WORD,
            height=3,
            width=70
        )
        self.custom_prompt.pack(fill="x", padx=5)

        # カスタムプロンプトのオプション設定
        prompt_options_frame = ttk.Frame(prompt_frame)
        prompt_options_frame.pack(fill="x", padx=5, pady=(5, 0))
        
        self.clean_custom_response_var = tk.BooleanVar(value=True)
        self.clean_custom_checkbox = ttk.Checkbutton(
            prompt_options_frame,
            text="前置きや余計な表現を削除",
            variable=self.clean_custom_response_var
        )
        self.clean_custom_checkbox.pack(side="left")

        # 説明の詳細度
        detail_frame = ttk.LabelFrame(main_frame, text="説明の詳細度（カスタムプロンプト使用時は無効）", padding=10)
        detail_frame.pack(fill="x", pady=(0, 10))
        
        self.detail_level_var = tk.StringVar(value="standard")
        
        detail_options = [
            ("簡潔（1文）", "brief"),
            ("標準（2-3文）", "standard"),
            ("詳細（4-5文）", "detailed")
        ]
        
        for text, value in detail_options:
            ttk.Radiobutton(
                detail_frame,
                text=text,
                value=value,
                variable=self.detail_level_var
            ).pack(side="left", padx=10)

        # フォルダ選択
        folder_frame = ttk.LabelFrame(main_frame, text="フォルダ選択", padding=10)
        folder_frame.pack(fill="x", pady=(0, 10))
        
        self.folder_var = tk.StringVar()
        self.folder_entry = ttk.Entry(folder_frame, textvariable=self.folder_var, width=70)
        self.folder_entry.pack(side="left", padx=5)
        
        browse_button = ttk.Button(folder_frame, text="参照", command=self.browse_folder, style='Accent.TButton')
        browse_button.pack(side="left", padx=5)

        # プログレス情報
        progress_frame = ttk.LabelFrame(main_frame, text="進捗状況", padding=10)
        progress_frame.pack(fill="x", pady=(0, 10))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame, 
            variable=self.progress_var, 
            maximum=100,
            mode='determinate',
            length=300
        )
        self.progress_bar.pack(fill="x", padx=5)

        # ログ表示エリア
        log_frame = ttk.LabelFrame(main_frame, text="ログ", padding=10)
        log_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # スクロールバー付きログ表示
        log_scroll = ttk.Scrollbar(log_frame)
        log_scroll.pack(side="right", fill="y")
        
        self.log_text = tk.Text(log_frame, height=12, yscrollcommand=log_scroll.set)
        self.log_text.pack(fill="both", expand=True)
        log_scroll.config(command=self.log_text.yview)
        
        # ボタンフレーム（中央寄せ）
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(0, 5))
        
        # ボタンを配置するための内部フレーム（中央寄せ用）
        button_center_frame = ttk.Frame(button_frame)
        button_center_frame.pack(anchor="center")
        
        # 実行ボタン（目立つスタイル）
        self.run_button = tk.Button(
            button_center_frame,
            text="画像分析実行",
            command=self.run_analysis,
            bg="#4CAF50",  # 緑色
            fg="white",
            font=('Helvetica', 12, 'bold'),
            width=20,
            height=2
        )
        self.run_button.pack(side="left", padx=5, pady=10)

        # 停止ボタン
        self.stop_button = tk.Button(
            button_center_frame,
            text="分析を停止",
            command=self.stop_analysis_handler,
            bg="#f44336",  # 赤色
            fg="white",
            font=('Helvetica', 12, 'bold'),
            width=20,
            height=2,
            state="disabled"  # 初期状態は無効
        )
        self.stop_button.pack(side="left", padx=5, pady=10)

        # 初期メッセージ
        self.append_log("画像分析ツールを起動しました。")
        self.append_log("※ Ollamaが起動していない場合は自動的に起動を試みます")
        self.append_log("1. Ollamaモデルを確認してください")
        self.append_log("2. 必要に応じて日本語出力を選択してください")
        self.append_log("3. 必要に応じてカスタムプロンプトを入力してください")
        self.append_log("4. カスタムプロンプトが空の場合、説明の詳細度を選択してください")
        self.append_log("5. 画像フォルダを選択してください")
        self.append_log("6. [画像分析実行]ボタンをクリックして処理を開始してください")
        self.append_log("\nサポートされている画像形式: jpg, jpeg, png, gif, bmp, webp")

    def browse_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.folder_var.set(folder_path)
            self.append_log(f"フォルダが選択されました: {folder_path}")

    def update_progress(self, value):
        self.progress_var.set(value)
        self.root.update_idletasks()

    def append_log(self, message):
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def stop_analysis_handler(self):
        """分析処理を停止する"""
        self.stop_analysis = True
        self.stop_button.config(state="disabled")
        self.append_log("分析停止を要求しました。現在の処理が完了するまでお待ちください...")

    def run_analysis(self):
        """画像分析処理を実行する"""
        folder_path = self.folder_var.get()
        if not folder_path:
            self.append_log("エラー: フォルダを選択してください。")
            return

        self.stop_analysis = False
        self.run_button.config(state="disabled")  # 実行中はボタンを無効化
        self.stop_button.config(state="normal")  # 停止ボタンを有効化
        self.progress_var.set(0)  # プログレスバーをリセット

        # ログをGUIに表示するためのハンドラーを設定
        class TextHandler(logging.Handler):
            def __init__(self, gui):
                super().__init__()
                self.gui = gui

            def emit(self, record):
                msg = self.format(record)
                self.gui.append_log(msg)

        logger.addHandler(TextHandler(self))

        # 画像分析処理を別スレッドで実行
        def analysis_thread():
            try:
                # ImageAnalyzerインスタンスを作成
                custom_prompt = self.custom_prompt.get("1.0", tk.END).strip()
                analyzer = ImageAnalyzer(
                    model=self.model_var.get(),
                    use_japanese=self.use_japanese_var.get(),
                    detail_level=self.detail_level_var.get(),
                    custom_prompt=custom_prompt if custom_prompt else None,
                    clean_custom_response=self.clean_custom_response_var.get()
                )
                # ディレクトリ内の画像を処理
                processed, errors = analyzer.process_directory(
                    folder_path,
                    progress_callback=self.update_progress,  # プログレスバーを更新するコールバック関数
                    stop_check=lambda: self.stop_analysis  # 停止ボタンが押されたかチェックする関数
                )
                if self.stop_analysis:
                    self.append_log("\n処理が停止されました:")
                else:
                    self.append_log("\n処理完了:")
                self.append_log(f"処理された画像数: {processed}")
                self.append_log(f"エラー数: {errors}")
            except Exception as e:
                self.append_log(f"エラーが発生しました: {str(e)}")
            finally:
                self.run_button.config(state="normal")  # 実行ボタンを再度有効化
                self.stop_button.config(state="disabled")  # 停止ボタンを無効化
                self.stop_analysis = False  # 停止フラグをリセット

        Thread(target=analysis_thread, daemon=True).start()

    def run(self):
        self.root.mainloop()

def main():
    gui = ImageAnalyzerGUI()
    gui.run()

if __name__ == "__main__":
    main()
