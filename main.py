#!/usr/bin/env python3
"""Draw one newspaper front page summing up 26 November 2026 world news.

Python 3.13 standard library only. No network. Deterministic: every run
writes the exact same bytes to entry.png.
"""
import os
import struct
import zlib

W, H = 1024, 1024
PAPER = (247, 242, 232)
INK = (18, 18, 18)
RED = (178, 34, 34)
BLUE = (28, 78, 158)
DARKBLUE = (16, 48, 96)
GREEN = (46, 125, 50)
GOLD = (198, 148, 32)
GREY = (120, 120, 120)
LIGHTGREY = (210, 205, 195)
WHITE = (255, 255, 255)
SKY = (135, 190, 235)

# 5x7 bitmap font: each glyph is 7 rows of 5 bits.
FONT = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["01110", "00100", "00100", "00100", "00100", "00100", "01110"],
    "J": ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "10101", "01010"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00110", "01000", "10000", "11111"],
    "3": ["11111", "00010", "00100", "00010", "00001", "10001", "01110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00010", "01100"],
    " ": ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
    ".": ["00000", "00000", "00000", "00000", "00000", "01100", "01100"],
    ",": ["00000", "00000", "00000", "00000", "01100", "00100", "01000"],
    "'": ["00100", "00100", "01000", "00000", "00000", "00000", "00000"],
    "-": ["00000", "00000", "00000", "01110", "00000", "00000", "00000"],
    ":": ["00000", "01100", "01100", "00000", "01100", "01100", "00000"],
    ";": ["00000", "01100", "01100", "00000", "01100", "00100", "01000"],
    "!": ["00100", "00100", "00100", "00100", "00100", "00000", "00100"],
    "?": ["01110", "10001", "00001", "00110", "00100", "00000", "00100"],
    "&": ["01100", "10010", "10100", "01000", "10101", "10010", "01101"],
    "%": ["11001", "11010", "00010", "00100", "01000", "01011", "10011"],
    "$": ["00100", "01111", "10100", "01110", "00101", "11110", "00100"],
    "/": ["00001", "00010", "00010", "00100", "01000", "01000", "10000"],
    "(": ["00010", "00100", "01000", "01000", "01000", "00100", "00010"],
    ")": ["01000", "00100", "00010", "00010", "00010", "00100", "01000"],
    "+": ["00000", "00100", "00100", "11111", "00100", "00100", "00000"],
    "=": ["00000", "00000", "11111", "00000", "11111", "00000", "00000"],
    '"': ["01010", "01010", "00000", "00000", "00000", "00000", "00000"],
    "*": ["00000", "10101", "01110", "10101", "00000", "00000", "00000"],
}


class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * w * h)

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def rect(self, x, y, w, h, c):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, c)

    def hline(self, x, y, w, c):
        self.rect(x, y, w, 1, c)

    def circle(self, cx, cy, r, c):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.set(xx, yy, c)

    def ellipse(self, cx, cy, rx, ry, c):
        for yy in range(cy - ry, cy + ry + 1):
            for xx in range(cx - rx, cx + rx + 1):
                if ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1:
                    self.set(xx, yy, c)

    def line(self, x0, y0, x1, y1, c):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        x, y = x0, y0
        while True:
            self.set(x, y, c)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

    def thick_line(self, x0, y0, x1, y1, c, t=2):
        for dy in range(-t // 2, t // 2 + 1):
            for dx in range(-t // 2, t // 2 + 1):
                self.line(x0 + dx, y0 + dy, x1 + dx, y1 + dy, c)

    def text(self, x, y, s, scale, c):
        cx = x
        for ch in s.upper():
            glyph = FONT.get(ch, FONT[" "])
            for row in range(7):
                for col in range(5):
                    if glyph[row][col] == "1":
                        self.rect(cx + col * scale, y + row * scale, scale, scale, c)
            cx += 6 * scale
        return cx

    def text_width(self, s, scale):
        return len(s) * 6 * scale - scale

    def text_centered(self, y, s, scale, c):
        x = (self.w - self.text_width(s, scale)) // 2
        self.text(x, y, s, scale, c)
        return x

    def wrap(self, s, max_chars):
        lines, cur = [], ""
        for word in s.split(" "):
            if cur and len(cur) + 1 + len(word) > max_chars:
                lines.append(cur)
                cur = word
            elif cur:
                cur += " " + word
            else:
                cur = word
        if cur:
            lines.append(cur)
        return lines

    def para(self, x, y, s, scale, c, max_width):
        max_chars = max(1, max_width // (6 * scale))
        lines = self.wrap(s, max_chars)
        for i, line in enumerate(lines):
            self.text(x, y + i * 9 * scale, line, scale, c)
        return y + len(lines) * 9 * scale


def draw_space_station(cv, x, y, w, h):
    # Sky panel, Earth below, station above it.
    cv.rect(x, y, w, h, SKY)
    cv.ellipse(x + w // 2, y + h + 60, w // 2, 90, BLUE)
    cv.ellipse(x + w // 2 - 90, y + h - 12, 70, 22, GREEN)
    cv.ellipse(x + w // 2 + 110, y + h - 28, 55, 18, GREEN)
    cv.ellipse(x + w // 2 + 20, y + h - 6, 45, 14, GREEN)
    cv.rect(x + 30, y + 22, 90, 10, WHITE)
    cv.rect(x + 130, y + 30, 70, 8, WHITE)
    # Station: central module + solar panels.
    cx, cy = x + w // 2, y + 78
    cv.rect(cx - 95, cy - 8, 60, 16, DARKBLUE)
    cv.rect(cx + 35, cy - 8, 60, 16, DARKBLUE)
    cv.rect(cx - 38, cy - 14, 76, 28, (200, 200, 200))
    cv.rect(cx - 38, cy - 14, 76, 6, WHITE)
    cv.line(cx, cy - 14, cx, cy - 38, INK)
    cv.circle(cx, cy - 42, 5, RED)
    cv.rect(cx - 95, cy - 8, 60, 3, WHITE)
    cv.rect(cx + 35, cy - 8, 60, 3, WHITE)
    # Clip the Earth to its panel: cover any part spilling below it.
    # The ellipse bottom reaches y+h+150, so cover 160 px down.
    cv.rect(x, y + h, w, 160, PAPER)
    cv.text(x + 14, y + 8, "TIANGONG ORBITS EARTH", 1, INK)


def draw_bank(cv, x, y, s=1):
    # Tiny bank building, fits in a 32x32 box beside a headline.
    cv.line(x + 16, y + 1, x + 1, y + 13, INK)
    cv.line(x + 16, y + 1, x + 31, y + 13, INK)
    cv.rect(x, y + 13, 32, 2, INK)
    for i in range(3):
        cv.rect(x + 3 + i * 10, y + 16, 3, 11, INK)
    cv.rect(x, y + 28, 32, 3, INK)


def draw_oil_rig(cv, x, y):
    # Tiny oil rig, fits in a 32x32 box.
    cv.rect(x + 2, y + 20, 28, 3, INK)
    cv.line(x + 6, y + 31, x + 11, y + 20, INK)
    cv.line(x + 26, y + 31, x + 21, y + 20, INK)
    cv.line(x + 16, y + 20, x + 16, y + 2, INK)
    cv.line(x + 16, y + 2, x + 9, y + 20, INK)
    cv.line(x + 16, y + 2, x + 23, y + 20, INK)
    cv.rect(x + 12, y + 14, 8, 6, RED)
    cv.circle(x + 27, y + 5, 3, GOLD)


def draw_dove(cv, x, y):
    # Tiny dove with an olive branch, fits in a 32x32 box.
    cv.ellipse(x + 14, y + 14, 12, 6, WHITE)
    cv.circle(x + 24, y + 10, 4, WHITE)
    cv.line(x + 27, y + 8, x + 31, y + 6, GOLD)
    cv.ellipse(x + 10, y + 7, 7, 4, (235, 235, 235))
    cv.line(x + 2, y + 24, x + 12, y + 28, GREEN)
    cv.circle(x + 5, y + 23, 2, GREEN)
    cv.circle(x + 10, y + 27, 2, GREEN)


def draw_cricket(cv, x, y):
    # Tiny cricket bat and ball, fits in a 32x32 box.
    cv.rect(x + 12, y + 1, 6, 16, (160, 110, 60))
    cv.rect(x + 13, y + 17, 4, 11, (120, 80, 40))
    cv.circle(x + 25, y + 23, 5, RED)


def draw_mercury(cv, x, y):
    # Tiny cratered Mercury, fits in a 32x32 box.
    cv.circle(x + 15, y + 15, 12, (170, 120, 80))
    cv.circle(x + 11, y + 12, 2, (120, 80, 50))
    cv.circle(x + 19, y + 18, 2, (120, 80, 50))
    cv.circle(x + 17, y + 10, 1, (120, 80, 50))


STORIES = [
    # (headline, summary, icon) — summaries kept short so all fit.
    ("US CONFIDENCE NEAR 2-YEAR HIGH",
     "Confidence climbs despite inflation. Canada acts as energy shocks loom.",
     "bank"),
    ("PETROBRAS UNVEILS $122BN PLAN",
     "Brazil's oil giant plans huge investment as its energy ambitions grow.",
     "oil"),
    ("VENEZUELA REVEALS $237.5BN DEBT",
     "Vast public debt is disclosed as a historic restructuring is prepared.",
     None),
    ("COLOMBIA: 10 YEARS AFTER PEACE",
     "A decade on, the UN warns key commitments are still unfinished.",
     "dove"),
    ("INDIA MARKS CONSTITUTION DAY",
     "India backs human control of AI in war, and a Nepal aid package.",
     None),
    ("BANGLADESH WAGE WIN",
     "Garment workers win a 36% rise in the minimum wage.",
     None),
    ("MISSION REACHES MERCURY",
     "A Japanese-European mission arrives after an eight-year journey.",
     "mercury"),
    ("US SHELVES RUSSIA DEAL PLAN",
     "Washington drops the plan. Moscow's figures show nearly 500,000 lost.",
     None),
    ("SWISS OFFICE SHUT IN PYONGYANG",
     "Pyongyang tells Switzerland to close its newly opened office.",
     None),
    ("IPL AUCTION: 1,220 REGISTER",
     "Gukesh reaches the chess final. New Zealand hold India to a draw.",
     "cricket"),
    ("5.6 QUAKE HITS NEPAL",
     "A magnitude 5.6 quake strikes Koshi Province near the Chinese border.",
     None),
]

ICON_DRAW = {"bank": draw_bank, "oil": draw_oil_rig, "dove": draw_dove,
             "cricket": draw_cricket, "mercury": draw_mercury}


def build():
    cv = Canvas(W, H, PAPER)
    cv.rect(0, 0, W, 6, INK)
    cv.rect(0, H - 6, W, 6, INK)
    cv.rect(0, 0, 6, H, INK)
    cv.rect(W - 6, 0, 6, H, INK)

    # Masthead.
    cv.text_centered(22, "WORLD NEWS", 8, INK)
    cv.text_centered(96, "THURSDAY 26 NOVEMBER 2026", 3, RED)
    cv.hline(20, 134, W - 40, INK)
    cv.hline(20, 138, W - 40, INK)

    # Lead label + headline.
    cv.text(20, 156, "LEAD STORY", 2, RED)
    y = cv.para(20, 182, "FIRST PAKISTANI ASTRONAUT JOINS CHINA'S TIANGONG STATION", 4, INK, 984)
    # Lead picture (left) + summary (right).
    pic_y = 268
    draw_space_station(cv, 20, pic_y, 470, 180)
    cv.para(520, pic_y + 8,
            "Muhammad Zeeshan Ali becomes the first foreign astronaut to travel to Tiangong, on the Shenzhou-24 mission.",
            2, INK, 484)
    cv.text(520, pic_y + 128, "A FIRST FOR PAKISTAN,", 2, RED)
    cv.text(520, pic_y + 152, "AND FOR TIANGONG.", 2, RED)

    cv.hline(20, 462, W - 40, INK)
    cv.text_centered(476, "THE REST OF THE DAY IN BRIEF", 2, INK)
    cv.hline(20, 508, W - 40, INK)

    # Lower stories in three columns: 4 / 4 / 3. Icons sit beside the
    # headline (32 px wide) so they cost no extra vertical space.
    cols = [STORIES[0:4], STORIES[4:8], STORIES[8:11]]
    col_x = [20, 355, 690]
    col_w = 314
    for ci, col in enumerate(cols):
        x = col_x[ci]
        y = 528
        for headline, summary, icon in col:
            hx, hw = x, col_w
            if icon:
                ICON_DRAW[icon](cv, x, y)
                hx, hw = x + 38, col_w - 38
            y = cv.para(hx, y, headline, 2, INK, hw)
            y += 6
            y = cv.para(x, y, summary, 2, (60, 60, 60), col_w)
            y += 12
            if ci < 2:
                cv.hline(x, y - 6, col_w, LIGHTGREY)
        if ci < 2:
            cv.rect(x + col_w + 10, 528, 2, 460, LIGHTGREY)

    cv.hline(20, 1000, W - 40, INK)
    cv.text_centered(1008, "WORLD NEWS - 26 NOVEMBER 2026", 1, INK)
    return cv


def write_png(cv, path):
    raw = bytearray()
    for yy in range(cv.h):
        raw.append(0)
        raw.extend(cv.px[yy * cv.w * 3:(yy + 1) * cv.w * 3])
    comp = zlib.compress(bytes(raw), 9)

    def chunk(typ, data):
        c = struct.pack(">I", len(data)) + typ + data
        return c + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", comp)
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    cv = build()
    n = write_png(cv, path)
    print(f"Wrote {path}: {cv.w}x{cv.h}, {n} bytes")


if __name__ == "__main__":
    main()
