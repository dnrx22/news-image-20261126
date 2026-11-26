#!/usr/bin/env python3
"""news-image-20261126 -- draw one image summing up the world news of
Thursday 26 November 2026.

Deterministic, stdlib only, no network. Writes entry.png (1200x800) to
$MAKEFUN_OUTPUT_DIR or /output.

Scenes (all real headlines from 26 Nov 2026, found by web search):
  1. Ukraine strikes Russia's Savasleyka air base, damaging 5 warplanes
     (3 MiG-31, 2 Su-34) and hitting two oil refineries in Samara.
  2. The 100th Macy's Thanksgiving Day Parade in New York is postponed
     to Saturday -- the first postponement ever due to weather (nor'easter).
  3. North Korea's Kim Jong Un calls for wider deployment of tactical
     nuclear weapons (KCNA, Thursday 26 Nov 2026).
  4. Champions League wild night: Roma hold PSG 2-2 (ending PSG's
     perfect record), Liverpool win 3-0 at Club Brugge, Man Utd draw
     2-2 at Sporting, Bayern lose 2-1 at Lille.
"""

import hashlib
import math
import os
import struct
import zlib

WIDTH = 1200
HEIGHT = 800

# ---------------------------------------------------------------- 5x7 font
# Each glyph: 7 rows of 5 bits, "1" = ink.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "%": ("10001", "10010", "00010", "00100", "01000", "01001", "10001"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "+": ("00000", "00100", "00100", "01110", "00100", "00100", "00000"),
}


def text_width(text, scale):
    return len(text) * 6 * scale - scale


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg) * (w * h)

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = color

    def rect(self, x, y, w, h, color):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                off = base + (xx - x0) * 3
                self.px[off:off + 3] = color

    def circle(self, cx, cy, r, color):
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            self.rect(cx - dx, cy + dy, 2 * dx + 1, 1, color)

    def ellipse(self, cx, cy, rx, ry, color):
        for dy in range(-ry, ry + 1):
            t = 1.0 - (dy * dy) / float(ry * ry)
            dx = int(rx * (t ** 0.5)) if t > 0 else 0
            self.rect(cx - dx, cy + dy, 2 * dx + 1, 1, color)

    def line(self, x0, y0, x1, y1, color, thick=1):
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(steps + 1):
            x = x0 + (x1 - x0) * i // steps
            y = y0 + (y1 - y0) * i // steps
            self.rect(x - thick // 2, y - thick // 2, thick, thick, color)

    def poly(self, points, color):
        # scanline fill of a simple polygon
        ys = [p[1] for p in points]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(points)
            for i in range(n):
                x0, y0 = points[i]
                x1, y1 = points[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                self.rect(int(xs[j]), y, int(xs[j + 1]) - int(xs[j]) + 1, 1, color)

    def text(self, x, y, s, scale, color):
        cx = x
        for ch in s:
            glyph = FONT.get(ch, FONT[" "])
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == "1":
                        self.rect(cx + col * scale, y + row * scale,
                                  scale, scale, color)
            cx += 6 * scale

    def text_center(self, cx, y, s, scale, color):
        self.text(cx - text_width(s, scale) // 2, y, s, scale, color)


# ---------------------------------------------------------------- colours
NAVY = bytes((20, 33, 61))
NAVY2 = bytes((27, 42, 74))
CREAM = bytes((245, 241, 230))
RED = bytes((214, 40, 40))
GOLD = bytes((255, 209, 102))
WHITE = bytes((255, 255, 255))
BLACK = bytes((15, 15, 15))
ORANGE = bytes((232, 114, 42))
YELLOW = bytes((255, 180, 0))
GREY = bytes((120, 124, 130))
DARKGREY = bytes((58, 58, 58))
GREEN = bytes((46, 125, 50))
GREEN2 = bytes((56, 142, 60))
SKY = bytes((107, 124, 140))

PANEL_W = 576
PANEL_H = 324
LABEL_H = 84


def label_bar(cv, px, py, line1, line2):
    cv.rect(px, py + PANEL_H - LABEL_H, PANEL_W, LABEL_H, NAVY)
    cv.rect(px, py + PANEL_H - LABEL_H, PANEL_W, 4, RED)
    cv.text_center(px + PANEL_W // 2, py + PANEL_H - LABEL_H + 14,
                   line1, 2, WHITE)
    cv.text_center(px + PANEL_W // 2, py + PANEL_H - LABEL_H + 46,
                   line2, 2, GOLD)


def draw_jet(cv, x, y, scale, color):
    # simple side-view fighter silhouette, nose pointing right
    body = [(x, y), (x + 46 * scale, y - 6 * scale),
            (x + 62 * scale, y), (x + 46 * scale, y + 6 * scale)]
    cv.poly(body, color)
    wing = [(x + 18 * scale, y - 2 * scale), (x + 30 * scale, y - 18 * scale),
            (x + 38 * scale, y - 18 * scale), (x + 30 * scale, y + 2 * scale)]
    cv.poly(wing, color)
    tail = [(x + 2 * scale, y - 2 * scale), (x + 8 * scale, y - 14 * scale),
            (x + 14 * scale, y - 14 * scale), (x + 12 * scale, y + 2 * scale)]
    cv.poly(tail, color)
    cv.rect(x - 4 * scale, y - 2 * scale, 6 * scale, 4 * scale, ORANGE)


def scene_ukraine(cv, px, py):
    # dusk sky, runway, jets, explosion over the air base
    cv.rect(px, py, PANEL_W, 150, NAVY2)
    cv.rect(px, py + 150, PANEL_W, 40, ORANGE)
    cv.rect(px, py + 190, PANEL_W, 50, BLACK)
    cv.rect(px, py + 205, PANEL_W, 8, GREY)
    for dx in range(20, PANEL_W, 70):
        cv.rect(px + dx, py + 207, 34, 4, WHITE)
    draw_jet(cv, px + 70, py + 55, 1, bytes((200, 200, 200)))
    draw_jet(cv, px + 225, py + 62, 1, bytes((170, 170, 170)))
    # smoke plume rising above the blast, then the fireball itself
    cv.circle(px + 408, py + 92, 30, GREY)
    cv.circle(px + 452, py + 66, 34, GREY)
    cv.circle(px + 496, py + 92, 26, GREY)
    cv.circle(px + 450, py + 150, 52, bytes((255, 107, 0)))
    cv.circle(px + 450, py + 150, 36, YELLOW)
    cv.circle(px + 450, py + 150, 19, bytes((255, 230, 109)))
    cv.circle(px + 414, py + 172, 15, bytes((255, 107, 0)))
    label_bar(cv, px, py, "UKRAINE HITS RUSSIAN AIR BASE",
              "5 WARPLANES DAMAGED")


def scene_parade(cv, px, py):
    # storm sky, rain, deflated balloon on a New York street
    cv.rect(px, py, PANEL_W, 240, SKY)
    cv.ellipse(px + 110, py + 45, 130, 30, bytes((70, 80, 92)))
    cv.ellipse(px + 330, py + 30, 150, 34, bytes((60, 70, 82)))
    cv.ellipse(px + 500, py + 60, 110, 28, bytes((70, 80, 92)))
    # rain streaks
    for dx in range(10, PANEL_W, 42):
        cv.line(px + dx, py + 90, px + dx - 14, py + 150,
                bytes((210, 225, 235)), 2)
    for dx in range(30, PANEL_W, 42):
        cv.line(px + dx, py + 150, px + dx - 14, py + 205,
                bytes((210, 225, 235)), 2)
    # buildings
    cv.rect(px + 8, py + 120, 70, 120, DARKGREY)
    cv.rect(px + 500, py + 100, 68, 140, DARKGREY)
    for wy in (130, 160, 190):
        cv.rect(px + 22, py + wy, 14, 12, GOLD)
        cv.rect(px + 514, py + wy - 10, 14, 12, GOLD)
    # street
    cv.rect(px, py + 205, PANEL_W, 35, bytes((48, 48, 48)))
    # deflated balloon: sagging red blob with folds
    cv.ellipse(px + 290, py + 205, 150, 26, RED)
    cv.ellipse(px + 290, py + 196, 120, 16, bytes((230, 70, 70)))
    cv.ellipse(px + 240, py + 190, 46, 12, bytes((180, 30, 30)))
    cv.ellipse(px + 350, py + 192, 40, 10, bytes((180, 30, 30)))
    cv.line(px + 150, py + 215, px + 120, py + 232, WHITE, 2)
    cv.line(px + 430, py + 215, px + 460, py + 232, WHITE, 2)
    label_bar(cv, px, py, "MACY'S 100TH PARADE POSTPONED",
              "FIRST TIME EVER - STORM")


def draw_star(cv, cx, cy, r, color):
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((int(cx + rr * math.cos(ang)), int(cy + rr * math.sin(ang))))
    cv.poly(pts, color)


def scene_korea(cv, px, py):
    # night sky, mountains, missile on launcher, red flag
    cv.rect(px, py, PANEL_W, 240, bytes((16, 24, 40)))
    for sx, sy in ((40, 30), (150, 55), (260, 25), (380, 50), (500, 35),
                   (90, 80), (330, 85), (540, 75)):
        cv.rect(px + sx, py + sy, 3, 3, WHITE)
    # mountains
    cv.poly([(px, py + 240), (px + 120, py + 130), (px + 240, py + 240)],
            bytes((30, 40, 60)))
    cv.poly([(px + 300, py + 240), (px + 440, py + 150), (px + 576, py + 240)],
            bytes((24, 33, 52)))
    # flag pole + red flag
    cv.rect(px + 470, py + 60, 5, 130, WHITE)
    cv.rect(px + 475, py + 62, 78, 44, RED)
    draw_star(cv, px + 500, py + 84, 13, WHITE)
    # missile on launcher
    cv.rect(px + 180, py + 200, 120, 8, DARKGREY)
    cv.rect(px + 195, py + 210, 90, 10, GREY)
    cv.poly([(px + 232, py + 60), (px + 240, py + 40), (px + 248, py + 60)],
            RED)
    cv.rect(px + 232, py + 60, 16, 130, bytes((220, 220, 220)))
    cv.rect(px + 226, py + 120, 28, 8, bytes((180, 180, 180)))
    cv.poly([(px + 228, py + 190), (px + 252, py + 190),
             (px + 240, py + 222)], ORANGE)
    cv.poly([(px + 234, py + 190), (px + 246, py + 190),
             (px + 240, py + 210)], YELLOW)
    cv.circle(px + 240, py + 228, 12, bytes((200, 200, 200)))
    label_bar(cv, px, py, "KIM ORDERS MORE TACTICAL",
              "NUCLEAR WEAPONS DEPLOYED")


def scene_football(cv, px, py):
    # green pitch, goal, ball, scoreboard
    for i in range(6):
        cv.rect(px + i * 96, py, 96, 240, GREEN if i % 2 == 0 else GREEN2)
    # pitch lines
    cv.rect(px, py + 118, PANEL_W, 3, WHITE)
    cv.circle(px + 288, py + 120, 42, WHITE)
    cv.circle(px + 288, py + 120, 39, GREEN)
    cv.rect(px + 30, py + 30, 130, 90, WHITE)
    cv.rect(px + 33, py + 33, 124, 84, GREEN)
    # goal
    cv.rect(px + 60, py + 45, 70, 6, WHITE)
    cv.rect(px + 60, py + 45, 6, 55, WHITE)
    cv.rect(px + 124, py + 45, 6, 55, WHITE)
    # ball
    cv.circle(px + 430, py + 175, 26, WHITE)
    cv.poly([(px + 430, py + 162), (px + 441, py + 170), (px + 437, py + 184),
             (px + 423, py + 184), (px + 419, py + 170)], BLACK)
    # scoreboard
    cv.rect(px + 300, py + 18, 258, 62, NAVY)
    cv.text(px + 314, py + 28, "PSG 2-2 ROMA", 2, WHITE)
    cv.text(px + 314, py + 54, "LIVERPOOL 3-0 BRUGGE", 2, GOLD)
    label_bar(cv, px, py, "CHAMPIONS LEAGUE WILD NIGHT",
              "ROMA END PSG PERFECT RECORD")


# ---------------------------------------------------------------- PNG encoder
def png_chunk(typ, data):
    chunk = struct.pack(">I", len(data)) + typ + data
    chunk += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    return chunk


def encode_png(cv):
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)  # filter: none
        raw += cv.px[y * cv.w * 3:(y + 1) * cv.w * 3]
    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    out = bytearray(b"\x89PNG\r\n\x1a\n")
    out += png_chunk(b"IHDR", ihdr)
    out += png_chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    out += png_chunk(b"IEND", b"")
    return bytes(out)


# ---------------------------------------------------------------- main
def build():
    cv = Canvas(WIDTH, HEIGHT, CREAM)
    # banner
    cv.rect(0, 0, WIDTH, 104, NAVY)
    cv.rect(0, 104, WIDTH, 6, RED)
    cv.text_center(WIDTH // 2, 18, "26 NOVEMBER 2026", 5, WHITE)
    cv.text_center(WIDTH // 2, 66, "THE WORLD IN ONE DAY", 2, GOLD)
    # 2x2 panels
    scene_ukraine(cv, 16, 126)
    scene_parade(cv, 608, 126)
    scene_korea(cv, 16, 466)
    scene_football(cv, 608, 466)
    return encode_png(cv)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    data = build()
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    print(f"Wrote {path}: {len(data)} bytes, {WIDTH}x{HEIGHT}")
    print("sha256:", hashlib.sha256(data).hexdigest())


if __name__ == "__main__":
    main()
