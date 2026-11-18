#!/usr/bin/env python3
"""Draw the 17 November 2026 one-day news image (1024x1024 PNG).

Reads tools/stories.json (researched from Reuters / Al Jazeera / AP / AFP /
Just Security coverage of 17 Nov 2026) and renders a newspaper front page
with PIL. Output: entry.png next to main.ts (the program copies it to
/output/entry.png). Pure stdlib + Pillow; no network.
"""
import json
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

W, H = 1024, 1024
PAPER = (250, 246, 238)
INK = (26, 26, 26)
NAVY = (20, 33, 61)
GOLD = (192, 138, 30)
RED = (180, 35, 24)
TEAL = (14, 116, 110)
GREY = (91, 91, 85)
CARD = (255, 255, 255)
BORDER = (221, 213, 194)

SERIF_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


def wrap(draw, text, fnt, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=fnt) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_bridge(d, x0, y0, x1, y1, color):
    """Suspension-bridge silhouette in the box (x0,y0)-(x1,y1)."""
    deck_y = y0 + (y1 - y0) * 0.58
    t1 = x0 + (x1 - x0) * 0.30
    t2 = x0 + (x1 - x0) * 0.70
    top = y0 + 14
    # main cable: end -> tower top -> sagging curve -> tower top -> end
    pts = [(x0 + 4, deck_y), (t1, top)]
    n = 24
    for i in range(n + 1):
        x = t1 + (t2 - t1) * i / n
        sag = (deck_y - 26 - top) * (1 - (2 * i / n - 1) ** 2)
        pts.append((x, top + (deck_y - 26 - top) - sag))
    pts += [(t2, top), (x1 - 4, deck_y)]
    d.line(pts, fill=color, width=4)
    # towers and deck
    for tx in (t1, t2):
        d.line([(tx, top - 6), (tx, deck_y)], fill=color, width=8)
        d.line([(tx - 16, top - 6), (tx + 16, top - 6)], fill=color, width=5)
    d.line([(x0, deck_y), (x1, deck_y)], fill=color, width=7)
    # suspenders from cable down to deck, between the towers
    for i in range(1, 6):
        x = t1 + (t2 - t1) * i / 6
        sag = (deck_y - 26 - top) * (1 - (2 * i / 6 - 1) ** 2)
        cy = top + (deck_y - 26 - top) - sag
        d.line([(x, cy), (x, deck_y)], fill=color, width=2)
    # water
    for wy in (y1 - 24, y1 - 10):
        d.line([(x0 + 12, wy), (x1 - 12, wy)], fill=color, width=3)


def draw_chart(d, x0, y0, x1, y1, color):
    pts = [(x0 + (x1 - x0) * i / 4, y0 + (y1 - y0) * (0.15 + 0.2 * i))
           for i in range(5)]
    d.line(pts, fill=color, width=5)
    ex, ey = pts[-1]
    d.polygon([(ex, ey), (ex - 16, ey - 2), (ex - 4, ey + 12)], fill=color)
    for i, bx in enumerate(range(4)):
        bh = (y1 - y0) * (0.55 - i * 0.1)
        d.rectangle([x0 + 8 + bx * 22, y1 - 8 - bh, x0 + 24 + bx * 22, y1 - 8],
                    fill=color)


def draw_drop(d, x0, y0, x1, y1, color):
    cx = (x0 + x1) // 2
    d.polygon([(cx, y0 + 4), (x1 - 6, y0 + (y1 - y0) * 0.55),
               (cx, y1 - 4), (x0 + 6, y0 + (y1 - y0) * 0.55)], fill=color)
    d.ellipse([x0 + 10, y0 + (y1 - y0) * 0.5, x1 - 10, y1 - 6], fill=color)
    for wy in (y1 - 2, y1 + 12):
        d.line([(x0, wy), (x1, wy)], fill=color, width=3)


def draw_globe(d, x0, y0, x1, y1, color):
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    r = min(x1 - x0, y1 - y0) // 2 - 4
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=5)
    d.ellipse([cx - r // 2, cy - r, cx + r // 2, cy + r], outline=color, width=3)
    d.line([(cx - r, cy), (cx + r, cy)], fill=color, width=3)
    for dx, dy in ((-r - 16, -r - 6), (0, -r - 14), (r + 16, -r - 6)):
        d.ellipse([cx + dx - 6, cy + dy - 6, cx + dx + 6, cy + dy + 6],
                  fill=color)


def draw_leaf(d, x0, y0, x1, y1, color):
    d.pieslice([x0, y0, x1, y1], 180, 360, fill=color)
    d.pieslice([x0 + 8, y0 + 14, x1 - 8, y1 - 6], 180, 360, fill=PAPER)
    d.line([((x0 + x1) // 2, y0 + (y1 - y0) // 2), ((x0 + x1) // 2, y1 - 2)],
           fill=color, width=4)


def draw_camera(d, x0, y0, x1, y1, color):
    d.rounded_rectangle([x0, y0 + 12, x1, y1 - 8], radius=8,
                        outline=color, width=4)
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2 + 4
    d.ellipse([cx - 20, cy - 20, cx + 20, cy + 20], outline=color, width=4)
    d.ellipse([cx - 7, cy - 7, cx + 7, cy + 7], fill=color)
    d.rectangle([x0 + 12, y0, x0 + 44, y0 + 12], fill=color)


def draw_rocket(d, x0, y0, x1, y1, color):
    cx = (x0 + x1) // 2
    d.polygon([(cx, y0 + 2), (cx + 20, y0 + 44), (cx - 20, y0 + 44)],
              fill=color)
    d.rectangle([cx - 20, y0 + 44, cx + 20, y0 + 78], fill=color)
    d.polygon([(cx - 20, y0 + 60), (cx - 36, y0 + 84), (cx - 20, y0 + 78)],
              fill=color)
    d.polygon([(cx + 20, y0 + 60), (cx + 36, y0 + 84), (cx + 20, y0 + 78)],
              fill=color)
    d.polygon([(cx - 9, y0 + 80), (cx + 9, y0 + 80), (cx, y0 + 104)],
              fill=(214, 90, 20))


ICONS = {"bridge": draw_bridge, "chart": draw_chart, "drop": draw_drop,
         "globe": draw_globe, "leaf": draw_leaf, "camera": draw_camera,
         "rocket": draw_rocket}


def main():
    with open(os.path.join(HERE, "stories.json"), encoding="utf-8") as f:
        data = json.load(f)

    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # --- masthead ---
    d.rectangle([0, 0, W, 132], fill=NAVY)
    title_f = font(SERIF_B, 58)
    t = data["masthead"]
    d.text(((W - d.textlength(t, font=title_f)) / 2, 20), t,
           font=title_f, fill=(255, 255, 255))
    date_f = font(SANS_B, 25)
    dt = data["date_label"]
    d.text(((W - d.textlength(dt, font=date_f)) / 2, 88), dt,
           font=date_f, fill=(217, 164, 65))
    d.rectangle([0, 132, W, 137], fill=GOLD)

    # --- lead story ---
    lead = data["lead"]
    lx, lw = 32, 640
    y = 150
    kf = font(SANS_B, 23)
    d.text((lx, y), lead["kicker"], font=kf, fill=RED)
    y += 36
    hf = font(SANS_B, 42)
    for line in wrap(d, lead["headline"], hf, lw):
        d.text((lx, y), line, font=hf, fill=INK)
        y += 51
    y += 8
    bf = font(SANS, 23)
    for line in wrap(d, lead["summary"], bf, lw):
        d.text((lx, y), line, font=bf, fill=(51, 51, 51))
        y += 31
    # lead icon: bridge, right of the text
    d.rectangle([712, 150, 992, 412], fill=(233, 228, 216))
    d.rectangle([712, 150, 992, 412], outline=BORDER, width=2)
    draw_bridge(d, 736, 192, 968, 372, NAVY)
    d.text((736, 376), "KERCH BRIDGE · BLACK SEA", font=font(SANS_B, 16),
           fill=GREY)
    d.line([(32, 432), (992, 432)], fill=BORDER, width=2)

    # --- 2x2 cards (type only; icons stay with lead + strip) ---
    cards = data["cards"]
    colors = [RED, (150, 60, 10), NAVY, TEAL]
    cw, chh, gap = 472, 170, 16
    for i, card in enumerate(cards):
        cx = 32 + (i % 2) * (cw + gap)
        cy = 448 + (i // 2) * (chh + 14)
        d.rectangle([cx, cy, cx + cw, cy + chh], fill=CARD, outline=BORDER,
                    width=2)
        d.rectangle([cx, cy, cx + 7, cy + chh], fill=colors[i])
        tx = cx + 24
        d.text((tx, cy + 12), card["kicker"], font=font(SANS_B, 19),
               fill=colors[i])
        yy = cy + 40
        for line in wrap(d, card["headline"], font(SANS_B, 25), cw - 48):
            d.text((tx, yy), line, font=font(SANS_B, 25), fill=INK)
            yy += 31
        yy += 4
        for line in wrap(d, card["summary"], font(SANS, 19), cw - 48):
            d.text((tx, yy), line, font=font(SANS, 19), fill=(51, 51, 51))
            yy += 25

    # --- bottom strip: culture + space ---
    strip = data["strip"]
    sicons = ["camera", "rocket"]
    scolors = [NAVY, (150, 60, 10)]
    sy = 816
    for i, item in enumerate(strip):
        sx = 32 + i * (cw + gap)
        d.rectangle([sx, sy, sx + cw, sy + 126], fill=CARD, outline=BORDER,
                    width=2)
        d.rectangle([sx, sy, sx + 7, sy + 126], fill=scolors[i])
        tx = sx + 24
        d.text((tx, sy + 10), item["kicker"], font=font(SANS_B, 19),
               fill=scolors[i])
        yy = sy + 38
        for line in wrap(d, item["headline"], font(SANS_B, 25), cw - 116):
            d.text((tx, yy), line, font=font(SANS_B, 25), fill=INK)
            yy += 31
        for line in wrap(d, item["summary"], font(SANS, 19), cw - 116):
            d.text((tx, yy), line, font=font(SANS, 19), fill=(51, 51, 51))
            yy += 25
        ICONS[sicons[i]](d, sx + cw - 96, sy + 20, sx + cw - 24, sy + 106,
                         scolors[i])

    # --- footer ---
    ff = font(SANS, 18)
    ft = data["footer"]
    d.text(((W - d.textlength(ft, font=ff)) / 2, 956), ft, font=ff, fill=GREY)
    d.text(((W - d.textlength("make.fun · daily news image", font=ff)) / 2,
            980), "make.fun · daily news image", font=ff, fill=GREY)

    out = os.path.join(ROOT, "entry.png")
    img.save(out, "PNG", optimize=True)
    print("wrote", out, os.path.getsize(out), "bytes",
          img.size, img.mode)


if __name__ == "__main__":
    main()
