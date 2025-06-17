import os
import shutil
from datetime import datetime
from PIL import Image
import pytesseract
import uuid
import tkinter as tk
from tkinter import messagebox
import pillow_heif
import re

# 註冊 HEIF 支援
pillow_heif.register_heif_opener()

class OCRApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OCR 轉換工具")
        
        # 設定視窗大小和位置
        window_width = 300
        window_height = 150
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 建立按鈕
        self.convert_button = tk.Button(
            root,
            text="開始轉換",
            command=self.start_conversion,
            height=2,
            width=20,
            font=("Arial", 12)
        )
        self.convert_button.pack(pady=20)
        
        # 建立狀態標籤
        self.status_label = tk.Label(
            root,
            text="準備就緒",
            font=("Arial", 10)
        )
        self.status_label.pack(pady=10)

    def start_conversion(self):
        try:
            # 資料夾路徑
            desktop = os.path.expanduser("~/Desktop")
            input_dir = os.path.join(desktop, "book", "input")
            output_dir = os.path.join(desktop, "book", "output")
            processed_base_dir = os.path.join(desktop, "book", "processed")

            # 建立必要資料夾
            os.makedirs(input_dir, exist_ok=True)
            os.makedirs(output_dir, exist_ok=True)
            os.makedirs(processed_base_dir, exist_ok=True)

            # 檢查輸入資料夾是否有檔案
            files = [f for f in os.listdir(input_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.heic', '.tif', '.bmp'))]
            if not files:
                messagebox.showinfo("提示", "輸入資料夾中沒有圖片檔案！")
                return

            self.status_label.config(text="正在處理中...")
            self.convert_button.config(state="disabled")
            self.root.update()

            processed_count = 0
            for filename in files:
                filepath = os.path.join(input_dir, filename)
                temp_jpg_path = None

                try:
                    # 轉為 RGB 並存成暫存 JPG
                    with Image.open(filepath) as img:
                        rgb_img = img.convert("RGB")
                        temp_jpg_path = os.path.join(input_dir, f"temp_{uuid.uuid4().hex}.jpg")
                        rgb_img.save(temp_jpg_path, "JPEG")

                    # OCR 辨識
                    with Image.open(temp_jpg_path) as temp_img:
                        text = pytesseract.image_to_string(temp_img, lang='eng')

                    # 偵測頁碼（取前3行，找純數字或常見頁碼格式）
                    page_number = None
                    for line in text.split('\n')[:3]:
                        line_strip = line.strip()
                        # 純數字
                        if re.fullmatch(r'\d{1,4}', line_strip):
                            page_number = line_strip
                            break
                        # Page 12 或 - 12 -
                        m = re.match(r'(?:Page|page)?\s*-?\s*(\d{1,4})\s*-?', line_strip)
                        if m:
                            page_number = m.group(1)
                            break

                    # 尋找所有含 figure/fig./Fig. 的段落
                    figure_lines = []
                    for line in text.split('\n'):
                        if re.search(r'\b(fig(?:ure)?\.?|Fig(?:ure)?\.?|FIG(?:URE)?\.?)(\s|:|\d)', line):
                            figure_lines.append(line.strip())
                    
                    # 組合 ChatGPT 指令
                    gpt_instruction = (
                        "請幫我將以下英文翻譯成繁體中文，保留原文段落、逐段對照，最後幫我摘要整理，必要時可加上表格。\n\n"
                        "------ 以下為英文原文 ------\n\n" + text.strip() +
                        "\n\n------ 請特別針對下列 figure/fig. 圖說段落，整理每一張圖的重點說明，並用 Notion 友善的格式（如 Markdown 標題、分點）呈現 ------\n\n"
                        + ("\n".join(figure_lines) if figure_lines else "（本頁未偵測到圖說段落）")
                    )
                    # 根據頁碼命名
                    base_name = os.path.splitext(filename)[0]
                    if page_number:
                        output_filename = f"{base_name}_{page_number}.txt"
                    else:
                        output_filename = f"{base_name}.txt"
                    output_path = os.path.join(output_dir, output_filename)

                    with open(output_path, "w", encoding="utf-8") as f:
                        f.write(gpt_instruction)

                    # 移動原始圖片
                    today = datetime.today().strftime('%Y-%m-%d')
                    processed_dir = os.path.join(processed_base_dir, today)
                    os.makedirs(processed_dir, exist_ok=True)
                    shutil.move(filepath, os.path.join(processed_dir, filename))

                    processed_count += 1

                except Exception as e:
                    messagebox.showerror("錯誤", f"處理 {filename} 時發生錯誤：{str(e)}")

                finally:
                    if temp_jpg_path and os.path.exists(temp_jpg_path):
                        os.remove(temp_jpg_path)

            if processed_count > 0:
                messagebox.showinfo("完成", f"成功處理 {processed_count} 個檔案！")
                self.status_label.config(text=f"已處理 {processed_count} 個檔案")
            else:
                self.status_label.config(text="處理完成，但沒有成功轉換的檔案")

        except Exception as e:
            messagebox.showerror("錯誤", f"發生錯誤：{str(e)}")
            self.status_label.config(text="處理失敗")

        finally:
            self.convert_button.config(state="normal")

def main():
    root = tk.Tk()
    app = OCRApp(root)
    root.mainloop()

if __name__ == "__main__":
    main() 