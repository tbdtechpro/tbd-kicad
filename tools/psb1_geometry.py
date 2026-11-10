"""Geometry of the ProtoSupplies PSB-1 MCU proto board, shared by gen_lib.py (library footprints) and gen_psb1.py
(schematic + layout). Grid coordinates: column C and row R from 0 at the top-left, 2.54 mm pitch, 38 x 38 positions
centred on the 102 x 102 mm board. Read from the vendor dimension drawing, the vendor CAD renders and photos of the
real board (2026-11-10)."""
P = 2.54
BOARD = 102.0
CORNER_R = 1.5
MOUNT = 45.72                      # mounting holes on a 91.44 mm square
HOLE_D = 3.5

# Two assumptions a meter on the real board can settle (both are how the vendor renders draw the copper):
V_COMMON = False                   # True if the seven V bus columns are one net
FEED_PAIRS_JOINED = False          # True if the G-band pad and V-band pad of a feed pair are one copper strip


def grid(c, r):
    return (c - 18.5) * P, (r - 18.5) * P


# bus columns: column -> (first row, last row)
V_COLS = {0: (6, 24), 5: (6, 24), 10: (6, 24), 18: (6, 37), 26: (6, 37), 31: (6, 33), 36: (6, 33)}
G_COLS = {1: (6, 24), 6: (6, 24), 11: (6, 37), 19: (6, 37), 27: (6, 37), 32: (6, 33), 37: (6, 33)}
FEED = (3, 8, 15, 22, 29, 34)      # columns of the feed pad pairs: row 4 in the G band, row 5 in the V band
G_BAND_ROW, V_BAND_ROW = 4, 5
# V band segments (front copper): (first column, V column) for V1..V7; the first segment has no feed pad
V_SEGMENTS = [(0, 0), (2, 5), (7, 10), (12, 18), (20, 26), (28, 31), (33, 36)]
# prototyping strips: (group letter, first col, last col, first row, last row); pad/net name = letter + (row + 1)
STRIPS = (('a', 2, 4, 6, 24), ('b', 7, 9, 6, 24), ('c', 12, 17, 6, 37), ('d', 20, 25, 6, 37), ('e', 28, 30, 6, 33), ('f', 33, 35, 6, 33))
JUMPER_ORIGIN = (9, 26)            # 2x2 VIN/V header, pin 1 top-left; row 26 = V (column 10 segment), row 27 = VIN
VIN_COL = (10, 28, 37)             # column, first row, last row
HEADER_2X20 = (3, 1, 20)           # column of pin 1, row of pin 1 (odd pins), number of columns; even pins one row up
HEADER_2X10 = (25, 1, 10)          # staggered: even pins and their breakouts sit +1.27 mm to the right


def v_net(i):
    return 'V' if V_COMMON else f'V{i}'


def v_net_of_col(c):
    return v_net(sorted(V_COLS).index(c) + 1)


# kit components of the DC input section: ref, stock footprint library, footprint, grid position of pad 1,
# KiCad rotation, value, stock symbol, pad -> net. Positions +/-0.15 mm from the vendor render; nets from the vendor
# schematic; LED anode from the back-side trace on the real board (R1 feeds the upper LED pad).
KIT = [
    ('P1', 'Connector_BarrelJack', 'BarrelJack_GCT_DCJ200-10-A_Horizontal', (4.28, 33.14), 0, 'DC jack 2.1 mm',
     'Connector', 'Barrel_Jack_Switch', {'1': 'VIN', '2': 'G', '3': 'G'}),
    ('J1', 'Connector_JST', 'JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical', (0.75, 30.5), 90, 'JST XH 2-pin',
     'Connector_Generic', 'Conn_01x02', {'1': 'VIN', '2': 'G'}),
    ('C1', 'Capacitor_THT', 'CP_Radial_D5.0mm_P2.00mm', (4.0, 30.54), 90, '100uF',
     'Device', 'C_Polarized', {'1': 'VIN', '2': 'G'}),
    ('C2', 'Capacitor_THT', 'C_Disc_D5.0mm_W2.5mm_P2.50mm', (6.0, 30.5), 90, '100nF',
     'Device', 'C', {'1': 'VIN', '2': 'G'}),
    ('R1', 'Resistor_THT', 'R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal', (7.5, 29.0), 270, '1k',
     'Device', 'R', {'1': 'VIN', '2': 'LED'}),
    ('D1', 'LED_THT', 'LED_D3.0mm', (7.5, 36.0), 90, 'LED 3 mm green',
     'Device', 'LED', {'1': 'G', '2': 'LED'}),
    ('JP1', 'Connector_PinHeader_2.54mm', 'PinHeader_2x02_P2.54mm_Vertical', JUMPER_ORIGIN, 0, 'VIN/V jumper',
     'Connector_Generic', 'Conn_02x02_Odd_Even', {'1': v_net_of_col(10), '2': v_net_of_col(10), '3': 'VIN', '4': 'VIN'}),
]
STOCK_3D = '${KICAD9_3DMODEL_DIR}/'


def grid_pads():
    """All prototyping-area pads as (net/pad name, c, r, square) - everything except the headers and the kit parts."""
    out = []
    for i, (c, (r0, r1)) in enumerate(sorted(V_COLS.items()), start=1):
        out += [(v_net(i), c, r, r == r0) for r in range(r0, r1 + 1)]
        if i > 1:
            out.append((v_net(i), FEED[i - 2], V_BAND_ROW, True))
    for c, (r0, r1) in G_COLS.items():
        out += [('G', c, r, r == r0) for r in range(r0, r1 + 1)]
    out += [('G', c, G_BAND_ROW, True) for c in FEED]
    for grp, c0, c1, r0, r1 in STRIPS:
        out += [(f'{grp}{r + 1}', c, r, False) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)]
    c, r0, r1 = VIN_COL
    out += [('VIN', c, r, r == r0) for r in range(r0, r1 + 1)]
    return out


def copper_runs():
    """Bus copper as (layer, net, [(c, r), ...]) polylines, as on the real board: V band on the front, G band on the
    back, columns and strips on both sides."""
    runs = []
    for i, (c0, c) in enumerate(V_SEGMENTS, start=1):
        r0, r1 = V_COLS[c]
        runs.append(('F.Cu', v_net(i), [(c0, V_BAND_ROW), (c, V_BAND_ROW), (c, r1)]))
        runs.append(('B.Cu', v_net(i), [(c, r0), (c, r1)]))
    runs.append(('B.Cu', 'G', [(1, G_BAND_ROW), (37, G_BAND_ROW)]))
    for c, (r0, r1) in G_COLS.items():
        runs.append(('B.Cu', 'G', [(c, G_BAND_ROW), (c, r1)]))
        runs.append(('F.Cu', 'G', [(c, r0), (c, r1)]))
    for grp, c0, c1, r0, r1 in STRIPS:
        for r in range(r0, r1 + 1):
            runs.append(('F.Cu', f'{grp}{r + 1}', [(c0, r), (c1, r)]))
            runs.append(('B.Cu', f'{grp}{r + 1}', [(c0, r), (c1, r)]))
    c, r0, r1 = VIN_COL
    jc, jr = JUMPER_ORIGIN
    runs.append(('F.Cu', v_net_of_col(10), [(10, V_COLS[10][1]), (10, jr), (jc, jr)]))
    runs.append(('F.Cu', 'VIN', [(jc, jr + 1), (c, jr + 1), (c, r1)]))
    runs.append(('B.Cu', 'VIN', [(c, r0), (c, r1)]))
    return runs


def input_runs():
    """DC-input section copper (back side): VIN distribution and the ground return, as (layer, net, width, points)."""
    return [
        ('B.Cu', 'VIN', 1.0, [(9, 27), (9, 30.5), (0.75, 30.5)]),                     # VIN bus to J1, C1, C2
        ('B.Cu', 'VIN', 1.0, [(7.5, 30.5), (7.5, 29.0)]),                              # R1
        ('B.Cu', 'VIN', 1.0, [(4.0, 30.54), (4.0, 33.14), (4.28, 33.14)]),              # jack centre pin
        ('B.Cu', 'LED', 0.4, [(7.5, 33.0), (7.5, 35.0)]),                               # R1 to LED anode
        ('B.Cu', 'G', 0.6, [(0.75, 29.5), (4.0, 29.74), (6.0, 29.5)]),                  # J1, C1, C2 ground
        ('F.Cu', 'G', 0.6, [(0.75, 29.5), (3.0, 29.5), (3.0, 35.62), (4.28, 35.62)]),    # J1 ground down to the jack sleeve on the front (crosses the VIN run)
        ('B.Cu', 'G', 0.6, [(6.17, 34.28), (6.17, 35.62)]),                             # jack switch pin
        ('B.Cu', 'G', 0.4, [(4.28, 35.62), (7.5, 35.62), (7.5, 36.0), (7.5, 37.7), (11, 37.7), (11, 37)]),   # LED cathode to the G column
    ]


def header_links():
    """Header pin to breakout-pad copper as (layer, net, [(c, r), ...]): odd pins straight down on the back, even pins
    on the front swinging between the columns, as the real board routes them."""
    runs = []
    for (c0, r0, n), key, dx, odd_rows, even_rows in ((HEADER_2X20, 'H', 0.0, (0, 1), (-1, 2)), (HEADER_2X10, 'K', 0.5, (0, 2), (-1, 1))):
        for i in range(n):
            c = c0 + i
            runs.append(('B.Cu', f'{key}{2*i+1}', [(c, r0 + odd_rows[0]), (c, r0 + odd_rows[1])]))
            ce = c + dx
            if dx == 0:
                runs.append(('F.Cu', f'{key}{2*i+2}', [(ce, r0 + even_rows[0]), (ce + 0.5, r0 + even_rows[0] + 0.5),
                                                        (ce + 0.5, r0 + even_rows[1] - 0.5), (ce, r0 + even_rows[1])]))
            else:
                runs.append(('F.Cu', f'{key}{2*i+2}', [(ce, r0 + even_rows[0]), (ce, r0 + even_rows[1])]))
    return runs

