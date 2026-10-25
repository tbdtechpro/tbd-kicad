#!/usr/bin/env python3
"""Generate projects/teensy-panel: Teensy 4.1 + GC9A01 round display + KY-040 encoder + TK103 I2S DAC
on an ElectroCookie full-size breadboard PCB. Pin assignments match cheap-comp-midi-pcb/ui/README.md.

    python3 tools/gen_teensy_panel.py
"""
import os, sys, uuid, json, math, copy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sexp import parse, find, find1, dump, Str
import wires as WR

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(ROOT, 'lib')
PROJ = os.path.join(ROOT, 'projects', 'teensy-panel')
NAME = 'teensy-panel'
os.makedirs(PROJ, exist_ok=True)


def f(x):
    s = ('%.4f' % x).rstrip('0').rstrip('.')
    return '0' if s in ('-0', '', '-') else s


def U():
    return str(uuid.uuid4())

ROOT_UUID = U()

# ----------------------------------------------------------------- symbols
LIBNAME = 'tbd'
SYMLIB = parse(open(os.path.join(LIB, LIBNAME + '.kicad_sym')).read())[0]
POWERLIB = parse(open('/usr/share/kicad/symbols/power.kicad_sym').read())[0]


def lib_symbol(lib, name):
    return [s for s in find(lib, 'symbol') if s[1] == name][0]


def pins_of(sym):
    """{number: (name, x, y, rot)} in library coordinates (y up)."""
    out = {}
    for sub in find(sym, 'symbol'):
        for p in find(sub, 'pin'):
            at = find1(p, 'at')
            out[find1(p, 'number')[1]] = (find1(p, 'name')[1], float(at[1]), float(at[2]), float(at[3]))
    return out


def prop_pos(sym, key):
    for p in find(sym, 'property'):
        if p[1] == key:
            at = find1(p, 'at')
            return float(at[1]), float(at[2])
    return 0.0, 0.0


# ------------------------------------------------------------ net plan
# Teensy pin number (symbol/footprint numbering) -> net.  From cheap-comp-midi-pcb ui/README.md and
# xtragravy/bench/teensy41/README.md: display SCL/SDA = 13/11, CS/DC/RST = 10/9/8, encoder CLK/DT/SW = 2/3/4,
# DAC BCK/LRCK/DIN = 21/20/7.
TEENSY_NETS = {
    '4': 'ENC_CLK', '5': 'ENC_DT', '6': 'ENC_SW',          # GPIO 2, 3, 4
    '9': 'I2S_DIN',                                        # GPIO 7 (OUT1A)
    '10': 'LCD_RST', '11': 'LCD_DC', '12': 'LCD_CS',       # GPIO 8, 9, 10
    '13': 'SPI_MOSI', '35': 'SPI_SCK',                     # GPIO 11, 13
    '42': 'I2S_LRCK', '43': 'I2S_BCK',                     # GPIO 20, 21
    '15': '+3V3', '46': '+3V3', '1': 'GND', '34': 'GND', '47': 'GND',
}
MODULES = {
    # ref: (symbol, {pin: net}, sheet position)
    'DS1': ('GC9A01_Round_1.28in_7pin', {'1': '+3V3', '2': 'GND', '3': 'SPI_SCK', '4': 'SPI_MOSI', '5': 'LCD_DC',
                                         '6': 'LCD_CS', '7': 'LCD_RST'}, (254.0, 101.6)),
    'SW1': ('KY-040_Rotary_Encoder_Module', {'1': 'GND', '2': '+3V3', '3': 'ENC_SW', '4': 'ENC_DT', '5': 'ENC_CLK'},
            (55.88, 114.3)),
    'U2': ('TK103_PCM5102A_I2S_DAC', {'1': 'GND', '2': '+3V3', '3': 'I2S_BCK', '4': 'I2S_DIN', '5': 'I2S_LRCK',
                                      '6': '+3V3'}, (254.0, 165.1)),
}
TEENSY_AT = (152.4, 139.7)
POWER_NETS = ('+3V3', 'GND')

# ------------------------------------------------------------ schematic
sch = []
lib_symbols = []
used_syms = ['Teensy_4.1'] + [m[0] for m in MODULES.values()]
for n in used_syms:
    s = copy.deepcopy(lib_symbol(SYMLIB, n))
    s[1] = Str(LIBNAME + ':' + n)
    lib_symbols.append(s)
for n in POWER_NETS:
    s = copy.deepcopy(lib_symbol(POWERLIB, n))
    s[1] = Str('power:' + n)
    lib_symbols.append(s)

pwr_count = [0]


def sym_instance(lib_id, ref, value, x, y, rot, sym, extra_props=None, hide_value=False):
    rx, ry = prop_pos(sym, 'Reference')
    vx, vy = prop_pos(sym, 'Value')
    props = [
        f'(property "Reference" "{ref}" (at {f(x + rx)} {f(y - ry)} 0) (effects (font (size 1.27 1.27)) (justify left)'
        + (' (hide yes)' if ref.startswith('#') else '') + '))',
        f'(property "Value" "{value}" (at {f(x + vx)} {f(y - vy)} 0) (effects (font (size 1.27 1.27)) (justify left)))',
    ]
    for key in ('Footprint', 'Datasheet', 'Description'):
        val = ''
        for p in find(sym, 'property'):
            if p[1] == key:
                val = p[2]
        val = val.replace('\\', '\\\\').replace('"', '\\"')
        props.append(f'(property "{key}" "{val}" (at {f(x)} {f(y)} 0) (effects (font (size 1.27 1.27)) (hide yes)))')
    pins = ' '.join(f'(pin "{n}" (uuid "{U()}"))' for n in pins_of(sym))
    return (f'(symbol (lib_id "{lib_id}") (at {f(x)} {f(y)} {rot}) (unit 1) (exclude_from_sim no) (in_bom yes)'
            f' (on_board yes) (dnp no) (uuid "{U()}")\n\t' + '\n\t'.join(props) + f'\n\t{pins}\n'
            f'\t(instances (project "{NAME}" (path "/{ROOT_UUID}" (reference "{ref}") (unit 1)))))')


def wire(x1, y1, x2, y2):
    return f'(wire (pts (xy {f(x1)} {f(y1)}) (xy {f(x2)} {f(y2)})) (stroke (width 0) (type default)) (uuid "{U()}"))'


def label(name, x, y, rot):
    just = 'left bottom' if rot == 0 else 'right bottom'
    return (f'(label "{name}" (at {f(x)} {f(y)} {rot}) (fields_autoplaced yes)'
            f' (effects (font (size 1.27 1.27)) (justify {just})) (uuid "{U()}"))')


def no_connect(x, y):
    return f'(no_connect (at {f(x)} {f(y)}) (uuid "{U()}"))'


def power_symbol(net, x, y, up):
    """+3V3 symbols stand above their pin; GND symbols hang below (or above when up=True)."""
    pwr_count[0] += 1
    sym = lib_symbol(POWERLIB, net)
    rot = 0
    if net == 'GND' and up:
        rot = 180
    return sym_instance('power:' + net, '#PWR%02d' % pwr_count[0], net, x, y, rot, sym)


def connect_pin(px, py, rot, net, is_power_pin):
    """Stub wire from a pin end at (px,py) pointing away from the body, then a label or power symbol."""
    dx = -1 if rot == 0 else 1            # rot 0: pin enters the body from the left, so the stub goes left
    if net in POWER_NETS:
        L = 5.08 if net == 'GND' else 10.16
        ex = px + dx * L
        sch.append(wire(px, py, ex, py))
        sch.append(power_symbol(net, ex, py, up=True if net == 'GND' and is_power_pin == 'teensy' else False))
    else:
        ex = px + dx * 10.16
        sch.append(wire(px, py, ex, py))
        sch.append(label(net, ex, py, 0 if dx > 0 else 180))


# Teensy
tsym = lib_symbol(SYMLIB, 'Teensy_4.1')
TX, TY = TEENSY_AT
sch.append(sym_instance(LIBNAME + ':Teensy_4.1', 'U1', 'Teensy_4.1', TX, TY, 0, tsym))
for num, (pname, px, py, prot) in pins_of(tsym).items():
    sx, sy = TX + px, TY - py
    net = TEENSY_NETS.get(num)
    if net is None:
        sch.append(no_connect(sx, sy))
    elif prot in (0, 180):
        connect_pin(sx, sy, prot, net, 'teensy')
    else:
        sch.append(no_connect(sx, sy))

for ref, (sname, nets, (MX, MY)) in MODULES.items():
    msym = lib_symbol(SYMLIB, sname)
    sch.append(sym_instance(LIBNAME + ':' + sname, ref, sname, MX, MY, 0, msym))
    for num, (pname, px, py, prot) in pins_of(msym).items():
        connect_pin(MX + px, MY - py, prot, nets[num], 'module')

NOTES = [
    'Teensy 4.1 front panel on an ElectroCookie full-size breadboard PCB.',
    'Pin assignments are the ones tested in cheap-comp-midi-pcb (ui/README.md, xtragravy/bench/teensy41/README.md).',
    'Teensy socket: left header in C1-C24, right header in G1-G24, micro-USB at row 1, micro-SD at row 24.',
    'Teensy pin  -> ElectroCookie hole (use the free holes of the same row strip):',
    '  GPIO 2/3/4   (encoder CLK/DT/SW)  -> A4/A5/A6      GPIO 7 (I2S DIN)  -> A9',
    '  GPIO 8/9/10  (LCD RST/DC/CS)      -> A10/A11/A12   GPIO 11 (MOSI)    -> A13    GPIO 13 (SCK) -> J14',
    '  GPIO 20/21   (I2S LRCK/BCK)       -> J7/J6         3.3 V -> A15 or J3          GND -> A1, J2 or J15',
    'TK103 XSMT is pulled high on the module; tied to 3.3 V here as in the tested build (a GPIO could mute it).',
    'All modules run from the Teensy 3.3 V regulator (250 mA max): display backlight + DAC + encoder pull-ups are well under that.',
]
sch.append('(text "%s" (at 20.32 270 0) (effects (font (size 1.778 1.778)) (justify left bottom)) (uuid "%s"))'
           % ('\\n'.join(NOTES), U()))

sch_text = ['(kicad_sch (version 20250114) (generator "eeschema") (generator_version "9.0") (uuid "%s") (paper "A3")' % ROOT_UUID,
            '\t(title_block (title "Teensy 4.1 front panel: GC9A01 + KY-040 + TK103 I2S DAC") (date "2026-10-24") (rev "1")'
            ' (comment 1 "Generated by tools/gen_teensy_panel.py; pins per cheap-comp-midi-pcb Teensy build"))',
            '\t(lib_symbols']
for s in lib_symbols:
    sch_text.append('\t\t' + dump(s, 2))
sch_text.append('\t)')
for item in sch:
    sch_text.append('\t' + item.replace('\n', '\n\t'))
sch_text.append(f'\t(sheet_instances (path "/" (page "1")))')
sch_text.append('\t(embedded_fonts no)')
sch_text.append(')')
open(os.path.join(PROJ, NAME + '.kicad_sch'), 'w').write('\n'.join(sch_text) + '\n')

# ---------------------------------------------------------------- PCB
# ElectroCookie footprint is drawn horizontally (row 1 left, A at the bottom). Rotating it by 270 deg (clockwise
# on screen) puts row 1 at the top and column A on the left, which is how the board is used here.
FPLIB = os.path.join(LIB, LIBNAME + '.pretty')


def load_fp(name):
    return parse(open(os.path.join(FPLIB, name + '.kicad_mod')).read())[0]


def rot(x, y, deg):
    a = math.radians(deg)
    # KiCad PCB: y down; a positive angle rotates counter-clockwise on screen
    return (x * math.cos(a) + y * math.sin(a), -x * math.sin(a) + y * math.cos(a))


def pad_pos(fp, num):
    for p in find(fp, 'pad'):
        if p[1] == num:
            at = find1(p, 'at')
            return float(at[1]), float(at[2])
    raise KeyError(num)


BRD = load_fp('ElectroCookie_Breadboard_Full')
BRD_ROT = 270
BRD_AT = (100.0, 150.0)


def hole(letter, row):
    """Board coordinates of an ElectroCookie hole in the rotated (vertical) orientation."""
    rows = {'J': -13.97, 'I': -11.43, 'H': -8.89, 'G': -6.35, 'F': -3.81,
            'E': 3.81, 'D': 6.35, 'C': 8.89, 'B': 11.43, 'A': 13.97}
    x = -78.74 + 2.54 * (row - 1)
    rx, ry = rot(x, rows[letter], BRD_ROT)
    return BRD_AT[0] + rx, BRD_AT[1] + ry


nets = {}
def net_id(name):
    if name not in nets:
        nets[name] = len(nets) + 1
    return nets[name]


placements = []   # (fp node, lib name, ref, value, x, y, rot, {pad: net}, options)
SOCKET_H = 8.5    # PinSocket_1xNN_P2.54mm_Vertical height: modules sit on top of their sockets


def model(path, offset=(0, 0, 0), rotate=(0, 0, 0)):
    return (f'(model "{path}" (offset (xyz {f(offset[0])} {f(offset[1])} {f(offset[2])})) (scale (xyz 1 1 1))'
            f' (rotate (xyz {f(rotate[0])} {f(rotate[1])} {f(rotate[2])})))')


STOCK_FP = '/usr/share/kicad/footprints'


def load_stock(libname, name):
    return parse(open(os.path.join(STOCK_FP, libname + '.pretty', name + '.kicad_mod')).read())[0]


HDR = '${KICAD9_3DMODEL_DIR}/Connector_PinHeader_2.54mm.3dshapes/PinHeader_1x24_P2.54mm_Vertical.step'

# Teensy: pad 1 on C1, rotated 270 so the USB end (pad 1 end) is at the top.
TFP = load_fp('Teensy41')
p1 = rot(*pad_pos(TFP, '1'), 270)
c1 = hole('C', 1)
# Teensy sits on two 24-pin sockets: socket (8.5) + its own male header plastic (2.54); headers added as extra models.
placements.append((TFP, 'Teensy41', 'U1', 'Teensy_4.1', c1[0] - p1[0], c1[1] - p1[1], 270, TEENSY_NETS,
                   dict(drop_pads={str(n) for n in range(49, 68)}, model_dz=SOCKET_H + 2.54,
                        extra_models=[model(HDR, (-29.21, -7.62, SOCKET_H), (0, 0, -90)),
                                      model(HDR, (29.21, 7.62, SOCKET_H), (0, 0, 90))])))

# GC9A01: 7-pin header down column J rows 32-38, display body over the board centre (toward column A).
GFP = load_fp('GC9A01_Round_1.28in_7pin')
g_rot = 270     # header row (along x in the library) becomes vertical; body (-y in lib) points to -x (over the board)
gp1 = rot(*pad_pos(GFP, '1'), g_rot)
j32 = hole('J', 32)
placements.append((GFP, 'GC9A01_Round_1.28in_7pin', 'DS1', 'GC9A01_Round_1.28in_7pin',
                   j32[0] - gp1[0], j32[1] - gp1[1], g_rot, MODULES['DS1'][1], dict(drop_npth=True, model_dz=SOCKET_H)))
# TK103: 6-pin socket down column A rows 48-53 (pin 1 = GND at A53, pins run upward), module standing toward the left edge (rails).
KFP = load_fp('TK103_Module_RA_Header')
k_rot = 90      # lib -y (module side) -> -x: the standing module faces the left edge
kp1 = rot(*pad_pos(KFP, '1'), k_rot)
a53 = hole('A', 53)
placements.append((KFP, 'TK103_Module_RA_Header', 'U2', 'TK103_PCM5102A_I2S_DAC',
                   a53[0] - kp1[0], a53[1] - kp1[1], k_rot, MODULES['U2'][1], dict(model_dz=SOCKET_H)))
# KY-040: 5-pin socket down column J rows 56-60, module standing toward the right edge.
EFP = load_fp('KY-040_Module_RA_Header')
e_rot = 270     # lib -y (module side) -> +x: the standing module faces the right edge
ep1 = rot(*pad_pos(EFP, '1'), e_rot)
j56 = hole('J', 56)
placements.append((EFP, 'KY-040_Module_RA_Header', 'SW1', 'KY-040_Rotary_Encoder_Module',
                   j56[0] - ep1[0], j56[1] - ep1[1], e_rot, MODULES['SW1'][1], dict(model_dz=SOCKET_H)))

# Female pin sockets soldered to the ElectroCookie (PCB only; not in the schematic). Pin 1 at the top row, rows downward.
def socket(ref, n, letter, row, nets):
    sfp = load_stock('Connector_PinSocket_2.54mm', f'PinSocket_1x{n:02d}_P2.54mm_Vertical')
    hx, hy = hole(letter, row)
    placements.append((sfp, f'PinSocket_1x{n:02d}_P2.54mm_Vertical', ref, f'PinSocket_1x{n:02d}', hx, hy, 0, nets,
                       dict(lib='Connector_PinSocket_2.54mm')))
socket('J1', 24, 'C', 1, {str(i): TEENSY_NETS[str(i)] for i in range(1, 25) if str(i) in TEENSY_NETS})
socket('J2', 24, 'G', 1, {str(i): TEENSY_NETS[str(49 - i)] for i in range(1, 25) if str(49 - i) in TEENSY_NETS})
socket('J3', 7, 'J', 32, MODULES['DS1'][1])
socket('J4', 6, 'A', 48, {str(i): MODULES['U2'][1][str(7 - i)] for i in range(1, 7)})
socket('J5', 5, 'J', 56, MODULES['SW1'][1])

# Breadboard strips carrying the Teensy nets, plus rails: left rails from A15/A1, right rails from J3/J2.
tpins = pins_of(tsym)
brd_nets = {}
for num, net in TEENSY_NETS.items():
    n = int(num)
    if 1 <= n <= 24:
        brd_nets['L%d' % n] = net
    elif 25 <= n <= 48:
        brd_nets['R%d' % (49 - n)] = net
brd_nets.update({'B+': '+3V3', 'B-': 'GND', 'T+': '+3V3', 'T-': 'GND'})
placements.append((BRD, 'ElectroCookie_Breadboard_Full', 'BRD1', 'ElectroCookie_Breadboard_Full',
                   BRD_AT[0], BRD_AT[1], BRD_ROT, brd_nets, {}))

for pl in placements:
    pn = pl[7]
    for net in pn.values():
        net_id(net)

# ------------------------------------------------------------ jumper wires
WDIR = os.path.join(PROJ, 'wires')
os.makedirs(WDIR, exist_ok=True)
wire_items, wire_rows = [], []
for wname, wnet, path in WR.WIRES:
    pts = WR.round_corners(WR.polyline3d(path))
    x1, y1 = pts[0][0], pts[0][1]
    verts, faces = WR.tube([(x - x1, -(y - y1), z) for x, y, z in pts], WR.DIA / 2)   # model frame: 3D Y up
    WR.write_wrl(os.path.join(WDIR, wname + '.wrl'), verts, faces)
    bx, by = BRD_AT
    nid = net_id(wnet)
    pads = ''.join(f'(pad "{k + 1}" thru_hole circle (at {f(pts[i][0]-x1)} {f(pts[i][1]-y1)}) (size 1.6 1.6) (drill 1) '
                   f'(layers "*.Cu" "*.Mask") (net {nid} "{wnet}") (uuid "{U()}"))' for k, i in enumerate((0, -1)))
    wire_items.append(
        f'(footprint "{LIBNAME}:JumperWire" (layer "F.Cu") (uuid "{U()}") (at {f(bx + x1)} {f(by + y1)} 0)'
        f' (descr "22 AWG solid-core jumper, purple sleeve") (tags "wire")'
        f' (property "Reference" "{wname}" (at 0 0 0) (layer "F.SilkS") (hide yes) (uuid "{U()}") (effects (font (size 0.6 0.6) (thickness 0.1))))'
        f' (property "Value" "{wnet}" (at 0 0 0) (layer "F.Fab") (hide yes) (uuid "{U()}") (effects (font (size 0.6 0.6) (thickness 0.1))))'
        f' (property "Footprint" "" (at 0 0 0) (layer "F.Fab") (hide yes) (uuid "{U()}") (effects (font (size 1 1) (thickness 0.15))))'
        f' (property "Datasheet" "" (at 0 0 0) (layer "F.Fab") (hide yes) (uuid "{U()}") (effects (font (size 1 1) (thickness 0.15))))'
        f' (property "Description" "jumper wire" (at 0 0 0) (layer "F.Fab") (hide yes) (uuid "{U()}") (effects (font (size 1 1) (thickness 0.15))))'
        f' (attr through_hole exclude_from_bom) {pads}'
        f' (model "${{KIPRJMOD}}/wires/{wname}.wrl" (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))'
        f' (embedded_fonts no))')
    # The wire's electrical path as an F.Cu track along its route (KiCad 9 cannot jumper two pads of one footprint
    # without copper).  It hides under the purple tube in 3D and doubles as the 2D wiring diagram.
    for i in range(1, len(pts) - 2):
        (xa, ya, _), (xb, yb, _) = pts[i], pts[i + 1]
        if abs(xa - xb) < 1e-6 and abs(ya - yb) < 1e-6:
            continue
        wire_items.append(f'(segment (start {f(bx + xa)} {f(by + ya)}) (end {f(bx + xb)} {f(by + yb)})'
                          f' (width 1) (layer "F.Cu") (net {nid}) (uuid "{U()}"))')
    route = ' > '.join((WR.hole_name(p[0], p[1]) or f'x={p[0]:+.1f}') + (f' r{p[1]:g}' if not isinstance(p[0], str) or True else '')
                       for p in path)
    wire_rows.append((wname, wnet, WR.hole_name(path[0][0], path[0][1]), WR.hole_name(path[-1][0], path[-1][1]),
                      route, WR.length_mm(pts) + 10))


def fp_instance(fp, libname, ref, value, x, y, r, padnets, drop_pads=(), drop_npth=False, model_dz=0.0,
                extra_models=(), lib=LIBNAME):
    fp = copy.deepcopy(fp)
    fp[1] = Str(lib + ':' + libname)
    # strip library-only tokens, set placement
    fp[:] = [n for n in fp if not (isinstance(n, list) and n[0] in ('version', 'generator', 'generator_version'))]
    # pads that exist on the module but not on the carrier (Teensy SD/USB/Ethernet pads, module mounting holes)
    fp[:] = [n for n in fp if not (isinstance(n, list) and n[0] == 'pad' and (n[1] in drop_pads or (drop_npth and 'np_thru_hole' in n)))]
    for m in find(fp, 'model'):
        xyz = find1(find1(m, 'offset'), 'xyz')
        xyz[3] = f(float(xyz[3]) + model_dz)
    for em in extra_models:
        fp.append(parse(em)[0])
    fp.insert(2, ['uuid', Str(U())])
    fp.insert(3, ['at', f(x), f(y), f(r)])
    for p in find(fp, 'property'):
        if p[1] == 'Reference':
            p[2] = Str(ref)
        elif p[1] == 'Value':
            p[2] = Str(value)
        at = find1(p, 'at')
        at[3] = f(float(at[3]) + r)
    for t in find(fp, 'fp_text'):
        at = find1(t, 'at')
        if len(at) > 3:
            at[3] = f(float(at[3]) + r)
    for p in find(fp, 'pad'):
        at = find1(p, 'at')
        if len(at) > 3:
            at[3] = f(float(at[3]) + r)
        else:
            at.append(f(r))
        net = padnets.get(p[1])
        if net:
            idx = max(i for i, n in enumerate(p) if isinstance(n, list) and n[0] == 'layers')
            p.insert(idx + 1, ['net', str(net_id(net)), Str(net)])
    fp.append(['path', Str('/' + ROOT_UUID + '/' + U())])
    fp.append(['sheetname', Str('Root')])
    fp.append(['sheetfile', Str(NAME + '.kicad_sch')])
    return dump(fp, 1)


LAYERS = '''(layers
\t\t(0 "F.Cu" signal) (2 "B.Cu" signal) (9 "F.Adhes" user "F.Adhesive") (11 "B.Adhes" user "B.Adhesive")
\t\t(13 "F.Paste" user) (15 "B.Paste" user) (5 "F.SilkS" user "F.Silkscreen") (7 "B.SilkS" user "B.Silkscreen")
\t\t(1 "F.Mask" user) (3 "B.Mask" user) (17 "Dwgs.User" user "User.Drawings") (19 "Cmts.User" user "User.Comments")
\t\t(21 "Eco1.User" user "User.Eco1") (23 "Eco2.User" user "User.Eco2") (25 "Edge.Cuts" user) (27 "Margin" user)
\t\t(31 "F.CrtYd" user "F.Courtyard") (29 "B.CrtYd" user "B.Courtyard") (35 "F.Fab" user) (33 "B.Fab" user)
\t)'''
pcb = ['(kicad_pcb (version 20241229) (generator "pcbnew") (generator_version "9.0")',
       '\t(general (thickness 1.6) (legacy_teardrops no))', '\t(paper "A3")', '\t' + LAYERS,
       '\t(setup (pad_to_mask_clearance 0) (allow_soldermask_bridges_in_footprints no) (tenting front back)'
       ' (pcbplotparams (layerselection 0x00000000_00000000_55555555_5755f5ff) (plot_on_all_layers_selection 0x00000000_00000000_00000000_00000000)))',
       '\t(net 0 "")']
for name, nid in sorted(nets.items(), key=lambda kv: kv[1]):
    pcb.append(f'\t(net {nid} "{name}")')
for fp, libname, ref, value, x, y, r, pn, opts in placements:
    pcb.append('\t' + fp_instance(fp, libname, ref, value, x, y, r, pn, **opts))
pcb.extend('\t' + w for w in wire_items)

# Board-level B.Cu tracks along every strip and rail that carries a net.  KiCad 9 does not treat copper drawn
# inside a footprint, or coincident pads of different footprints, as connected; these tracks (over the breadboard's
# own copper) give the connectivity engine the strips, so the ratsnest only shows what is really missing.
strip_nets = dict(brd_nets)
for ref, n, letter, row, pinnets in (('J3', 7, 'J', 32, MODULES['DS1'][1]), ('J5', 5, 'J', 56, MODULES['SW1'][1])):
    for i in range(n):
        strip_nets['R%d' % (row + i)] = pinnets[str(i + 1)]
for i in range(6):                                                   # DAC socket A48-53, pin 1 at A53
    strip_nets['L%d' % (53 - i)] = MODULES['U2'][1][str(i + 1)]
for wname, wnet, path in WR.WIRES:
    for lane, row in ((path[0][0], path[0][1]), (path[-1][0], path[-1][1])):
        if isinstance(lane, str) and lane in 'ABCDEFGHIJ':
            strip_nets[('L' if lane in 'ABCDE' else 'R') + str(int(round(row)))] = wnet
        elif isinstance(lane, str):
            strip_nets[lane] = wnet
def seg(x1, y1, x2, y2, net):
    return (f'(segment (start {f(x1)} {f(y1)}) (end {f(x2)} {f(y2)}) (width 1.3) (layer "B.Cu")'
            f' (net {net_id(net)}) (uuid "{U()}"))')
bx, by = BRD_AT
for name, net in sorted(strip_nets.items()):
    if name[0] in 'LR':
        y = by + WR.row_y(int(name[1:]))
        xa, xb = (WR.COLS['A'], WR.COLS['E']) if name[0] == 'L' else (WR.COLS['F'], WR.COLS['J'])
        pcb.append('\t' + seg(bx + xa, y, bx + xb, y, net))
    else:                                                            # rail: rows 0-64 plus its jumper pad
        x = bx + WR.COLS[name]
        pcb.append('\t' + seg(x, by + WR.row_y(0), x, by + WR.row_y(64), net))
        # top jumper (y = -83.82) joins the - rails, bottom jumper (+83.82) the + rails; T pads at x=+1.27, B at -1.27
        sgn = -1 if name[1] == '-' else 1
        jx, jy, ye = bx + (1.27 if name[0] == 'T' else -1.27), by + sgn * 83.82, by + sgn * 84.5
        pcb.append('\t' + seg(x, by + WR.row_y(0 if sgn < 0 else 64), x, ye, net))
        pcb.append('\t' + seg(x, ye, jx, ye, net))
        pcb.append('\t' + seg(jx, ye, jx, jy, net))
# The Teensy joins its own GND pins (C1, G2, G15) and 3V3 pins (C15, G3) on its PCB; the footprint cannot say so,
# so add the ties as tracks hidden under the Teensy (GND on B.Cu, 3V3 on F.Cu so they never cross).
def tie(layer, net, pts_):
    for (xa, ya), (xb, yb) in zip(pts_, pts_[1:]):
        pcb.append(f'\t(segment (start {f(bx + xa)} {f(by + ya)}) (end {f(bx + xb)} {f(by + yb)}) (width 0.8)'
                   f' (layer "{layer}") (net {net_id(net)}) (uuid "{U()}"))')
R = WR.row_y
tie('B.Cu', 'GND', [(WR.COLS['C'], R(1)), (-1.2, R(1)), (-1.2, R(15)), (WR.COLS['G'], R(15))])
tie('B.Cu', 'GND', [(-1.2, R(2)), (WR.COLS['G'], R(2))])
tie('F.Cu', '+3V3', [(WR.COLS['C'], R(15)), (1.2, R(15)), (1.2, R(3)), (WR.COLS['G'], R(3))])
# board outline = the ElectroCookie, vertical
W, H = 52.07, 172.72
pcb.append(f'\t(gr_rect (start {f(BRD_AT[0]-W/2)} {f(BRD_AT[1]-H/2)}) (end {f(BRD_AT[0]+W/2)} {f(BRD_AT[1]+H/2)})'
           f' (stroke (width 0.1) (type default)) (fill no) (layer "Edge.Cuts") (uuid "{U()}"))')
pcb.append('\t(embedded_fonts no)')
pcb.append(')')
open(os.path.join(PROJ, NAME + '.kicad_pcb'), 'w').write('\n'.join(pcb) + '\n')

with open(os.path.join(PROJ, 'WIRES.md'), 'w') as fh:
    fh.write('# teensy-panel: jumper wires (generated by tools/gen_teensy_panel.py)\n\n')
    fh.write('22 AWG solid core, purple sleeve, 1.5 mm OD. Routes are given as hole > waypoint > hole in the vertical view '
             '(row 1 at the top, column A on the left); x is mm from the centre line, r is the row. Cut length includes '
             '10 mm for the two stripped ends.\n\n')
    fh.write('Before wiring: bridge both rail jumpers (top end joins the two - rails, bottom end the two + rails). The right rails '
             'are fed from the Teensy by W01/W02; the left rails then come live through the jumpers.\n\n')
    fh.write('| Wire | Net | From | To | Route | Cut (mm) |\n|---|---|---|---|---|---|\n')
    for wname, wnet, a, b, route, L in wire_rows:
        fh.write(f'| {wname} | {wnet} | {a} | {b} | {route} | {int(round(L / 5.0) * 5)} |\n')
    fh.write('\nIn KiCad the wires are also drawn as 1 mm tracks on F.Cu along their routes (KiCad 9 has no wire object), and '
             'the breadboard strips and rails as 1.3 mm tracks on B.Cu, so the ratsnest and DRC understand the build. '
             'Two airwires remain on purpose: the two rail jumpers, bridged with solder. Ignore the clearance and '
             'co-located-hole DRC errors: they come from the breadboard holes shared by several footprints.\n')
    fh.write('\nLanes: x=-15.6/-17.2/-18.8/-20.4 run beside column A, x=-2.9/0/+2.9 run down the centre gap, '
             'x=+15.6/+17.2 run beside column J. Wires at the same lane are stacked: the display wires lie on the board, '
             'the encoder wires ride on top of them. W07 hops over the x=-17.2 lane at row 36; W13 hops over rows 35-38; '
             'W04 rides over rows 34-38 down column G.\n')

# ------------------------------------------------------- project + tables
pro = {
    "board": {"design_settings": {"defaults": {}, "rule_severities": {}, "rules": {}}, "layer_presets": [], "viewports": []},
    "boards": [], "cvpcb": {"equivalence_files": []},
    "libraries": {"pinned_footprint_libs": ["tbd"], "pinned_symbol_libs": ["tbd"]},
    "meta": {"filename": NAME + ".kicad_pro", "version": 3},
    "net_settings": {"classes": [{"name": "Default", "clearance": 0.2, "track_width": 0.25, "via_diameter": 0.6,
                                  "via_drill": 0.3, "diff_pair_width": 0.2, "diff_pair_gap": 0.25}], "meta": {"version": 4}},
    "pcbnew": {"page_layout_descr_file": ""},
    "schematic": {"legacy_lib_dir": "", "legacy_lib_list": []},
    "sheets": [[ROOT_UUID, "Root"]], "text_variables": {},
}
json.dump(pro, open(os.path.join(PROJ, NAME + '.kicad_pro'), 'w'), indent=2)
open(os.path.join(PROJ, 'sym-lib-table'), 'w').write(
    '(sym_lib_table (version 7)\n  (lib (name "tbd")(type "KiCad")(uri "${KIPRJMOD}/../../lib/tbd.kicad_sym")(options "")(descr "tbd-kicad component library"))\n)\n')
open(os.path.join(PROJ, 'fp-lib-table'), 'w').write(
    '(fp_lib_table (version 7)\n  (lib (name "tbd")(type "KiCad")(uri "${KIPRJMOD}/../../lib/tbd.pretty")(options "")(descr "tbd-kicad footprints"))\n)\n')
print('nets:', nets)
print('wrote', PROJ)
