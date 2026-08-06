"""
创建应用图标
"""

from PIL import Image, ImageDraw, ImageFont
import os


def create_icon():
    """创建应用图标"""
    # 创建一个256x256的图像
    size = 256
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 绘制背景（渐变蓝色）
    for y in range(size):
        r = int(50 + (y / size) * 50)
        g = int(100 + (y / size) * 50)
        b = int(200 + (y / size) * 55)
        draw.line([(0, y), (size, y)], fill=(r, g, b, 255))

    # 绘制树形结构
    # 主干线
    draw.line([(64, 40), (64, 200)], fill=(255, 255, 255), width=4)

    # 分支线
    draw.line([(64, 80), (180, 80)], fill=(255, 255, 255), width=3)
    draw.line([(64, 140), (180, 140)], fill=(255, 255, 255), width=3)

    # 节点圆圈
    # 根节点
    draw.ellipse([(44, 20), (84, 60)], fill=(100, 200, 100), outline=(255, 255, 255), width=2)

    # 子节点
    draw.ellipse([(160, 60), (200, 100)], fill=(100, 200, 100), outline=(255, 255, 255), width=2)
    draw.ellipse([(160, 120), (200, 160)], fill=(255, 200, 100), outline=(255, 255, 255), width=2)

    # 底部节点
    draw.ellipse([(44, 180), (84, 220)], fill=(255, 200, 100), outline=(255, 255, 255), width=2)

    # 绘制文字（简化版）
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        font = ImageFont.load_default()

    draw.text((90, 30), "CREO", fill=(255, 255, 255), font=font)
    draw.text((90, 190), "编号器", fill=(255, 255, 255), font=font)

    # 保存为ICO文件
    icon_path = os.path.join(os.path.dirname(__file__), "app_icon.ico")
    img.save(icon_path, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
    print(f"Icon created: {icon_path}")

    # 同时保存为PNG用于预览
    png_path = os.path.join(os.path.dirname(__file__), "app_icon.png")
    img.save(png_path)
    print(f"PNG preview: {png_path}")

    return icon_path


if __name__ == "__main__":
    create_icon()
