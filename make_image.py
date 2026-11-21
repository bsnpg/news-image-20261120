#!/usr/bin/env python3
"""Build the news-image entry v2: one 1024x1024 newspaper page summing up
Friday 20 November 2026 world news. Deterministic, no network, PIL only.
Run:  python3 make_image.py   -> writes entry.png (1024x1024, <=1 MiB).

Design (ATM of the top-10 convergent skeleton -- structure only, our own
text and drawings): cream paper, black serif masthead, red kicker, italic
deck line, 6-stat numbers strip, coloured region bar, 3 equal lead columns
with drawn scenes, 10 small stories in a 5x2 grid with drawn mini-scenes,
a dark-navy world map with numbered pins beside a numbered briefs list, a
red-bordered DATE CHECK box, and a source footer. All 36 stories were
verified against high-credibility sources (Reuters, AP, BBC, Al Jazeera,
WSJ, ESA, IMD, ...) as first reported on Friday 20 November 2026;
Thursday's news is explicitly left out. Uncertain items carry a status tag
(Reported / Ongoing / Forecast / Officials' count).
"""
import math
from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
PAPER = (247, 242, 228)
INK = (25, 25, 25)
RED = (163, 22, 33)
NAVY = (31, 58, 95)
NAVY_D = (22, 42, 70)
GOLD = (161, 98, 7)
TEAL = (14, 107, 107)
GREY = (96, 94, 88)
LIGHT = (233, 227, 209)
CARD = (252, 249, 240)
SKY = (16, 34, 64)

DJ = "/usr/share/fonts/truetype/dejavu/"


def font(name, size):
    try:
        return ImageFont.truetype(DJ + name, size)
    except OSError:
        return ImageFont.truetype(DJ + "DejaVuSans.ttf", size)


def serif_b(s):
    return font("DejaVuSerif-Bold.ttf", s)


def serif(s):
    return font("DejaVuSerif.ttf", s)


def serif_i(s):
    try:
        return ImageFont.truetype(DJ + "DejaVuSerif-Italic.ttf", s)
    except OSError:
        return serif(s)


def sans(s):
    return font("DejaVuSans.ttf", s)


def sans_b(s):
    return font("DejaVuSans-Bold.ttf", s)


def wrap(draw, text, fnt, max_w):
    """Greedy word wrap; returns a list of lines that fit max_w."""
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def text_block(draw, x, y, text, fnt, max_w, fill=INK, leading=None):
    """Draw wrapped text; returns the y just below the last line."""
    lh = leading if leading else int(fnt.size * 1.28)
    for line in wrap(draw, text, fnt, max_w):
        draw.text((x, y), line, font=fnt, fill=fill)
        y += lh
    return y


def hline(draw, x0, x1, y, fill=INK, width=1):
    draw.line([(x0, y), (x1, y)], fill=fill, width=width)


def check_w(draw, text, fnt, max_w, where):
    """Print a warning if a single line is too wide (caught at build time)."""
    w = draw.textlength(text, font=fnt)
    if w > max_w:
        print(f"OVERFLOW {where}: {w:.0f} > {max_w} :: {text}")
    return w


# ---------------------------------------------------------------- data
# 36 stories, all verified as first reported on Friday 20 November 2026.
# Fields: n, tag, label, head, body, src, chip, region, pin (lon, lat).
LEADS = [
    dict(n=1, tag="KYIV, UKRAINE \u00b7 WAR", label="KYIV",
         head="Russian missiles hit three Kyiv bridges",
         body="An overnight barrage of about 110 missiles and 400 drones killed at "
              "least eight people across Ukraine and cut power and water in the "
              "capital. Three bridges over the Dnipro were damaged.",
         src="Reuters", chip="OFFICIALS' COUNT", region="Europe",
         pin=(30.5, 50.4)),
    dict(n=2, tag="ODISHA, INDIA \u00b7 CYCLONE", label="CYCLONE AKVAN",
         head="Cyclone Akvan comes ashore in eastern India",
         body="The storm crossed the coast near Gopalpur from about 8 am, after more "
              "than 300,000 people were moved to shelters. Winds reached 70 to "
              "80 km/h, gusting to 90; no deaths were reported.",
         src="IMD, Reuters", chip="WEATHER OFFICE", region="Asia",
         pin=(85.2, 19.3)),
    dict(n=3, tag="TOKYO \u00b7 SEOUL \u00b7 TAIPEI \u00b7 MARKETS", label="AI SELL-OFF",
         head="AI sell-off sinks Asia's stock markets",
         body="Taiwan's index fell 6.2% to end its worst week in decades. Seoul lost "
              "5.2% and Tokyo 5.1% as chipmakers led the slide. SoftBank dropped "
              "more than 14%.",
         src="Al Jazeera, WSJ", chip="CLOSING PRICES", region="Asia",
         pin=(139.7, 35.7)),
]

SMALL = [
    dict(n=4, tag="BRUSSELS \u00b7 DIPLOMACY", head="UK and EU seal a \u201creset\u201d deal",
         body="Food trade, visas, carbon.", src="Reuters", scene="flags", ban="UK-EU RESET",
         region="Europe"),
    dict(n=5, tag="ANTALYA \u00b7 CLIMATE \u00b7 ONGOING",
         head="COP31 reaches its last day with no deal",
         body="Draft leaves out fossil fuels.", src="UN News", scene="globe", ban="COP31: NO DEAL",
         region="Europe"),
    dict(n=6, tag="POLAND \u00b7 SECURITY \u00b7 REPORTED",
         head="Russian cruise missile lands in Poland",
         body="Field landing; airports shut.", src="Reuters", scene="missile", ban="POLAND: MISSILE",
         region="Europe"),
    dict(n=7, tag="CENTRAL IRAQ \u00b7 SECURITY",
         head="Iraqi army enters a militia stronghold",
         body="Troops enter Jurf al-Sakhar.", src="Reuters", scene="convoy", ban="IRAQ: ARMY IN",
         region="Middle East"),
    dict(n=8, tag="ITALY \u00b7 LABOUR", head="General strike over Italy's budget",
         body="Workers and students march.", src="Reuters", scene="crowd", ban="ITALY: STRIKE",
         region="Europe"),
    dict(n=9, tag="TOKYO \u00b7 ECONOMY", head="Japan's inflation picks up to 2.3%",
         body="Headline CPI; rise in view.", src="Reuters", scene="chart", ban="JAPAN: +2.3%",
         region="Asia"),
    dict(n=10, tag="MERCURY \u00b7 SPACE \u00b7 FORECAST",
         head="BepiColombo poised for Mercury orbit",
         body="Commands sent; burn Saturday.", src="ESA", scene="space", ban="MERCURY ORBIT",
         region="Global"),
    dict(n=11, tag="TURKANA, KENYA \u00b7 ENERGY",
         head="Kenya starts drilling its first oil",
         body="First crude due Dec 1.", src="Capital FM", scene="rig", ban="KENYA: OIL",
         region="Africa"),
    dict(n=12, tag="BOSTON, US \u00b7 COURTS",
         head="US judge open to blocking Trump green-card freeze",
         body="Freeze challenged in court.", src="Reuters", scene="court", ban="BOSTON: FREEZE",
         region="Americas"),
    dict(n=13, tag="WELLINGTON \u00b7 CRICKET", head="Phillips hits 118 against India",
         body="Hundreds in all three formats.", src="AP", scene="cricket", ban="PHILLIPS: 118",
         region="Oceania"),
]

# briefs: n, place, headline, source, region (one line each in the tail list)
BRIEFS = [
    (14, "Seoul", "Impeach top judge", "Yonhap", "Asia"),
    (15, "Riyadh", "Houthis warn Red Sea ports", "Reuters", "Middle East"),
    (16, "Hormuz", "Brent settles $92.57", "Reuters", "Middle East"),
    (17, "California", "M5.0 quake, no injuries", "AP", "Americas"),
    (18, "Europe", "Strike in 25 countries", "CNN", "Europe"),
    (19, "Colombo", "Rate raised to 9%", "Reuters", "Asia"),
    (20, "Bayelsa", "Funeral barge capsizes", "Reuters", "Africa"),
    (21, "WFP", "$12bn appeal for 2027", "Reuters", "Global"),
    (22, "Florida", "River floods; Kyle nears", "NWS", "Americas"),
    (23, "Tokyo", "Chile\u2013Japan minerals deal", "Reuters", "Asia"),
    (24, "Gaza", "Ground op ends; 6 killed", "Al Jazeera", "Middle East"),
    (25, "Beijing", "Loan rates held 18th month", "Xinhua", "Asia"),
    (26, "Seoul", "First cholera case in a decade", "AP", "Asia"),
    (27, "Blantyre", "Fuel crisis, night queues", "Al Jazeera", "Africa"),
    (28, "Cox's Bazar", "Myanmar dismisses ruling", "AP", "Asia"),
    (29, "Shenzhen", "Xi hails Australia ties", "Reuters", "Asia"),
    (30, "Las Vegas", "Russell fastest in practice", "F1", "Americas"),
    (31, "Brussels", "EU plastic-waste ban Sat", "Reuters", "Europe"),
    (32, "UK", "PM condemns airspace breach", "Reuters", "Europe"),
    (33, "Singapore", "Indonesia gas restored", "Reuters", "Asia"),
    (34, "Washington", "Trump hails Putin talks", "Reuters", "Americas"),
    (35, "Turin", "ATP Finals semis Saturday", "ATP", "Europe"),
    (36, "Wellington", "Nicholls 175 in 216 stand", "AP", "Oceania"),
]

STATS = [
    ("3", "bridges hit in Kyiv"),
    ("300,000+", "people moved to shelters"),
    ("\u22125.1%", "Nikkei, Friday's close"),
    ("118", "Phillips' century against India"),
    ("2.3%", "Japan inflation, October"),
    ("$92.57", "Brent, Friday settle"),
]

# Region counts recomputed from the v2 story set; they sum to 36.
REGIONS = [("Europe", 9, (31, 58, 95)), ("Asia", 11, (163, 22, 33)),
           ("Middle East", 4, (161, 98, 7)), ("Africa", 3, (14, 107, 107)),
           ("Americas", 5, (107, 33, 168)), ("Oceania", 2, (46, 125, 50)),
           ("Global", 2, (96, 94, 88))]

# Map pins for stories 1-13. dx,dy = display offset in px (leader line drawn
# back to the true position); used where pins would otherwise collide.
PINS = {1: (30.5, 50.4, 5, -9), 2: (85.2, 19.3, 0, 0), 3: (139.7, 35.7, 0, 0),
        4: (4.4, 50.8, -5, -8), 5: (30.7, 36.9, 3, 12), 6: (22.0, 50.3, -6, -11),
        7: (44.4, 32.9, 7, 9), 8: (12.5, 41.9, 0, 0), 9: (139.7, 35.7, 14, -12),
        11: (36.1, 3.3, 0, 0), 12: (-71.1, 42.4, 0, 0), 13: (174.8, -41.3, 0, 0)}
# pin 10 (Mercury) is off-planet: drawn in the corner box instead.


# ---------------------------------------------------------------- lead pictures
def draw_kyiv(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=SKY)
    for fx, fy in [(0.04, 0.13), (0.13, 0.06), (0.25, 0.17), (0.38, 0.07),
                   (0.50, 0.14), (0.63, 0.06), (0.75, 0.11), (0.88, 0.05),
                   (0.19, 0.24), (0.56, 0.21), (0.81, 0.20)]:
        sx, sy = x + fx * w, y + fy * h
        d.ellipse([sx - 1, sy - 1, sx + 1, sy + 1], fill=(220, 220, 200))
    # building silhouettes (fractions of w / h)
    for fx, fw, fh in [(0.00, 0.13, 0.45), (0.15, 0.10, 0.60), (0.26, 0.15, 0.42),
                       (0.43, 0.11, 0.66), (0.55, 0.13, 0.48), (0.70, 0.15, 0.56),
                       (0.87, 0.11, 0.43)]:
        bx, bw, bh = x + fx * w, fw * w, fh * h
        d.rectangle([bx, y + h - bh, bx + bw, y + h], fill=(10, 20, 40))
        wy = y + h - bh + 8
        while wy < y + h - 6:
            wx = bx + 6
            while wx < bx + bw - 4:
                if (int(wx) + int(wy)) % 3 == 0:
                    d.rectangle([wx, wy, wx + 4, wy + 5], fill=(255, 214, 120))
                wx += 12
            wy += 12
    # missile arcs (dashed) + fire glows
    for (afx, afy, bfx, bfy) in [(0.06, 0.06, 0.38, 0.56), (0.47, 0.03, 0.78, 0.60),
                                (0.88, 0.09, 1.02, 0.50)]:
        ax, ay, bx, by = x + afx * w, y + afy * h, x + bfx * w, y + bfy * h
        for t in [i / 14 for i in range(15)]:
            px = ax + (bx - ax) * t
            py = ay + (by - ay) * t - 26 * math.sin(math.pi * t)
            d.ellipse([px - 1.5, py - 1.5, px + 1.5, py + 1.5], fill=(255, 230, 150))
    for fx, fy in [(0.38, 0.59), (0.78, 0.63), (0.98, 0.53)]:
        fxp, fyp = x + fx * w, y + fy * h
        d.ellipse([fxp - 7, fyp - 7, fxp + 7, fyp + 7], fill=(255, 140, 40))
        d.ellipse([fxp - 3, fyp - 3, fxp + 3, fyp + 3], fill=(255, 220, 120))
    # bridge across the bottom
    d.rectangle([x, y + h - 12, x + w, y + h - 8], fill=(30, 30, 34))
    px = x + 8
    while px < x + w - 8:
        d.line([(px, y + h - 8), (px, y + h - 26)], fill=(30, 30, 34), width=3)
        px += 26
    d.rectangle([x, y + h - 26, x + w, y + h - 23], fill=(30, 30, 34))


def draw_cyclone(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(38, 110, 150))
    # land (left) and sea (right)
    d.polygon([(x, y), (x + 74, y), (x + 92, y + h // 2), (x + 70, y + h), (x, y + h)],
              fill=(214, 196, 150))
    d.line([(x + 74, y), (x + 92, y + h // 2), (x + 70, y + h)], fill=(120, 90, 60), width=2)
    # spiral (capped so it stays inside the picture)
    cx, cy = x + w - 70, y + h // 2 + 4
    for r in range(8, 48, 8):
        a0 = r * 0.35
        pts = []
        for k in range(41):
            a = a0 + k / 40.0 * 4.6
            rr = r + k * 0.25
            pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a) * 0.9))
        d.line(pts, fill=(255, 255, 255), width=3)
    d.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=RED)
    d.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], fill=(255, 255, 255))
    # rain streaks
    for rx in range(x + 10, x + w - 10, 18):
        d.line([(rx, y + 8), (rx - 6, y + 26)], fill=(200, 225, 240), width=2)
    d.rectangle([x, y + h - 20, x + w, y + h], fill=(22, 42, 70))
    d.text((x + 8, y + h - 17), "LANDFALL  \u00b7  8 AM", font=sans_b(11),
           fill=(255, 255, 255))


def draw_market(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(18, 20, 26))
    for gy in range(y + 14, y + h - 8, 22):
        d.line([(x + 6, gy), (x + w - 6, gy)], fill=(48, 52, 60), width=1)
    fx = [0.03, 0.19, 0.34, 0.50, 0.66, 0.81, 0.97]
    fy = [0.16, 0.25, 0.22, 0.42, 0.38, 0.59, 0.70]
    pts = [(x + a * w, y + b * h) for a, b in zip(fx, fy)]
    pts[-1] = (x + w - 10, y + h - 14)
    d.line(pts, fill=(220, 60, 60), width=4)
    for px, py in pts[1:-1]:
        d.ellipse([px - 3, py - 3, px + 3, py + 3], fill=(255, 120, 120))
    d.text((x + 10, y + h - 18), "TAIPEI \u22126.2%  \u00b7  SEOUL \u22125.2%",
           font=sans_b(10), fill=(255, 255, 255))


LEAD_DRAW = {1: draw_kyiv, 2: draw_cyclone, 3: draw_market}


# ---------------------------------------------------------------- mini scenes
def scene_flags(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(214, 226, 240))
    # UK flag (left half)
    d.rectangle([x + 4, y + 6, x + w // 2 - 2, y + h - 10], fill=(28, 52, 120))
    d.rectangle([x + 4, y + h // 2 - 3, x + w // 2 - 2, y + h // 2 + 3],
                fill=(255, 255, 255))
    d.rectangle([x + w // 4 - 3, y + 6, x + w // 4 + 3, y + h - 10],
                fill=(255, 255, 255))
    d.rectangle([x + 4, y + h // 2 - 1, x + w // 2 - 2, y + h // 2 + 1],
                fill=(200, 30, 40))
    d.rectangle([x + w // 4 - 1, y + 6, x + w // 4 + 1, y + h - 10],
                fill=(200, 30, 40))
    # EU flag (right half)
    d.rectangle([x + w // 2 + 2, y + 6, x + w - 4, y + h - 10], fill=(0, 51, 153))
    cx, cy = x + 3 * w // 4, y + h // 2
    for k in range(12):
        a = k * math.pi / 6
        d.ellipse([cx + 11 * math.cos(a) - 1.5, cy + 11 * math.sin(a) - 1.5,
                   cx + 11 * math.cos(a) + 1.5, cy + 11 * math.sin(a) + 1.5],
                  fill=(255, 210, 0))
    d.rectangle([x, y + h - 8, x + w, y + h], fill=(120, 140, 90))


def scene_globe(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(220, 232, 240))
    d.ellipse([x + w - 28, y + 4, x + w - 12, y + 20], fill=(255, 200, 60))
    d.polygon([(x, y + h), (x, y + h - 14), (x + w // 2, y + h - 22),
               (x + w, y + h - 12), (x + w, y + h)], fill=(90, 160, 90))
    d.polygon([(x, y + h), (x, y + h - 8), (x + w // 2, y + h - 14),
               (x + w, y + h - 6), (x + w, y + h)], fill=(60, 130, 70))
    cx, cy, r = x + 34, y + 22, 16
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(46, 125, 190),
              outline=(20, 60, 110), width=2)
    d.ellipse([cx - 8, cy - 6, cx + 2, cy + 4], fill=(90, 180, 110))
    d.ellipse([cx + 2, cy + 4, cx + 10, cy + 12], fill=(90, 180, 110))
    tx = x + w - 48
    d.rectangle([tx, y + 8, tx + 8, y + h - 16], fill=(255, 255, 255),
                outline=INK, width=1)
    d.rectangle([tx + 2, y + 16, tx + 6, y + h - 16], fill=RED)
    d.ellipse([tx - 3, y + h - 20, tx + 11, y + h - 8], fill=RED)


def scene_missile(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(200, 220, 240))
    d.rectangle([x, y + h - 20, x + w, y + h], fill=(110, 160, 70))
    d.polygon([(x + 30, y + h - 14), (x + 110, y + 14), (x + 126, y + 10),
               (x + 60, y + h - 8)], fill=(140, 140, 140))
    d.polygon([(x + 110, y + 14), (x + 126, y + 10), (x + 118, y + 24)], fill=RED)
    d.ellipse([x + 120, y + 8, x + 140, y + 22], fill=(240, 240, 240))
    d.ellipse([x + 132, y + 2, x + 148, y + 14], fill=(220, 220, 220))
    for gx in range(x + 8, x + w - 8, 16):
        d.line([(gx, y + h - 2), (gx + 3, y + h - 12)], fill=(70, 120, 50), width=2)


def scene_convoy(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(240, 220, 180))
    d.ellipse([x + w - 24, y + 4, x + w - 8, y + 20], fill=(255, 210, 120))
    d.rectangle([x, y + h - 18, x + w, y + h], fill=(210, 180, 130))
    d.rectangle([x, y + h - 26, x + w, y + h - 18], fill=(90, 80, 70))
    for tx in [x + 28, x + 84, x + 138]:
        d.rectangle([tx, y + h - 38, tx + 34, y + h - 26], fill=(120, 100, 60))
        d.rectangle([tx + 24, y + h - 38, tx + 34, y + h - 30], fill=(90, 120, 160))
        d.ellipse([tx + 6, y + h - 28, tx + 12, y + h - 22], fill=(20, 20, 20))
        d.ellipse([tx + 22, y + h - 28, tx + 28, y + h - 22], fill=(20, 20, 20))
    for px in [x + 6, x + w - 12]:
        d.line([(px, y + h - 18), (px, y + 14)], fill=(120, 90, 50), width=3)
        for a in [-0.6, -0.2, 0.2, 0.6]:
            d.line([(px, y + 14), (px + 14 * math.sin(a), y + 14 - 10 * math.cos(a))],
                   fill=(60, 130, 60), width=2)


def scene_crowd(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(225, 225, 220))
    d.rectangle([x, y + h - 14, x + w, y + h], fill=(140, 140, 135))
    d.line([(x + 40, y + 8), (x + 40, y + 30)], fill=INK, width=2)
    d.rectangle([x + 28, y + 2, x + 56, y + 12], fill=(255, 255, 255),
                outline=RED, width=1)
    d.line([(x + 140, y + 10), (x + 140, y + 32)], fill=INK, width=2)
    d.rectangle([x + 128, y + 4, x + 156, y + 14], fill=(255, 255, 255),
                outline=RED, width=1)
    cols = [INK, RED, (30, 60, 120), (120, 60, 30), TEAL, (90, 90, 90)]
    for i, cx in enumerate(range(x + 12, x + w - 8, 18)):
        d.ellipse([cx - 5, y + 24, cx + 5, y + 34], fill=cols[i % len(cols)])
        d.polygon([(cx - 7, y + h - 14), (cx + 7, y + h - 14), (cx, y + 34)],
                  fill=cols[i % len(cols)])


def scene_chart(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(252, 249, 240))
    d.ellipse([x + w - 34, y + 4, x + w - 10, y + 28], fill=RED)
    for i, bh in enumerate([14, 18, 15, 22, 28]):
        bx = x + 10 + i * 16
        d.rectangle([bx, y + h - 10 - bh, bx + 11, y + h - 10],
                    fill=TEAL if i < 4 else RED)
    d.line([(x + 6, y + h - 10), (x + w - 6, y + h - 10)], fill=INK, width=1)
    d.text((x + 8, y + 2), "+2.3%", font=sans_b(12), fill=RED)


def scene_space(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(16, 24, 48))
    for sx, sy in [(12, 8), (40, 16), (70, 6), (100, 12), (130, 8), (160, 18),
                   (180, 6), (55, 24), (115, 26)]:
        d.ellipse([x + sx - 1, y + sy - 1, x + sx + 1, y + sy + 1],
                  fill=(255, 255, 255))
    d.ellipse([x + 8, y + 10, x + 44, y + 46], fill=(170, 160, 150))
    d.ellipse([x + 16, y + 18, x + 22, y + 24], fill=(130, 120, 110))
    d.ellipse([x + 28, y + 28, x + 34, y + 34], fill=(130, 120, 110))
    d.rectangle([x + 120, y + 18, x + 136, y + 30], fill=(220, 220, 220))
    d.rectangle([x + 104, y + 22, x + 120, y + 26], fill=(90, 140, 200))
    d.rectangle([x + 136, y + 22, x + 152, y + 26], fill=(90, 140, 200))
    d.line([(x + 44, y + 28), (x + 70, y + 20), (x + 95, y + 24), (x + 120, y + 24)],
           fill=(255, 210, 120), width=2)


def scene_rig(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + 18], fill=(255, 180, 90))
    d.rectangle([x, y + 18, x + w, y + 36], fill=(255, 140, 60))
    d.rectangle([x, y + 36, x + w, y + h], fill=(200, 90, 40))
    d.ellipse([x + w // 2 - 10, y + 8, x + w // 2 + 10, y + 28],
              fill=(255, 230, 150))
    d.polygon([(x + 30, y + h), (x + w // 2 - 4, y + 8), (x + w // 2 + 4, y + 8),
               (x + w - 30, y + h)], outline=(30, 20, 10), width=3)
    d.line([(x + w // 2, y + 8), (x + w - 24, y + 20)], fill=(30, 20, 10), width=3)
    d.rectangle([x, y + h - 6, x + w, y + h], fill=(40, 25, 15))


def scene_court(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(232, 228, 218))
    d.polygon([(x + w // 2 - 30, y + 16), (x + w // 2 + 30, y + 16),
               (x + w // 2, y + 4)], fill=(245, 242, 235), outline=INK)
    for cx in [x + 24, x + 60, x + 96, x + 132]:
        d.rectangle([cx, y + 18, cx + 8, y + h - 12], fill=(250, 248, 242),
                    outline=INK)
    d.rectangle([x + 16, y + h - 12, x + w - 16, y + h - 8], fill=(120, 110, 100))
    d.rectangle([x + w - 34, y + h - 22, x + w - 12, y + h - 14], fill=(120, 80, 40))
    d.line([(x + w - 23, y + h - 14), (x + w - 23, y + h - 4)], fill=(90, 60, 30),
           width=3)


def scene_cricket(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(120, 180, 90))
    d.rectangle([x + w // 2 - 14, y + 6, x + w // 2 + 14, y + h - 8],
                fill=(220, 200, 150))
    for sx in [x + w // 2 - 6, x + w // 2, x + w // 2 + 6]:
        d.line([(sx, y + 10), (sx, y + 20)], fill=(240, 220, 120), width=2)
    d.rectangle([x + 24, y + 14, x + 34, y + h - 14], fill=(190, 150, 90))
    d.rectangle([x + 27, y + 6, x + 31, y + 14], fill=(120, 90, 50))
    d.ellipse([x + w - 30, y + h - 24, x + w - 18, y + h - 12], fill=RED)
    d.text((x + w - 52, y + 4), "118", font=sans_b(14), fill=RED)


SCENES = {"flags": scene_flags, "globe": scene_globe, "missile": scene_missile,
          "convoy": scene_convoy, "crowd": scene_crowd, "chart": scene_chart,
          "space": scene_space, "rig": scene_rig, "court": scene_court,
          "cricket": scene_cricket}

# ---------------------------------------------------------------- map
# Simplified continent outlines (lon, lat). Equirectangular projection.
CONTINENTS = [
    [(-168, 66), (-150, 70), (-135, 69), (-125, 71), (-110, 68), (-95, 69), (-85, 66),
     (-80, 73), (-70, 62), (-60, 55), (-55, 47), (-60, 44), (-70, 42), (-75, 35),
     (-80, 26), (-84, 30), (-90, 21), (-97, 16), (-105, 20), (-110, 24), (-115, 29),
     (-120, 34), (-125, 40), (-124, 48), (-130, 55), (-140, 60), (-150, 59),
     (-158, 58), (-165, 60), (-168, 66)],
    [(-80, 9), (-77, 4), (-80, -3), (-81, -6), (-77, -12), (-72, -18), (-70, -23),
     (-65, -30), (-62, -35), (-65, -41), (-68, -48), (-69, -54), (-66, -50),
     (-62, -42), (-58, -35), (-52, -32), (-48, -27), (-41, -23), (-39, -15),
     (-35, -8), (-38, -4), (-44, -2), (-50, 0), (-55, 5), (-60, 8), (-65, 10),
     (-72, 11), (-77, 8), (-80, 9)],
    [(-17, 15), (-16, 20), (-10, 30), (-5, 35), (0, 36), (10, 37), (15, 32),
     (20, 32), (25, 32), (30, 31), (32, 31), (35, 28), (37, 22), (39, 18),
     (43, 12), (48, 11), (51, 11), (48, 5), (44, 0), (41, -5), (40, -10),
     (38, -15), (35, -20), (33, -26), (30, -30), (26, -34), (20, -35), (17, -32),
     (15, -28), (13, -22), (12, -17), (10, -10), (9, -4), (9, 4), (5, 5),
     (0, 6), (-5, 5), (-8, 4), (-12, 8), (-15, 11), (-17, 15)],
    [(-10, 36), (-9, 38), (-9, 43), (-4, 44), (-2, 47), (-1, 49), (0, 51),
     (2, 51), (4, 53), (7, 54), (8, 57), (10, 59), (12, 56), (18, 56),
     (21, 55), (24, 58), (24, 60), (28, 60), (30, 62), (35, 65), (40, 68),
     (50, 69), (60, 69), (68, 73), (75, 72), (85, 75), (95, 76), (105, 77),
     (115, 74), (125, 73), (135, 72), (145, 72), (155, 70), (162, 68), (170, 67),
     (178, 65), (170, 60), (162, 56), (158, 52), (156, 51), (150, 59), (142, 55),
     (140, 50), (135, 44), (132, 43), (128, 38), (126, 35), (122, 32), (120, 28),
     (118, 25), (110, 20), (108, 18), (105, 10), (103, 8), (100, 7), (98, 12),
     (95, 16), (92, 21), (89, 22), (86, 20), (82, 17), (80, 13), (77, 8),
     (76, 10), (74, 15), (72, 20), (70, 22), (66, 25), (62, 25), (58, 25),
     (55, 26), (52, 27), (50, 29), (48, 30), (46, 29), (44, 29), (42, 31),
     (40, 33), (38, 36), (36, 36), (33, 36), (30, 36), (27, 37), (25, 35),
     (23, 36), (20, 38), (18, 40), (15, 38), (12, 38), (10, 37), (8, 38),
     (5, 36), (2, 36), (0, 35), (-3, 35), (-6, 35), (-9, 37), (-10, 36)],
    [(113, -22), (114, -28), (115, -32), (115, -35), (118, -35), (122, -34),
     (126, -32), (130, -32), (132, -32), (135, -35), (138, -35), (140, -38),
     (144, -38), (147, -39), (150, -37), (153, -32), (153, -27), (151, -24),
     (149, -20), (146, -19), (143, -15), (142, -11), (140, -14), (137, -12),
     (135, -12), (132, -12), (130, -13), (127, -14), (124, -15), (121, -17),
     (118, -20), (115, -21), (113, -22)],
    [(-5, 50), (-3, 53), (-5, 56), (-3, 58), (-1, 57), (0, 53), (-1, 51), (-4, 50)],
    [(130, 31), (132, 33), (134, 34), (136, 35), (138, 36), (140, 38), (141, 40),
     (142, 42), (143, 44), (141, 43), (140, 39), (139, 37), (137, 35), (135, 33),
     (133, 34), (131, 33), (130, 31)],
    [(167, -45), (169, -43), (172, -41), (174, -39), (176, -38), (178, -37),
     (176, -39), (174, -41), (172, -43), (169, -46), (167, -45)],
]


def draw_map(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=NAVY_D)
    d.rectangle([x, y, x + w, y + h], outline=(120, 140, 175), width=2)
    for poly in CONTINENTS:
        pts = []
        for lon, lat in poly:
            px = x + (lon + 180.0) / 360.0 * w
            py = y + (90.0 - lat) / 180.0 * h
            pts.append((px, py))
        d.polygon(pts, fill=(188, 172, 138), outline=(140, 128, 100))
    # graticule
    for lon in range(-150, 181, 30):
        gx = x + (lon + 180.0) / 360.0 * w
        d.line([(gx, y), (gx, y + h)], fill=(70, 90, 120), width=1)
    for lat in range(-60, 91, 30):
        gy = y + (90.0 - lat) / 180.0 * h
        d.line([(x, gy), (x + w, gy)], fill=(70, 90, 120), width=1)
    # pins 1-9, 11-13 (r=7; offset pins get a leader line to the true spot)
    for n, (lon, lat, dx, dy) in PINS.items():
        px = x + (lon + 180.0) / 360.0 * w
        py = y + (90.0 - lat) / 180.0 * h
        qx, qy = px + dx, py + dy
        if dx or dy:
            d.line([(px, py), (qx, qy)], fill=(255, 255, 255), width=1)
            d.ellipse([px - 2, py - 2, px + 2, py + 2], fill=(255, 255, 255))
        r = 7
        d.ellipse([qx - r, qy - r, qx + r, qy + r], fill=RED,
                  outline=(255, 255, 255), width=2)
        d.text((qx, qy), str(n), font=sans_b(8), fill=(255, 255, 255),
               anchor="mm")
    # Mercury note
    d.rectangle([x + 8, y + h - 30, x + 190, y + h - 8], fill=RED)
    d.text((x + 14, y + h - 26), "10  Mercury: BepiColombo poised",
           font=sans_b(10), fill=(255, 255, 255))


# ---------------------------------------------------------------- layout
def build():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    mx, cw = 22, W - 44  # margin, content width

    # kicker row
    d.text((mx, 12), "THE WORLD IN ONE DAY", font=sans_b(11), fill=RED)
    rt = "36 STORIES  \u00b7  7 REGIONS  \u00b7  EVERY ONE DATED FRIDAY 20 NOVEMBER 2026"
    d.text((mx + cw - d.textlength(rt, font=sans_b(10)), 13), rt, font=sans_b(10),
           fill=INK)

    # masthead: giant black serif date
    d.text((mx, 28), "Friday 20 November 2026", font=serif_b(40), fill=INK)

    # deck line (italic, 4 top stories)
    y = 80
    y = text_block(d, mx, y,
                   "Russian missiles smash three Kyiv bridges  \u00b7  Cyclone Akvan floods "
                   "India's east coast  \u00b7  An AI sell-off sinks Asia's markets  \u00b7  "
                   "Britain and the EU strike a reset deal",
                   serif_i(15), cw, fill=INK, leading=18)
    hline(d, mx, mx + cw, y + 4, fill=INK, width=2)
    hline(d, mx, mx + cw, y + 8, fill=INK, width=1)
    y += 12

    # stat strip
    bw = (cw - 5 * 4) // 6
    for i, (num, cap) in enumerate(STATS):
        bx = mx + i * (bw + 4)
        d.rectangle([bx, y, bx + bw, y + 44], fill=CARD, outline=(200, 192, 170))
        d.rectangle([bx, y, bx + 4, y + 44], fill=RED)
        d.text((bx + 10, y + 3), num, font=sans_b(23), fill=RED)
        text_block(d, bx + 10, y + 28, cap, sans(9), bw - 16, fill=GREY, leading=10)
    y += 52

    # region bar (counts sum to 36)
    total = sum(c for _, c, _ in REGIONS)
    assert total == 36, total
    x = mx
    for name, count, col in REGIONS:
        seg = int(cw * count / total)
        d.rectangle([x, y, x + seg, y + 16], fill=col)
        short = {"Middle East": "M.East"}.get(name, name)
        lab = f"{short} {count}"
        if d.textlength(lab, font=sans_b(10)) <= seg - 8:
            d.text((x + 5, y + 2), lab, font=sans_b(10), fill=(255, 255, 255))
        else:
            # narrow segment: show just the count, centred
            num = str(count)
            d.text((x + seg / 2 - d.textlength(num, font=sans_b(10)) / 2, y + 2),
                   num, font=sans_b(10), fill=(255, 255, 255))
        x += seg
    y += 22

    # ---- leads: 3 equal columns
    lead_y = y
    lead_h = 296
    lw = (cw - 2 * 10) // 3
    img_h = 140
    for i, lead in enumerate(LEADS):
        lx = mx + i * (lw + 10)
        LEAD_DRAW[lead["n"]](d, lx, lead_y, lw, img_h)
        # red label banner overlapping the top-left of the image
        lab = lead["label"]
        lw_lab = d.textlength(lab, font=sans_b(11)) + 14
        d.rectangle([lx, lead_y, lx + lw_lab, lead_y + 18], fill=RED)
        d.text((lx + 7, lead_y + 3), lab, font=sans_b(11), fill=(255, 255, 255))
        # status chip at the bottom-right of the image
        chip = lead["chip"]
        cw_chip = d.textlength(chip, font=sans_b(9)) + 12
        d.rectangle([lx + lw - cw_chip, lead_y + img_h - 18,
                     lx + lw, lead_y + img_h], fill=(10, 20, 40))
        d.text((lx + lw - cw_chip + 6, lead_y + img_h - 15), chip,
               font=sans_b(9), fill=(255, 255, 255))
        ty = lead_y + img_h + 8
        d.text((lx, ty), f"{lead['n']}  {lead['tag']}", font=sans_b(10), fill=RED)
        ty += 15
        ty = text_block(d, lx, ty, lead["head"], serif_b(18), lw, leading=21)
        ty = text_block(d, lx, ty + 2, lead["body"], sans(11), lw, leading=13)
        d.text((lx, ty + 2), "(" + lead["src"] + ")", font=serif_i(9), fill=GREY)
    y = lead_y + lead_h + 6

    # ---- small stories: 2 rows x 5, each with a drawn mini-scene
    cw5 = (cw - 4 * 6) // 5
    row_h = 106
    img5 = 50
    for r in range(2):
        for c in range(5):
            s = SMALL[r * 5 + c]
            sx = mx + c * (cw5 + 6)
            sy = y + r * (row_h + 6)
            d.rectangle([sx, sy, sx + cw5, sy + row_h], fill=CARD,
                        outline=(200, 192, 170))
            d.rectangle([sx, sy, sx + cw5, sy + 3], fill=GOLD)
            SCENES[s["scene"]](d, sx + 1, sy + 4, cw5 - 2, img5)
            # red banner label on the mini-scene (top-10 pattern)
            bw = d.textlength(s["ban"], font=sans_b(8)) + 8
            d.rectangle([sx + 1, sy + 4, sx + 1 + bw, sy + 14], fill=RED)
            d.text((sx + 5, sy + 5), s["ban"], font=sans_b(8), fill=(255, 255, 255))
            ty = sy + img5 + 6
            check_w(d, f"{s['n']}  {s['tag']}", sans_b(8), cw5 - 12,
                    f"small {s['n']} tag")
            d.text((sx + 6, ty), f"{s['n']}  {s['tag']}", font=sans_b(8), fill=GREY)
            ty += 11
            # headline must wrap to at most 2 lines
            hl = wrap(d, s["head"], sans_b(11), cw5 - 12)
            if len(hl) > 2:
                print(f"OVERFLOW small {s['n']} head: {len(hl)} lines :: {s['head']}")
            ty = text_block(d, sx + 6, ty, s["head"], sans_b(11), cw5 - 12,
                            leading=12)
            # body + source on one line
            bs = s["body"] + " (" + s["src"] + ")"
            check_w(d, bs, sans(9), cw5 - 12, f"small {s['n']} body+src")
            d.text((sx + 6, ty + 1), bs, font=sans(9), fill=INK)
    y += 2 * row_h + 6 + 6

    # ---- bottom band: map (left) + briefs (right)
    d.text((mx, y), "WHERE IT HAPPENED", font=sans_b(12), fill=INK)
    d.text((mx + 482, y), "ALSO ON FRIDAY 20 NOVEMBER  \u2014  23 MORE STORIES",
           font=sans_b(12), fill=INK)
    y += 18
    band_y = y
    band_h = 162
    map_x, map_w = mx, 470
    draw_map(d, map_x, band_y, map_w, band_h)
    d.text((map_x, band_y + band_h + 4), "Pins 1\u201313 mark the drawn stories.",
           font=sans(9), fill=GREY)
    # briefs in two columns
    bx0 = mx + 482
    col_w = (cw - 482 - 8) // 2
    for idx, (n, place, head, src, region) in enumerate(BRIEFS):
        col = idx // 12
        row = idx % 12
        bx = bx0 + col * (col_w + 8)
        by = band_y + row * 13
        d.text((bx, by), f"{n}", font=sans_b(9), fill=RED)
        line = f"{place} \u2014 {head} ({src})"
        check_w(d, line, sans(9), col_w - 22, f"brief {n}")
        d.text((bx + 22, by), line, font=sans(9), fill=INK)
    y = band_y + band_h + 18

    # ---- date check
    dc_text = ("Left out as Thursday 19 November's news: the World Court's ruling on "
               "Myanmar, the Trump\u2013Xi\u2013Putin declaration in Shenzhen, Tonga's drought "
               "emergency, the migrant boat lost off Senegal, Bukele's third-term filing, "
               "the Houthi strike on Riyadh's PIF Tower, Somalia's UAE envoy order, the "
               "Jepchirchir ban, the \u2018Yalta format\u2019 rejection, the UK\u2013Norway vessels "
               "deal, and Indonesia's asset bill. Anthropic's $83-a-share pricing "
               "(Wed 18 Nov) and debut (Thu 19 Nov). Not yet happened: "
               "BepiColombo's Mercury insertion (Sat) and any final COP31 text.")
    dc_lines = wrap(d, dc_text, sans(10), cw - 104)
    dc_h = 8 + len(dc_lines) * 12 + 4
    d.rectangle([mx, y, mx + cw, y + dc_h], outline=RED, width=2)
    d.text((mx + 8, y + 4), "DATE CHECK", font=sans_b(11), fill=RED)
    text_block(d, mx + 96, y + 4, dc_text, sans(10), cw - 104, leading=12)
    y += dc_h + 8

    # ---- footer
    d.text((mx, y), "Every story here happened, or was first reported, on Friday 20 November 2026. "
                    "Sources named beside each story  \u00b7  original drawings",
           font=sans(9), fill=GREY)
    d.text((mx, y + 11), "CONFIRMED = reported by the named source.  CLAIM = one side's account.  "
                         "Officials' counts are attributed.",
           font=sans(9), fill=GREY)
    y += 24
    print("final y:", y, "(page height 1024)")
    return img


if __name__ == "__main__":
    image = build()
    image.save("entry.png", optimize=True)
    import os
    print("saved entry.png", image.size, os.path.getsize("entry.png"), "bytes")
