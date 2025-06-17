#!/bin/bash

# 切換到腳本所在目錄
cd "$(dirname "$0")"

# 檢查 Python 環境
if ! command -v python3 &> /dev/null; then
    echo "錯誤：找不到 Python3，請先安裝 Python3"
    read -p "按任意鍵繼續..."
    exit 1
fi

# 檢查必要套件
if ! python3 -c "import PIL" &> /dev/null || ! python3 -c "import pytesseract" &> /dev/null || ! python3 -c "import pillow_heif" &> /dev/null; then
    echo "正在安裝必要套件..."
    pip3 install -r requirements.txt
fi

# 檢查 Tesseract
if ! command -v tesseract &> /dev/null; then
    echo "錯誤：找不到 Tesseract，請先安裝 Tesseract"
    echo "可以使用以下指令安裝："
    echo "brew install tesseract"
    read -p "按任意鍵繼續..."
    exit 1
fi

# 執行程式
python3 ocr_gui.py 