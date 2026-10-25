"""Jumper-wire routing for the teensy-panel ElectroCookie build.

A wire is a polyline of (lane, row[, z]) points in the vertical-board frame: lane is a column letter, a rail name
(B+ B- T+ T-) or an x value in mm from the board centre line; row is the ElectroCookie row (fractions allowed).
Wires lie on the board at Z1 and hop to Z2 where they must cross another wire.  22 AWG solid core with 1.5 mm
sleeving.  Each wire becomes a two-pad footprint (pads share number "1", so KiCad treats the ends as connected)
with a purple tube model and a drawing-layer polyline."""
import math

COLS = {'A': -13.97, 'B': -11.43, 'C': -8.89, 'D': -6.35, 'E': -3.81, 'F': 3.81, 'G': 6.35, 'H': 8.89, 'I': 11.43,
        'J': 13.97, 'B+': -20.32, 'B-': -22.86, 'T+': 20.32, 'T-': 22.86}
L1, L2, L3, L4 = -15.6, -17.2, -18.8, -20.4       # lanes left of column A (L4 runs over the unused B+ holes)
C1, C2, C3 = -2.9, 0.0, 2.9                         # centre-gap lanes
R1, R2 = 15.6, 17.2                                 # lanes right of column J
Z1, Z2 = 0.9, 2.4                                   # wire centre heights: on the board / hopping over another wire
DIA = 1.5

# name, net, path.  Pin map: Teensy left column C1-24 (tap at A/B), right column G1-24 (tap at H/I/J);
# display socket J32-38 (VCC GND SCL SDA DC CS RST, the header order), DAC socket A48-53 (XSMT LRCK DIN BCK 3V3 GND
# top-down), encoder socket J56-60 (GND + SW DT CLK).
WIRES = [
    ('W01', '+3V3', [('J', 3), ('T+', 3)]),
    ('W02', 'GND', [('J', 2), ('T-', 2)]),
    ('W03', '+3V3', [('I', 32), ('I', 31, Z2), ('T+', 31, Z2)]),             # display VCC (J32), hops the R lanes
    ('W04', 'GND', [('G', 33, Z2), ('G', 39, Z2), ('T-', 39, Z2)]),          # display GND (J33), rides over rows 34-38
    ('W05', 'SPI_SCK', [('H', 14), ('H', 34)]),                              # D13 -> SCL (J34), straight down column H
    ('W06', 'SPI_MOSI', [('A', 13), (L1, 13), (L1, 35), ('I', 35)]),          # D11 -> SDA (J35)
    ('W07', 'LCD_DC', [('A', 11), (L3, 11), (L3, 36), (L2 - 1.0, 36, Z2), (L2 + 1.0, 36, Z2), ('I', 36)]),  # D9 -> DC (J36), hops L2
    ('W08', 'LCD_CS', [('A', 12), (L2, 12), (L2, 37), ('I', 37)]),            # D10 -> CS (J37)
    ('W09', 'LCD_RST', [('A', 10), (L4, 10), (L4, 38), ('I', 38)]),           # D8 -> RST (J38)
    ('W10', 'ENC_SW', [('A', 6), (L1, 6, Z2), (L1, 29, Z2), (C3, 29, Z2), (C3, 58, Z2), ('I', 58, Z2)]),    # D4 -> SW (J58)
    ('W11', 'ENC_DT', [('A', 5), (L2, 5, Z2), (L2, 30, Z2), (C2, 30, Z2), (C2, 59, Z2), ('I', 59, Z2)]),    # D3 -> DT (J59)
    ('W12', 'ENC_CLK', [('A', 4), (L3, 4, Z2), (L3, 31, Z2), (C1, 31, Z2), (C1, 60, Z2), ('I', 60, Z2)]),   # D2 -> CLK (J60)
    ('W13', 'I2S_DIN', [('A', 9), ('B', 9), ('B', 34), ('B', 34.6, Z2), ('B', 38.4, Z2), ('B', 39), ('B', 50)]),  # D7 -> DIN (A50), hops rows 35-38
    ('W14', 'I2S_LRCK', [('H', 7), (R1, 7), (R1, 49), ('E', 49)]),            # D20 -> LRCK (A49)
    ('W15', 'I2S_BCK', [('H', 6), (R2, 6), (R2, 51), ('E', 51)]),             # D21 -> BCK (A51)
    ('W16', '+3V3', [('C', 52), (-7.62, 52), (-7.62, 58), ('B+', 58)]),       # DAC 3V3 (A52) from the left + rail
    ('W17', 'GND', [('C', 53), ('C', 57), ('B-', 57)]),                       # DAC GND (A53) to the left - rail
    ('W18', '+3V3', [('D', 48), (-5.5, 48), (-5.5, 52), ('E', 52)]),          # DAC XSMT (A48) tied to its own 3V3 strip
    ('W19', '+3V3', [('H', 57), ('H', 53), ('T+', 53)]),                      # encoder + (J57) from the right + rail
    ('W20', 'GND', [('I', 56), ('I', 54), ('T-', 54)]),                       # encoder GND (J56) to the right - rail
]


def lane_x(lane):
    return COLS[lane] if isinstance(lane, str) else float(lane)


def row_y(row):
    return -78.74 + 2.54 * (row - 1)


def hole_name(lane, row):
    return f'{lane}{int(round(row))}' if isinstance(lane, str) else None


def polyline3d(path):
    """Board-frame points (x, y, z) with the vertical legs into the holes added."""
    pts = []
    for p in path:
        lane, row = p[0], p[1]
        z = p[2] if len(p) > 2 else Z1
        pts.append((lane_x(lane), row_y(row), z))
    first, last = pts[0], pts[-1]
    return [(first[0], first[1], -1.8)] + pts + [(last[0], last[1], -1.8)]


def round_corners(pts, r=1.8, n=5):
    out = [pts[0]]
    for i in range(1, len(pts) - 1):
        p0, p, p2 = pts[i - 1], pts[i], pts[i + 1]
        d1 = [p[k] - p0[k] for k in range(3)]; d2 = [p2[k] - p[k] for k in range(3)]
        l1 = math.sqrt(sum(c * c for c in d1)); l2 = math.sqrt(sum(c * c for c in d2))
        if l1 < 1e-6 or l2 < 1e-6:
            continue
        rr = min(r, l1 / 2, l2 / 2)
        a = [p[k] - d1[k] / l1 * rr for k in range(3)]
        b = [p[k] + d2[k] / l2 * rr for k in range(3)]
        for t in [j / n for j in range(n + 1)]:
            out.append(tuple((1 - t) ** 2 * a[k] + 2 * (1 - t) * t * p[k] + t * t * b[k] for k in range(3)))
    out.append(pts[-1])
    return out


def tube(pts, radius, sides=10):
    """Triangle mesh around a polyline using parallel-transport frames."""
    def sub(a, b): return [a[k] - b[k] for k in range(3)]
    def norm(a):
        l = math.sqrt(sum(c * c for c in a)); return [c / l for c in a] if l > 1e-9 else [0, 0, 1]
    def cross(a, b): return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]
    tangents = []
    for i in range(len(pts)):
        if i == 0: t = sub(pts[1], pts[0])
        elif i == len(pts) - 1: t = sub(pts[-1], pts[-2])
        else: t = [a + b for a, b in zip(norm(sub(pts[i], pts[i - 1])), norm(sub(pts[i + 1], pts[i])))]
        tangents.append(norm(t))
    nrm = norm(cross(tangents[0], [1, 0, 0] if abs(tangents[0][0]) < 0.9 else [0, 1, 0]))
    verts, faces = [], []
    for i, (p, t) in enumerate(zip(pts, tangents)):
        nrm = norm(sub(nrm, [t[k] * sum(nrm[j] * t[j] for j in range(3)) for k in range(3)]))
        bn = cross(t, nrm)
        for s in range(sides):
            a = 2 * math.pi * s / sides
            verts.append(tuple(p[k] + radius * (math.cos(a) * nrm[k] + math.sin(a) * bn[k]) for k in range(3)))
        if i:
            b0, b1 = (i - 1) * sides, i * sides
            for s in range(sides):
                s2 = (s + 1) % sides
                faces.append((b0 + s, b1 + s, b1 + s2)); faces.append((b0 + s, b1 + s2, b0 + s2))
    for base in (0, (len(pts) - 1) * sides):
        for s in range(1, sides - 1):
            faces.append((base, base + s, base + s + 1))
    return verts, faces


def write_wrl(path, verts, faces, colour=(0.45, 0.18, 0.72), scale=1 / 2.54):
    out = ['#VRML V2.0 utf8', 'Shape { appearance Appearance { material Material { diffuseColor %.2f %.2f %.2f } }' % colour,
           ' geometry IndexedFaceSet { solid FALSE coord Coordinate { point [',
           ','.join('%.4f %.4f %.4f' % (v[0] * scale, v[1] * scale, v[2] * scale) for v in verts),
           '] } coordIndex [', ','.join('%d,%d,%d,-1' % f for f in faces), '] } }']
    open(path, 'w').write('\n'.join(out) + '\n')


def length_mm(pts):
    return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
