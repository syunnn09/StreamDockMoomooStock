import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from logger import Logger

def create_price_image(price, change, width=72, height=72):
    img = Image.new("RGB", (width, height), color=(15, 15, 15))
    draw = ImageDraw.Draw(img)

    if change > 0:
        text_color = (255, 65, 65) # 赤
    elif change < 0:
        text_color = (46, 204, 113) # 緑
    else:
        text_color = (220, 220, 220) # 白

    price_text = f"{price:,}"[:8]

    try:
        font = ImageFont.truetype("arialbd.ttf", 18)
    except OSError:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), price_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = (width - text_width) / 2
    y = (height - text_height) / 2 - bbox[1]

    draw.text((x, y), price_text, fill=text_color, font=font)

    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return f"data:image/png;base64,{base64.b64encode(buffered.getvalue()).decode('utf-8')}"
