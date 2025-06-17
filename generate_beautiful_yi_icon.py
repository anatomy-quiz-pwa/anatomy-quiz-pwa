from PIL import Image, ImageDraw, ImageFont
import os

size = 512
radius = 80
bg_color = '#333333'
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

font_size = 320
font = ImageFont.truetype(font_path, font_size)

# 建立帶圓角的底圖
img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)
# 畫圓角矩形
rect = [0, 0, size, size]
draw.rounded_rectangle(rect, radius, fill=bg_color)

# 計算文字大小與位置
w, h = draw.textsize(text, font=font)
text_x = (size - w) / 2
text_y = (size - h) / 2 - 10

draw.text((text_x, text_y), text, fill=text_color, font=font)

# 輸出到桌面
desktop = os.path.expanduser('~/Desktop')
output_path = os.path.join(desktop, 'yi_beautiful_icon.png')
img.save(output_path)
print(f'已產生 {output_path}') 