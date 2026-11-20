#!/usr/bin/env python3
"""Build the news-image entry: one 1024x1024 newspaper page summing up
Friday 20 November 2026 world news. Deterministic, no network, PIL only.
Run:  python3 make_image.py   -> writes entry.png (1024x1024, <=1 MiB).

Design (our own): a dark navy masthead band with the date, an asymmetric
lead layout (one big Kyiv lead left, Cyclone + AI sell-off stacked right),
ten small cards, a world map with numbered pins on the RIGHT and the briefs
list on the LEFT, a DATE CHECK box, and a source footer. All text, figures
and drawings are our own; the stories are the day's reported facts, each
attributed to its source, with Thursday's news explicitly left out.
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


# ---------------------------------------------------------------- data
# 36 stories. Fields: n, place, field, headline, body, source, region, pin.
LEADS = [
    dict(n=1, tag="KYIV, UKRAINE · WAR", head="Russian missiles hit three Kyiv bridges",
         body="An overnight barrage of about 110 missiles and 400 drones killed at least "
              "eight people across Ukraine and cut power and water in the capital. Three "
              "bridges over the Dnipro were damaged, and the grid operator called the "
              "situation extremely critical.",
         src="Kyiv Independent, BBC", region="Europe", pin=(30.5, 50.4)),
    dict(n=2, tag="ODISHA, INDIA · CYCLONE", head="Cyclone Akvan comes ashore in eastern India",
         body="The storm crossed the coast near Gopalpur from about 8 am, after more than "
              "300,000 people were moved to shelters. Winds reached 90 to 100 km/h; no "
              "deaths were reported, and schools shut across the coast.",
         src="IMD, Deccan Herald", region="Asia", pin=(85.2, 19.3)),
    dict(n=3, tag="TOKYO · SEOUL · TAIPEI · MARKETS", head="AI sell-off sinks Asia's stock markets",
         body="Taiwan's index fell 6.2% to end its worst week since 1991. Seoul lost 5.2% "
              "and Tokyo 5.1% as chipmakers led the slide, after Wall Street fell 2% the "
              "day before. SoftBank dropped more than 14%.",
         src="Al Jazeera, Anadolu", region="Asia", pin=(139.7, 35.7)),
]

SMALL = [
    dict(n=4, tag="BRUSSELS · DIPLOMACY", head="UK and EU seal a \u201creset\u201d deal",
         body="Food trade, youth visas, carbon.", src="Reuters", region="Europe"),
    dict(n=5, tag="ANTALYA · CLIMATE", head="COP31 reaches its last day with no deal",
         body="Draft leaves out fossil fuels.", src="UN News", region="Europe"),
    dict(n=6, tag="EASTERN POLAND · SECURITY", head="Russian cruise missile lands in Poland",
         body="Fell in a field; airports paused.", src="Reuters", region="Europe"),
    dict(n=7, tag="CENTRAL IRAQ · SECURITY", head="Iraqi army enters a militia stronghold",
         body="Troops deploy to Jurf al-Sakhar.", src="Reuters", region="Middle East"),
    dict(n=8, tag="ITALY · LABOUR", head="General strike over Italy's budget",
         body="Workers and students march.", src="Reuters", region="Europe"),
    dict(n=9, tag="TOKYO · ECONOMY", head="Japan's inflation picks up to 2.3%",
         body="December rate rise in view.", src="Reuters", region="Asia"),
    dict(n=10, tag="MERCURY · SPACE", head="BepiColombo reaches Mercury",
         body="Probe ends a 6bn-mile trip.", src="ESA, BBC", region="Global"),
    dict(n=11, tag="TURKANA, KENYA · ENERGY", head="Kenya starts drilling its first oil",
         body="First crude is due on 1 December.", src="allAfrica", region="Africa"),
    dict(n=12, tag="SAN SALVADOR · POLITICS", head="Bukele files to run for a third term",
         body="The vote is on 28 February 2027.", src="AP", region="Americas"),
    dict(n=13, tag="WELLINGTON · CRICKET", head="Phillips hits 118 against India",
         body="Hundreds in all three formats.", src="ICC", region="Oceania"),
]

BRIEFS = [
    (14, "Seoul", "Ruling party to impeach top judge", "Korea Herald", "Asia"),
    (15, "Riyadh", "Houthi missile hits PIF Tower", "Reuters", "Middle East"),
    (16, "Hormuz", "Tankers burn as Brent nears $92.50", "Reuters", "Middle East"),
    (17, "California", "Magnitude 5.0 quake near Pinnacles; no injuries", "AP", "Americas"),
    (18, "Europe", "Cost-of-living strike in 25 countries", "Al Jazeera", "Europe"),
    (19, "Colombo", "Sri Lanka raises its rate to 9%", "Reuters", "Asia"),
    (20, "Mogadishu", "Somalia gives UAE envoy 72 hours to leave", "AFP", "Africa"),
    (21, "Nairobi", "Marathon champion Jepchirchir banned 3 years", "AP", "Africa"),
    (22, "Florida", "St. Johns River floods; Kyle nears", "AP", "Americas"),
    (23, "Sudan", "Drone strike hits a gold mine", "Reuters", "Africa"),
    (24, "Gaza", "Israeli ground operation in central Gaza", "Reuters", "Middle East"),
    (25, "Beijing", "China holds loan rates for an 18th month", "Xinhua", "Asia"),
    (26, "Seoul", "First cholera case in a decade", "Korea Herald", "Asia"),
    (27, "Blantyre", "Malawi fuel crisis, night queues", "Al Jazeera", "Africa"),
    (28, "Cox's Bazar", "Rohingya pray after ICJ ruling", "Al Jazeera", "Asia"),
    (29, "Shenzhen", "Xi hails turnaround in Australia ties", "CGTN", "Asia"),
    (30, "Las Vegas", "Russell fastest in wet practice", "Formula1.com", "Americas"),
    (31, "Addis Ababa", "Ethiopia and Eritrea trade shelling", "Reuters", "Africa"),
    (32, "Paris", "Europe rejects a \u2018Yalta format\u2019 for talks", "Reuters", "Europe"),
    (33, "Canberra", "$100m for Ukrainian vessels", "BBC", "Oceania"),
    (34, "Jakarta", "Indonesia passes asset-forfeiture bill", "Reuters", "Asia"),
    (35, "Turin", "ATP Finals group stage ends; semis Saturday", "ATP", "Europe"),
    (36, "Wellington", "Nicholls scores 175 in 216-run stand", "ICC", "Oceania"),
]

STATS = [
    ("3", "bridges hit in Kyiv"),
    ("300,000+", "people moved to shelters"),
    ("\u22125.1%", "Nikkei, Friday's close"),
    ("118", "Phillips' century against India"),
    ("2.3%", "Japan inflation, October"),
    ("$92.50", "Brent crude, Hormuz shut"),
]

REGIONS = [("Europe", 8, (31, 58, 95)), ("Asia", 10, (163, 22, 33)),
           ("Middle East", 4, (161, 98, 7)), ("Africa", 6, (14, 107, 107)),
           ("Americas", 4, (107, 33, 168)), ("Oceania", 3, (46, 125, 50)),
           ("Global", 1, (96, 94, 88))]


# ---------------------------------------------------------------- pictures
def draw_kyiv(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=SKY)
    for sx, sy in [(12, 18), (40, 8), (78, 24), (120, 10), (160, 20), (200, 8),
                   (240, 16), (280, 6), (60, 34), (180, 30), (260, 28)]:
        d.ellipse([x + sx - 1, y + sy - 1, x + sx + 1, y + sy + 1], fill=(220, 220, 200))
    # building silhouettes
    for bx, bw, bh in [(0, 46, 62), (52, 34, 84), (92, 52, 58), (150, 38, 92),
                       (194, 44, 66), (244, 52, 78), (302, 40, 60)]:
        d.rectangle([x + bx, y + h - bh, x + bx + bw, y + h], fill=(10, 20, 40))
        for wy in range(y + h - bh + 8, y + h - 6, 12):
            for wx in range(x + bx + 6, x + bx + bw - 4, 12):
                if (wx + wy) % 3 == 0:
                    d.rectangle([wx, wy, wx + 4, wy + 5], fill=(255, 214, 120))
    # missile arcs (dashed) + fire glows
    for (ax, ay, bx, by) in [(20, 8, 120, 78), (150, 4, 250, 84), (280, 12, 330, 70)]:
        for t in [i / 14 for i in range(15)]:
            px = ax + (bx - ax) * t
            py = ay + (by - ay) * t - 26 * math.sin(math.pi * t)
            d.ellipse([x + px - 1.5, y + py - 1.5, x + px + 1.5, y + py + 1.5],
                      fill=(255, 230, 150))
    for fx, fy in [(120, 82), (250, 88), (330, 74)]:
        d.ellipse([x + fx - 7, y + fy - 7, x + fx + 7, y + fy + 7], fill=(255, 140, 40))
        d.ellipse([x + fx - 3, y + fy - 3, x + fx + 3, y + fy + 3], fill=(255, 220, 120))
    # bridge across the bottom
    d.rectangle([x, y + h - 12, x + w, y + h - 8], fill=(30, 30, 34))
    for px in range(x + 8, x + w - 8, 26):
        d.line([(px, y + h - 8), (px, y + h - 26)], fill=(30, 30, 34), width=3)
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
    d.text((x + 8, y + h - 17), "LANDFALL  ·  8 AM", font=sans_b(11), fill=(255, 255, 255))


def draw_market(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(18, 20, 26))
    for gy in range(y + 14, y + h - 8, 22):
        d.line([(x + 6, gy), (x + w - 6, gy)], fill=(48, 52, 60), width=1)
    pts = [(x + 10, y + 22), (x + 60, y + 34), (x + 110, y + 30), (x + 160, y + 58),
           (x + 210, y + 52), (x + 260, y + 82), (x + 310, y + 96), (x + w - 10, y + h - 14)]
    d.line(pts, fill=(220, 60, 60), width=4)
    for px, py in pts[1:-1]:
        d.ellipse([px - 3, py - 3, px + 3, py + 3], fill=(255, 120, 120))
    d.text((x + 10, y + h - 18), "TAIPEI \u22126.2%  ·  SEOUL \u22125.2%",
           font=sans_b(10), fill=(255, 255, 255))


def icon(d, x, y, w, h, kind):
    """Small flat icon for a small story. kind selects the drawing."""
    d.rectangle([x, y, x + w, y + h], fill=LIGHT)
    if kind == "flags":  # UK + EU
        d.rectangle([x + 8, y + 10, x + w // 2 - 4, y + h - 10], fill=(28, 52, 120))
        d.rectangle([x + 8, y + h // 2 - 3, x + w // 2 - 4, y + h // 2 + 3], fill=(255, 255, 255))
        d.rectangle([x + w // 4 - 3, y + 10, x + w // 4 + 3, y + h - 10], fill=(255, 255, 255))
        cx, cy = x + 3 * w // 4, y + h // 2
        for k in range(8):
            a = k * math.pi / 4
            d.ellipse([cx + 12 * math.cos(a) - 2, cy + 12 * math.sin(a) - 2,
                       cx + 12 * math.cos(a) + 2, cy + 12 * math.sin(a) + 2],
                      fill=(255, 210, 0))
    elif kind == "globe":
        d.ellipse([x + w // 2 - 20, y + 6, x + w // 2 + 20, y + h - 6], fill=(46, 125, 70))
        d.ellipse([x + w // 2 - 12, y + 12, x + w // 2 + 2, y + 26], fill=(120, 190, 220))
        d.ellipse([x + w // 2 + 2, y + 30, x + w // 2 + 16, y + 44], fill=(120, 190, 220))
        d.rectangle([x + w - 16, y + 6, x + w - 10, y + h - 6], fill=RED)
        d.ellipse([x + w - 19, y + 4, x + w - 7, y + 16], fill=RED)
    elif kind == "missile":
        d.polygon([(x + 14, y + h - 10), (x + w // 2, y + 8), (x + w - 14, y + h - 10)],
                  fill=(120, 120, 120))
        d.polygon([(x + w // 2 - 4, y + 8), (x + w // 2 + 4, y + 8), (x + w // 2, y + 22)],
                  fill=RED)
        d.ellipse([x + w // 2 - 5, y + h - 18, x + w // 2 + 5, y + h - 8], fill=(255, 140, 40))
        d.line([(x + 8, y + h - 6), (x + w - 8, y + h - 6)], fill=(60, 120, 60), width=4)
    elif kind == "fort":
        d.rectangle([x + 14, y + 22, x + w - 14, y + h - 10], fill=(150, 120, 80))
        d.rectangle([x + 10, y + 14, x + 22, y + 26], fill=(150, 120, 80))
        d.rectangle([x + w - 22, y + 14, x + w - 10, y + 26], fill=(150, 120, 80))
        d.rectangle([x + w // 2 - 8, y + h - 26, x + w // 2 + 8, y + h - 10], fill=(60, 40, 20))
        d.line([(x + w // 2, y + 6), (x + w // 2, y + 16)], fill=INK, width=2)
        d.polygon([(x + w // 2, y + 6), (x + w // 2 + 14, y + 10), (x + w // 2, y + 14)], fill=RED)
    elif kind == "crowd":
        for i, (cx, cy) in enumerate([(10, 16), (24, 12), (38, 18), (16, 32), (30, 34), (44, 30)]):
            d.ellipse([x + cx - 4, y + cy - 4, x + cx + 4, y + cy + 4], fill=INK if i % 2 else RED)
            d.polygon([(x + cx - 5, y + cy + 12), (x + cx + 5, y + cy + 12), (x + cx, y + cy + 3)],
                      fill=INK if i % 2 else RED)
    elif kind == "chart":
        for i, bh in enumerate([12, 16, 13, 20, 26]):
            bx = x + 6 + i * 9
            d.rectangle([bx, y + h - 8 - bh, bx + 6, y + h - 8], fill=TEAL if i < 4 else RED)
        d.text((x + 6, y + 4), "+2.3%", font=sans_b(11), fill=RED)
    elif kind == "planet":
        d.ellipse([x + 6, y + 6, x + 30, y + 30], fill=(150, 140, 130))
        d.ellipse([x + 12, y + 12, x + 18, y + 18], fill=(110, 100, 90))
        d.ellipse([x + 20, y + 20, x + 26, y + 26], fill=(110, 100, 90))
        d.rectangle([x + 36, y + 14, x + 48, y + 22], fill=(90, 140, 200))
        d.rectangle([x + 32, y + 10, x + 36, y + 26], fill=(200, 200, 200))
        d.line([(x + 42, y + 22), (x + 46, y + 34)], fill=(200, 200, 200), width=2)
    elif kind == "derrick":
        d.polygon([(x + 14, y + h - 8), (x + w // 2 - 4, y + 10), (x + w // 2 + 4, y + 10),
                   (x + w - 14, y + h - 8)], outline=INK, width=3)
        d.line([(x + w // 2, y + 10), (x + w - 20, y + 26)], fill=INK, width=3)
        d.line([(x + 14, y + h - 8), (x + w - 14, y + h - 8)], fill=INK, width=3)
        d.ellipse([x + w - 26, y + 20, x + w - 14, y + 32], fill=(20, 20, 20))
    elif kind == "ballot":
        d.rectangle([x + 16, y + 22, x + w - 16, y + h - 8], fill=(60, 90, 160))
        d.rectangle([x + w // 2 - 12, y + 14, x + w // 2 + 12, y + 22], fill=(40, 60, 120))
        d.line([(x + w // 2 - 8, y + h - 20), (x + w // 2 - 2, y + h - 12),
                (x + w // 2 + 10, y + h - 28)], fill=(255, 255, 255), width=3)
    elif kind == "bat":
        d.rectangle([x + 14, y + 12, x + 26, y + h - 12], fill=(190, 150, 90))
        d.rectangle([x + 18, y + 6, x + 22, y + 14], fill=(120, 90, 50))
        d.ellipse([x + w - 24, y + h - 24, x + w - 12, y + h - 12], fill=RED)
        d.text((x + w - 40, y + 8), "118", font=sans_b(14), fill=RED)


ICON_KIND = {4: "flags", 5: "globe", 6: "missile", 7: "fort", 8: "crowd",
             9: "chart", 10: "planet", 11: "derrick", 12: "ballot", 13: "bat"}

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

PINS = {1: (30.5, 50.4), 2: (85.2, 19.3), 3: (139.7, 35.7), 4: (4.4, 50.8),
        5: (30.7, 36.9), 6: (19.4, 51.8), 7: (44.4, 32.9), 8: (12.5, 41.9),
        9: (139.7, 35.7), 10: (0, 0), 11: (36.1, 3.3), 12: (-89.2, 13.7),
        13: (174.8, -41.3)}
# pin 10 (Mercury) is off-planet: drawn in the corner box instead.


def draw_map(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(214, 205, 180))
    d.rectangle([x, y, x + w, y + h], outline=INK, width=2)
    for poly in CONTINENTS:
        pts = []
        for lon, lat in poly:
            px = x + (lon + 180.0) / 360.0 * w
            py = y + (90.0 - lat) / 180.0 * h
            pts.append((px, py))
        d.polygon(pts, fill=(168, 152, 110), outline=(90, 80, 60))
    # graticule
    for lon in range(-150, 181, 30):
        gx = x + (lon + 180.0) / 360.0 * w
        d.line([(gx, y), (gx, y + h)], fill=(190, 180, 155), width=1)
    for lat in range(-60, 91, 30):
        gy = y + (90.0 - lat) / 180.0 * h
        d.line([(x, gy), (x + w, gy)], fill=(190, 180, 155), width=1)
    # pins 1-9, 11-13
    for n, (lon, lat) in PINS.items():
        if n == 10:
            continue
        px = x + (lon + 180.0) / 360.0 * w
        py = y + (90.0 - lat) / 180.0 * h
        r = 8
        d.ellipse([px - r, py - r, px + r, py + r], fill=RED, outline=(255, 255, 255), width=2)
        d.text((px - 2.5 if n < 10 else px - 5, py - 5), str(n), font=sans_b(9),
               fill=(255, 255, 255))
    # Mercury note
    d.rectangle([x + 8, y + h - 30, x + 168, y + h - 8], fill=NAVY)
    d.text((x + 14, y + h - 26), "10  Mercury: BepiColombo", font=sans_b(10),
           fill=(255, 255, 255))


# ---------------------------------------------------------------- layout
def build():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    mx, cw = 22, W - 44  # margin, content width

    # masthead band
    d.rectangle([mx, 14, mx + cw, 104], fill=NAVY)
    d.rectangle([mx, 14, mx + cw, 104], outline=NAVY_D, width=2)
    d.text((mx + 16, 26), "Friday 20 November 2026", font=serif_b(44), fill=(255, 255, 255))
    d.text((mx + 16, 76), "THE WORLD, IN ONE PAGE", font=sans_b(13), fill=(255, 210, 120))
    rx = mx + cw - 16
    d.text((rx - d.textlength("36 STORIES  ·  7 REGIONS", font=sans_b(13)), 30),
           "36 STORIES  ·  7 REGIONS", font=sans_b(13), fill=(255, 255, 255))
    d.text((rx - d.textlength("EVERY ONE FRIDAY", font=sans(11)), 52),
           "EVERY ONE FRIDAY", font=sans(11), fill=(210, 220, 235))
    d.text((rx - d.textlength("ONE DAY'S NEWS", font=sans(11)), 68),
           "ONE DAY'S NEWS", font=sans(11), fill=(210, 220, 235))

    # sub-headline
    y = 112
    y = text_block(d, mx, y,
                   "Russian missiles smash three Kyiv bridges  ·  Cyclone Akvan floods "
                   "India's east coast  ·  An AI sell-off sinks Asia's markets  ·  Britain "
                   "and the EU strike a reset deal",
                   serif_i(17), cw, fill=INK, leading=21)
    hline(d, mx, mx + cw, y + 3, fill=INK, width=2)
    hline(d, mx, mx + cw, y + 7, fill=INK, width=1)
    y += 12

    # stat strip
    bw = (cw - 5 * 4) // 6
    for i, (num, cap) in enumerate(STATS):
        bx = mx + i * (bw + 4)
        d.rectangle([bx, y, bx + bw, y + 46], fill=CARD, outline=(200, 192, 170))
        d.rectangle([bx, y, bx + 4, y + 46], fill=RED)
        d.text((bx + 10, y + 3), num, font=sans_b(23), fill=RED)
        text_block(d, bx + 10, y + 29, cap, sans(9), bw - 16, fill=GREY, leading=10)
    y += 54

    # region bar
    total = sum(c for _, c, _ in REGIONS)
    x = mx
    for name, count, col in REGIONS:
        seg = int(cw * count / total)
        d.rectangle([x, y, x + seg, y + 18], fill=col)
        label = name if count > 1 else "1"
        short = {"Middle East": "M.East"}.get(name, label)
        if seg >= 60:
            d.text((x + 6, y + 3), f"{short} {count}", font=sans_b(10), fill=(255, 255, 255))
        elif count == 1:
            d.text((x + 8, y + 3), "1", font=sans_b(10), fill=(255, 255, 255))
        x += seg
    y += 24
    d.text((mx, y), "Regions:  Global 1 = Mercury (BepiColombo).  Counts are the stories on this page.",
           font=sans(9), fill=GREY)
    y += 18

    # ---- leads: Kyiv big left; Cyclone + AI stacked right
    lead_y = y
    lead_h = 268
    # Kyiv (left, 478 wide)
    kx, kw = mx, 478
    draw_kyiv(d, kx, lead_y, kw, 138)
    ly = lead_y + 146
    d.text((kx, ly), "1  KYIV, UKRAINE · WAR", font=sans_b(11), fill=RED)
    ly += 16
    ly = text_block(d, kx, ly, LEADS[0]["head"], serif_b(21), kw, leading=24)
    ly = text_block(d, kx, ly + 2, LEADS[0]["body"], sans(12), kw, leading=15)
    d.text((kx, ly + 2), "(" + LEADS[0]["src"] + ")", font=serif_i(10), fill=GREY)
    # right column: two horizontal cards
    rx, rw = mx + 490, 490
    card_h = (lead_h - 8) // 2
    for i, lead in enumerate([LEADS[1], LEADS[2]]):
        cy = lead_y + i * (card_h + 8)
        d.rectangle([rx, cy, rx + rw, cy + card_h], fill=CARD, outline=(200, 192, 170))
        if i == 0:
            draw_cyclone(d, rx + 6, cy + 6, 186, card_h - 12)
        else:
            draw_market(d, rx + 6, cy + 6, 186, card_h - 12)
        tx = rx + 200
        d.text((tx, cy + 8), f"{lead['n']}  {lead['tag']}", font=sans_b(10), fill=RED)
        ty = text_block(d, tx, cy + 24, lead["head"], serif_b(17), rw - 208, leading=20)
        ty = text_block(d, tx, ty + 2, lead["body"], sans(11), rw - 208, leading=13)
        d.text((tx, cy + card_h - 16), "(" + lead["src"] + ")", font=serif_i(9), fill=GREY)
    y = lead_y + lead_h + 6

    # ---- small stories: 2 rows x 5
    cw5 = (cw - 4 * 5) // 5
    row_h = 104
    for r in range(2):
        for c in range(5):
            s = SMALL[r * 5 + c]
            sx = mx + c * (cw5 + 5)
            sy = y + r * (row_h + 6)
            d.rectangle([sx, sy, sx + cw5, sy + row_h], fill=CARD, outline=(200, 192, 170))
            d.rectangle([sx, sy, sx + cw5, sy + 3], fill=GOLD)
            icon(d, sx + 6, sy + 8, 52, 42, ICON_KIND[s["n"]])
            d.text((sx + 64, sy + 8), f"{s['n']}", font=sans_b(16), fill=RED)
            d.text((sx + 64, sy + 26), s["tag"], font=sans_b(8), fill=GREY)
            ty = text_block(d, sx + 6, sy + 54, s["head"], sans_b(12), cw5 - 12, leading=13)
            text_block(d, sx + 6, ty + 1, s["body"] + " (" + s["src"] + ")",
                       sans(10), cw5 - 12, leading=12)
    y += 2 * row_h + 6 + 8

    # ---- briefs (left) + map (right)
    d.text((mx, y), "ALSO ON FRIDAY 20 NOVEMBER  \u2014  23 MORE STORIES",
           font=sans_b(12), fill=INK)
    d.text((mx + 640, y), "WHERE IT HAPPENED", font=sans_b(12), fill=INK)
    y += 18
    # briefs in two columns
    col_w = 312
    for idx, (n, place, head, src, region) in enumerate(BRIEFS):
        col = idx // 12
        row = idx % 12
        bx = mx + col * (col_w + 8)
        by = y + row * 14
        d.text((bx, by), f"{n}", font=sans_b(9), fill=RED)
        d.text((bx + 22, by), f"{place} \u2014 {head} ({src})", font=sans(9), fill=INK)
    # map
    map_x, map_w = mx + 640, cw - 640
    draw_map(d, map_x, y, map_w, 150)
    d.text((map_x, y + 154), "Pins 1\u201313 mark the drawn stories.",
           font=sans(9), fill=GREY)
    y += 176

    # ---- date check
    dc_text = ("Left out as Thursday 19 November's news: the World Court's ruling on "
               "Myanmar, the Trump\u2013Xi\u2013Putin declaration in Shenzhen, Tonga's drought "
               "emergency, the migrant boat lost off Senegal, Anthropic's $83bn IPO pricing, "
               "and the $190.4m Van Gogh sale. Not yet happened, so not shown: "
               "BepiColombo's orbit insertion round Mercury and any final COP31 text.")
    dc_lines = wrap(d, dc_text, sans(10), cw - 104)
    dc_h = 8 + len(dc_lines) * 12 + 4
    d.rectangle([mx, y, mx + cw, y + dc_h], outline=RED, width=2)
    d.text((mx + 8, y + 4), "DATE CHECK", font=sans_b(11), fill=RED)
    text_block(d, mx + 96, y + 4, dc_text, sans(10), cw - 104, leading=12)
    y += dc_h + 8

    # ---- footer
    d.text((mx, y), "Every story here happened, or was first reported, on Friday 20 November 2026. "
                    "Officials' counts are attributed.",
           font=sans(9), fill=GREY)
    d.text((mx, y + 12), "Sources named beside each story  ·  original drawings",
           font=sans(9), fill=GREY)
    return img


if __name__ == "__main__":
    image = build()
    image.save("entry.png", optimize=True)
    import os
    print("saved entry.png", image.size, os.path.getsize("entry.png"), "bytes")
