"""Generates isometric (3D-look) SVG markup for the role illustrations."""
OX, OY, SC = 160, 136, 1.12
def P(x, y, z):
    return (round(OX + (x - y) * 0.866 * SC, 1), round(OY + ((x + y) * 0.5 - z) * SC, 1))
def fmt(p):
    return f"{p[0]:g} {p[1]:g}"

W = ['#FFFFFF', '#E3E8F0', '#C8D0DD']
B = ['#4A78C9', '#1F4FA3', '#163B7A']
K = ['#33465F', '#1A2A42', '#0F1E33']
O = ['#F6B07A', '#E8833A', '#C46A26']
S = ['#FBFAF6', '#E7E3DA', '#D2CCBF']
G = ['#4BAA74', '#1F7A4D', '#17603C']
D = ['#F0E7D6', '#DCCFB5', '#C9B998']
WD = ['#DDB07A', '#BF8A52', '#9E6E3B']
LB = ['#DCE7F8', '#BCD0F0', '#9DB8E6']
SKIN = '#B9825A'
EDGE = 'stroke="#0F1E33" stroke-opacity=".18" stroke-width=".6" stroke-linejoin="round"'

class Scene:
    def __init__(self):
        self.out = []
    def poly(self, pts, fill, edge=True):
        d = 'M' + ' L'.join(fmt(P(*p)) for p in pts) + 'Z'
        self.out.append(f'<path d="{d}" fill="{fill}"{(" " + EDGE) if edge else ""}></path>')
    def box(self, x, y, z, w, d, h, m):
        self.poly([(x, y + d, z), (x + w, y + d, z), (x + w, y + d, z + h), (x, y + d, z + h)], m[2])
        self.poly([(x + w, y, z), (x + w, y + d, z), (x + w, y + d, z + h), (x + w, y, z + h)], m[1])
        self.poly([(x, y, z + h), (x + w, y, z + h), (x + w, y + d, z + h), (x, y + d, z + h)], m[0])
    def rectL(self, x1, x2, y, z1, z2, fill):
        self.poly([(x1, y, z1), (x2, y, z1), (x2, y, z2), (x1, y, z2)], fill, False)
    def rectR(self, x, y1, y2, z1, z2, fill):
        self.poly([(x, y1, z1), (x, y2, z1), (x, y2, z2), (x, y1, z2)], fill, False)
    def top(self, x1, y1, x2, y2, z, fill):
        self.poly([(x1, y1, z), (x2, y1, z), (x2, y2, z), (x1, y2, z)], fill, False)
    def line(self, a, b, color, w=1.4, op=1):
        self.out.append(f'<path d="M{fmt(P(*a))} L{fmt(P(*b))}" stroke="{color}" stroke-width="{w}" stroke-opacity="{op}" stroke-linecap="round" fill="none"></path>')
    def circle(self, x, y, z, r, fill, stroke=None):
        cx, cy = P(x, y, z)
        s = f' stroke="{stroke}" stroke-width="2"' if stroke else ''
        self.out.append(f'<circle cx="{cx:g}" cy="{cy:g}" r="{r}" fill="{fill}"{s}></circle>')
    def shadow(self, x, y, rx, ry):
        cx, cy = P(x, y, 0)
        self.out.append(f'<ellipse cx="{cx:g}" cy="{cy:g}" rx="{rx}" ry="{ry}" fill="#0F1E33" fill-opacity=".10"></ellipse>')
    def ground(self, m, s=66):
        self.box(-s, -s, -7, 2 * s, 2 * s, 7, m)

def owner():
    s = Scene(); s.ground(D)
    s.box(-42, -46, 0, 72, 64, 44, W)
    for y in range(-46, 18, 10):
        s.box(27, y + 2, 44, 3, 5, 6, W)
    for x in range(-42, 30, 10):
        s.box(x + 2, 15, 44, 5, 3, 6, W)
    s.top(-12, 18, 4, 58, .3, S[2])
    s.rectL(-12, 4, 18, 0, 26, B[1])
    s.rectL(-10, 2, 18, 22, 26, B[0])
    for x1 in (-34, 14):
        s.rectL(x1, x1 + 8, 18, 24, 35, K[2])
        s.poly([(x1, 18, 37), (x1 + 8, 18, 37), (x1 + 4, 18, 42)], K[2], False)
    for y1 in (-36, -6):
        s.rectR(30, y1, y1 + 8, 24, 35, K[1])
    s.shadow(-52, 44, 12, 5)
    s.box(-54, 42, 0, 4, 4, 42, WD)
    for dx, dz, r in ((-6, 44, 11), (7, 46, 11), (0, 52, 10)):
        s.circle(-52 + dx * .8, 44 - dx * .8, dz, r, G[1] if r == 10 else G[0])
    s.shadow(31, 50, 9, 4)
    s.box(27, 46, 0, 9, 8, 24, W)
    s.circle(31.5, 50, 31.5, 6.6, '#FFFFFF', None)
    s.circle(31.5, 50, 29, 5, SKIN)
    s.line((27.5, 50, 33), (35.5, 50, 33), K[2], 2)
    s.circle(39, 50, 14, 3.2, 'none', O[1])
    s.line((39, 52, 10.5), (39, 56, 6), O[1], 2.2)
    return s.out

def office():
    s = Scene(); s.ground(S)
    s.box(-58, -46, 0, 116, 90, 2, B)
    L = lambda a, b, w=1.6, op=1: s.line((a[0], a[1], 2.1), (b[0], b[1], 2.1), '#FFFFFF', w, op)
    for a, b in (((-48, -36), (48, -36)), ((48, -36), (48, 34)), ((48, 34), (-48, 34)), ((-48, 34), (-48, -36)),
                 ((-6, -36), (-6, 6)), ((-48, 0), (-22, 0)), ((14, 10), (14, 34)), ((14, 10), (48, 10))):
        L(a, b, 2)
    L((-48, -41), (48, -41), 1, .6)
    for xx in (-48, 48):
        L((xx, -43), (xx, -39), 1, .6)
    for i in range(-40, 41, 16):
        L((i, -36), (i, 34), .6, .18)
    s.poly([(-44, 8, 2.3), (-20, 8, 2.3), (-44, 30, 2.3)], O[0], False)
    s.poly([(-40, 13, 2.4), (-28, 13, 2.4), (-40, 24, 2.4)], B[1], False)
    s.shadow(24, -18, 22, 9)
    s.box(12, -30, 2, 26, 22, 24, W)
    s.box(12, -30, 26, 26, 22, 3, O)
    s.rectL(17, 23, -8, 8, 18, K[2]); s.rectL(27, 33, -8, 8, 18, K[2])
    s.rectR(38, -26, -20, 10, 18, K[1])
    s.box(-36, 38, 2, 44, 3, 3, O)
    s.poly([(8, 38, 2), (8, 41, 2), (13, 39.5, 3.5)], K[2], False)
    s.box(22, 50, 0, 36, 7, 7, W)
    s.box(26, 58, 0, 30, 7, 7, LB)
    return s.out

def contractor():
    s = Scene(); s.ground(D)
    s.box(-54, -54, 0, 62, 52, 3, S)
    cols = [(-54, -54), (4, -54), (-54, -6), (4, -6)]
    for (x, y) in cols:
        s.box(x, y, 3, 4, 4, 28, S)
    s.box(-54, -54, 31, 62, 52, 3, S)
    for (x, y) in cols[:3]:
        s.box(x, y, 34, 4, 4, 22, S)
    s.box(-54, -54, 56, 30, 52, 3, S)
    for z in (40, 46, 52):
        s.line((-50, -2, z), (4, -2, z), O[1], 1, .7)
    s.shadow(42, -38, 8, 4)
    s.box(38, -42, 0, 7, 7, 74, O)
    for z in range(6, 74, 8):
        s.line((38, -35, z), (45, -35, z + 8), O[2], .8)
    s.box(-34, -41, 74, 92, 5, 5, O)
    s.box(46, -42, 70, 12, 7, 8, K)
    s.line((-14, -38.5, 74), (-14, -38.5, 44), K[2], 1)
    s.box(-28, -41, 40, 28, 5, 4, K)
    s.shadow(-22, 40, 12, 5)
    s.box(-32, 34, 0, 18, 12, 10, O)
    for z in (3.3, 6.6):
        s.line((-32, 46, z), (-14, 46, z), O[2], .8)
    s.box(-8, 40, 0, 10, 8, 6, W)
    s.shadow(24, 44, 7, 3)
    s.box(20, 40, 0, 9, 8, 19, O)
    s.rectL(20, 29, 48, 9, 11, '#FFFFFF')
    s.circle(24.5, 44, 24, 4.6, SKIN)
    s.circle(24.5, 44, 27, 4.8, O[1])
    s.line((19.5, 44, 26), (29.5, 44, 26), O[2], 2)
    return s.out

def developer():
    s = Scene(); s.ground(S)
    for i in range(20, 62, 10):
        s.line((i, 22, .1), (i, 62, .1), B[1], .8, .5)
    for j in range(22, 63, 10):
        s.line((20, j, .1), (60, j, .1), B[1], .8, .5)
    s.top(30, 32, 40, 42, .2, O[0])
    def tower(x, y, w, d, h, m, win):
        s.shadow(x + w, y + d, w * .7, w * .3)
        s.box(x, y, 0, w, d, h, m)
        for z in range(10, h - 4, 9):
            s.line((x + 3, y + d, z), (x + w - 3, y + d, z), win, 2, .9)
            s.line((x + w, y + 3, z), (x + w, y + d - 3, z), win, 2, .9)
    tower(-56, -56, 24, 24, 58, W, B[0])
    tower(-22, -58, 26, 26, 78, B, '#FFFFFF')
    tower(-56, -18, 24, 24, 42, K, O[0])
    tower(28, -44, 20, 20, 32, O, '#FFFFFF')
    tower(-12, -14, 28, 28, 52, W, B[1])
    s.line((-9, -45, 78), (-9, -45, 92), K[2], 1.4)
    s.circle(-9, -45, 93, 2.6, O[1])
    return s.out

def furnish():
    s = Scene(); s.ground(WD)
    s.box(-66, -66, 0, 132, 4, 50, S)
    s.box(-66, -66, 0, 4, 132, 50, S)
    s.rectL(-22, 22, -62, 20, 42, '#FFFFFF')
    s.rectL(-19, 19, -62, 23, 39, B[0])
    s.poly([(-19, -62, 23), (-6, -62, 33), (4, -62, 27), (19, -62, 36), (19, -62, 23)], B[2], False)
    s.rectR(-62, -30, 2, 16, 40, LB[0])
    s.line((-62, -14, 16), (-62, -14, 40), '#FFFFFF', 1.5)
    s.top(-36, -24, 36, 44, .2, '#F4C9A3')
    s.top(-30, -18, 30, 38, .3, '#F6B07A')
    s.box(-42, -62, 8, 72, 6, 16, B)
    s.box(-46, -60, 0, 6, 26, 16, B)
    s.box(-40, -56, 0, 70, 22, 9, B)
    s.box(-36, -55, 9, 32, 18, 4, LB)
    s.box(-2, -55, 9, 32, 18, 4, LB)
    s.box(30, -60, 0, 6, 26, 16, B)
    s.shadow(46, -48, 6, 3)
    s.box(45, -50, 0, 2, 2, 40, K)
    s.box(40, -55, 38, 12, 12, 10, O)
    s.shadow(0, 12, 18, 7)
    s.box(-16, 0, 0, 32, 18, 9, WD)
    s.box(-6, 4, 9, 8, 8, 4, W)
    s.shadow(48, 34, 9, 4)
    s.box(42, 28, 0, 12, 12, 10, W)
    for dx, dz, r, c in ((0, 22, 10, G[0]), (-5, 28, 8, G[1]), (5, 30, 7, G[0])):
        s.circle(48 + dx, 34 - dx, dz, r, c)
    return s.out


def finance():
    s = Scene(); s.ground(S)
    s.shadow(-6, -6, 46, 18)
    s.box(-46, -44, 0, 70, 56, 5, W)
    s.box(-42, -40, 5, 62, 48, 4, W)
    s.box(-38, -36, 9, 54, 40, 3, B)
    for x in (-34, -20, -6, 8):
        s.box(x, 0, 12, 5, 5, 26, W)
    for y in (-30, -16):
        s.box(12, y, 12, 5, 5, 26, W)
    s.box(-40, -38, 38, 58, 44, 5, B)
    s.poly([(-40, 6, 43), (18, 6, 43), (-11, 6, 58)], W[1])
    s.poly([(-34, 6, 45), (12, 6, 45), (-11, 6, 54)], B[0], False)
    s.poly([(18, -38, 43), (18, 6, 43), (-11, 6, 58), (-11, -38, 58)], B[1])
    s.shadow(36, 40, 16, 6)
    s.box(22, 30, 0, 30, 22, 1.5, W)
    for i, w in ((0, 22), (5, 22), (10, 14)):
        s.line((26, 35 + i, 1.6), (26 + w, 35 + i, 1.6), K[1], 1.2, .55)
    s.line((40, 49, 1.6), (48, 49, 1.6), O[1], 2)
    s.shadow(-40, 42, 9, 4)
    for z in range(0, 15, 3):
        s.box(-46, 36, z, 11, 11, 2.6, O)
    return s.out

import sys
scenes = {'owner': owner, 'office': office, 'contractor': contractor, 'developer': developer, 'furnish': furnish, 'finance': finance}
for k, f in scenes.items():
    out = f()
    open(sys.argv[1] + f'/{k}.svgfrag', 'w').write('\n'.join(out))
    print(k, len(out), sum(len(x) for x in out))
