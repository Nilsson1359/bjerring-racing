#!/usr/bin/env python3
"""Laver den engelske udgave af Facebook top 5-grafikken (assets/fb-top5.jpg -> assets/fb-top5-en.jpg).
Danske tekster dækkes med en flade, der interpoleres fra kanterne (bevarer baggrundens forløb), og engelsk tekst tegnes ovenpå."""
from PIL import Image, ImageDraw, ImageFont
import numpy as np

SRC, OUT = 'assets/fb-top5.jpg', 'assets/fb-top5-en.jpg'
FONT = '/System/Library/Fonts/Supplemental/DIN Condensed Bold.ttf'
im = Image.open(SRC).convert('RGB')
a = np.asarray(im).astype(float)

def patch(x0, y0, x1, y1):
    """Udfyld rektanglet ved at interpolere vandret mellem kantpixels (række for række)."""
    L = a[y0:y1, x0 - 3:x0 - 1].mean(axis=1)
    R = a[y0:y1, x1 + 1:x1 + 3].mean(axis=1)
    t = np.linspace(0, 1, x1 - x0)[None, :, None]
    a[y0:y1, x0:x1] = L[:, None, :] * (1 - t) + R[:, None, :] * t

def fit(text, maxw, size):
    while size > 8:
        f = ImageFont.truetype(FONT, size)
        if f.getbbox(text)[2] - f.getbbox(text)[0] <= maxw:
            return f
        size -= 1
    return ImageFont.truetype(FONT, size)

patch(258, 8, 1472, 100)       # titel
patch(675, 120, 925, 158)       # I DANMARK
boxes = [(132, '248,000'), (449, '140,000'), (766, '86,000'), (1083, '35,000'), (1400, '18,000')]
for x, _ in boxes:
    patch(x - 6, 906, x + 172, 986)

img = Image.fromarray(a.clip(0, 255).astype('uint8'))
d = ImageDraw.Draw(img)

def center(text, cx, top, font, fill='#ffffff', spacing=0):
    if spacing:
        w = sum(font.getlength(c) for c in text) + spacing * (len(text) - 1)
        x = cx - w / 2
        for c in text:
            d.text((x, top), c, font=font, fill=fill)
            x += font.getlength(c) + spacing
        return
    bb = font.getbbox(text)
    d.text((cx - (bb[2] - bb[0]) / 2 - bb[0], top - bb[1]), text, font=font, fill=fill)

center('RACING DRIVERS WITH THE MOST FACEBOOK FOLLOWERS', 864, 30, fit('RACING DRIVERS WITH THE MOST FACEBOOK FOLLOWERS', 1190, 84))
center('IN DENMARK', 800, 124, ImageFont.truetype(FONT, 38), fill='#e9ecf2', spacing=6)
for x, n in boxes:
    cx = x + 82
    center('c. ' + n, cx, 914, fit('c. ' + n, 168, 42))
    center('followers', cx, 952, ImageFont.truetype(FONT, 30), fill='#dfe3ea')

img.save(OUT, quality=90)
print('ok', OUT)
