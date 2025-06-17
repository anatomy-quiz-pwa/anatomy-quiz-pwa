from PIL import Image, ImageDraw, ImageFont
import os

# 設定圖檔大小與顏色
size = 512
bg_color = 'black'
text_color = 'white'
text = '譯'

# 嘗試尋找系統中文字型
font_path_candidates = [
    '/System/Library/Fonts/STHeiti Medium.ttc',
    '/System/Library/Fonts/PingFang.ttc',
    '/System/Library/Fonts/Hiragino Sans GB W3.ttc',
    '/Library/Fonts/Arial Unicode.ttf',
]
font_path = None
for path in font_path_candidates:
    if os.path.exists(path):
        font_path = path
        break
if font_path is None:
    raise RuntimeError('找不到中文字型，請手動指定 font_path')

font_size = 340
font = ImageFont.truetype(font_path, font_size)

img = Image.new('RGB', (size, size), color=bg_color)
draw = ImageDraw.Draw(img)

# 計算文字大小與位置
w, h = draw.textsize(text, font=font)
# 微調 Y 位置讓字體居中
text_x = (size - w) / 2
text_y = (size - h) / 2 - 20

draw.text((text_x, text_y), text, fill=text_color, font=font)

# 輸出到桌面
desktop = os.path.expanduser('~/Desktop')
output_path = os.path.join(desktop, 'yi_icon.png')
img.save(output_path)
print(f'已產生 {output_path}') 