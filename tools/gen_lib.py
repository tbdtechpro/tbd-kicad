#!/usr/bin/env python3
"""Build lib/tbd.kicad_sym and lib/tbd.pretty/.

Every dimension here is cited in docs/components.md. Re-run after editing:
    python3 tools/gen_lib.py
"""
import os, sys, uuid, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sexp import parse, find, find1, dump, Str

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(ROOT, 'lib')
VENDOR = os.path.join(LIB, 'vendor')
LIBNAME = 'tbd'
PRETTY = os.path.join(LIB, LIBNAME + '.pretty')
MODEL = '${KIPRJMOD}/../../lib/3d/'


def f(x):
    s = ('%.4f' % x).rstrip('0').rstrip('.')
    return '0' if s in ('-0', '', '-') else s


def U():
    return str(uuid.uuid4())

# ----------------------------------------------------------------- symbols

def pin(num, name, etype, x, y, rot, length=2.54):
    return (f'(pin {etype} line (at {f(x)} {f(y)} {rot}) (length {f(length)})'
            f' (name "{name}" (effects (font (size 1.27 1.27))))'
            f' (number "{num}" (effects (font (size 1.27 1.27)))))')


def prop(name, value, x, y, hide=False, justify=None):
    eff = '(effects (font (size 1.27 1.27))'
    if justify:
        eff += f' (justify {justify})'
    if hide:
        eff += ' (hide yes)'
    eff += ')'
    return f'(property "{name}" "{value}" (at {f(x)} {f(y)} 0) {eff})'


def box_symbol(name, ref, left, right, footprint, datasheet, desc, keywords, fp_filters=''):
    """Rectangular symbol. left/right are lists of (number, name, electrical_type) or None for a gap."""
    nl, nr = len(left), len(right)
    rows = max(nl, nr)
    half = 2.54 * math.ceil((rows + 1) / 2)          # pins land on the 2.54 grid
    maxL = max([len(p[1]) for p in left if p] + [0])
    maxR = max([len(p[1]) for p in right if p] + [0])
    W = 5.08 * math.ceil(((maxL + maxR) * 1.27 + 7.62) / 5.08)
    W = max(W, 15.24)
    pins = []
    for i, p in enumerate(left):
        if p:
            pins.append(pin(p[0], p[1], p[2], -(W / 2 + 2.54), half - 2.54 * (i + 1), 0))
    for i, p in enumerate(right):
        if p:
            pins.append(pin(p[0], p[1], p[2], (W / 2 + 2.54), half - 2.54 * (i + 1), 180))
    body = (f'(rectangle (start {f(-W/2)} {f(half)}) (end {f(W/2)} {f(-half)})'
            ' (stroke (width 0.254) (type default)) (fill (type background)))')
    props = [
        prop('Reference', ref, -W / 2, half + 1.27, justify='left'),
        prop('Value', name, -W / 2, -half - 1.27, justify='left'),
        prop('Footprint', footprint, 0, -half - 3.81, hide=True),
        prop('Datasheet', datasheet, 0, -half - 6.35, hide=True),
        prop('Description', desc, 0, -half - 8.89, hide=True),
        prop('ki_keywords', keywords, 0, 0, hide=True),
    ]
    if fp_filters:
        props.append(prop('ki_fp_filters', fp_filters, 0, 0, hide=True))
    return ('(symbol "%s" (pin_names (offset 1.016)) (exclude_from_sim no) (in_bom yes) (on_board yes)\n\t%s\n'
            '\t(symbol "%s_0_1" %s)\n\t(symbol "%s_1_1"\n\t\t%s\n\t)\n\t(embedded_fonts no)\n)'
            % (name, '\n\t'.join(props), name, body, name, '\n\t\t'.join(pins)))


def set_prop(sym, key, value, hide=None):
    for p in find(sym, 'property'):
        if p[1] == key:
            p[2] = Str(value)
            return
    node = ['property', Str(key), Str(value), ['at', '0', '0', '0'],
            ['effects', ['font', ['size', '1.27', '1.27']], ['hide', 'yes']]]
    # insert after the last existing property
    idx = max(i for i, n in enumerate(sym) if isinstance(n, list) and n[0] == 'property')
    sym.insert(idx + 1, node)


KICAD10_ONLY = {'in_pos_files', 'duplicate_pin_numbers_are_jumpers', 'show_name', 'do_not_autoplace'}


def strip_v10(node):
    """Drop tokens that only KiCad 10 (format 20251024) understands."""
    if isinstance(node, list):
        node[:] = [n for n in node if not (isinstance(n, list) and n and n[0] in KICAD10_ONLY)]
        for n in node:
            strip_v10(n)
    return node


def vendored_symbol(path, oldname, newname, footprint, datasheet, desc, keywords, power_out_pins=()):
    root = strip_v10(parse(open(path).read())[0])
    sym = [s for s in find(root, 'symbol') if s[1] == oldname][0]
    sym[1] = Str(newname)
    for sub in find(sym, 'symbol'):
        sub[1] = Str(newname + sub[1][len(oldname):])
    set_prop(sym, 'Value', newname)
    set_prop(sym, 'Footprint', footprint)
    set_prop(sym, 'Datasheet', datasheet)
    set_prop(sym, 'Description', desc)
    set_prop(sym, 'ki_keywords', keywords)
    for sub in find(sym, 'symbol'):
        for p in find(sub, 'pin'):
            if find1(p, 'number')[1] in power_out_pins:
                p[1] = 'power_out'
    return dump(sym, 0)

# ------------------------------------------------------------- footprints

def fp_prop(name, value, x, y, layer, hide=False):
    return (f'(property "{name}" "{value}" (at {f(x)} {f(y)} 0) (layer "{layer}")'
            + (' (hide yes)' if hide else '') + f' (uuid "{U()}")'
            ' (effects (font (size 1 1) (thickness 0.15))))')


def fp_line(x1, y1, x2, y2, layer, w=0.12):
    return (f'(fp_line (start {f(x1)} {f(y1)}) (end {f(x2)} {f(y2)})'
            f' (stroke (width {f(w)}) (type solid)) (layer "{layer}") (uuid "{U()}"))')


def fp_rect(x1, y1, x2, y2, layer, w=0.12):
    return (f'(fp_rect (start {f(x1)} {f(y1)}) (end {f(x2)} {f(y2)})'
            f' (stroke (width {f(w)}) (type solid)) (fill no) (layer "{layer}") (uuid "{U()}"))')


def fp_circle(cx, cy, r, layer, w=0.12):
    return (f'(fp_circle (center {f(cx)} {f(cy)}) (end {f(cx + r)} {f(cy)})'
            f' (stroke (width {f(w)}) (type solid)) (fill no) (layer "{layer}") (uuid "{U()}"))')


def fp_text(text, x, y, layer, size=1.0, thick=0.15, rot=0):
    return (f'(fp_text user "{text}" (at {f(x)} {f(y)} {rot}) (layer "{layer}") (uuid "{U()}")'
            f' (effects (font (size {f(size)} {f(size)}) (thickness {f(thick)}))))')


def pad_tht(num, x, y, size=1.7, drill=1.0, shape='circle', rot=0):
    return (f'(pad "{num}" thru_hole {shape} (at {f(x)} {f(y)} {rot}) (size {f(size)} {f(size)})'
            f' (drill {f(drill)}) (layers "*.Cu" "*.Mask") (remove_unused_layers no) (uuid "{U()}"))')


def pad_npth(x, y, drill):
    return (f'(pad "" np_thru_hole circle (at {f(x)} {f(y)}) (size {f(drill)} {f(drill)})'
            f' (drill {f(drill)}) (layers "*.Cu" "*.Mask") (uuid "{U()}"))')


def pad_smd(num, x, y, sx, sy, layer='F.Cu'):
    mask = 'F.Mask' if layer == 'F.Cu' else 'B.Mask'
    paste = 'F.Paste' if layer == 'F.Cu' else 'B.Paste'
    return (f'(pad "{num}" smd rect (at {f(x)} {f(y)}) (size {f(sx)} {f(sy)})'
            f' (layers "{layer}" "{paste}" "{mask}") (uuid "{U()}"))')


def model(path, offset=(0, 0, 0), rotate=(0, 0, 0), scale=(1, 1, 1)):
    return (f'(model "{path}" (offset (xyz {f(offset[0])} {f(offset[1])} {f(offset[2])}))'
            f' (scale (xyz {f(scale[0])} {f(scale[1])} {f(scale[2])}))'
            f' (rotate (xyz {f(rotate[0])} {f(rotate[1])} {f(rotate[2])})))')


def footprint(name, descr, tags, attr, items, ref_y, val_y, jumpers=False):
    head = [
        f'(footprint "{name}" (version 20241229) (generator "pcbnew") (generator_version "9.0") (layer "F.Cu")',
        f'\t(descr "{descr}")', f'\t(tags "{tags}")',
        '\t' + fp_prop('Reference', 'REF**', 0, ref_y, 'F.SilkS'),
        '\t' + fp_prop('Value', name, 0, val_y, 'F.Fab'),
        '\t' + fp_prop('Datasheet', '', 0, 0, 'F.Fab', hide=True),
        '\t' + fp_prop('Description', '', 0, 0, 'F.Fab', hide=True),
        f'\t(attr {attr})',
    ]
    return '\n'.join(head + ['\t' + i for i in items] + ['\t(embedded_fonts no)', ')'])


def write_fp(name, text):
    os.makedirs(PRETTY, exist_ok=True)
    with open(os.path.join(PRETTY, name + '.kicad_mod'), 'w') as fh:
        fh.write(text + '\n')


def vendored_footprint(path, newname, descr, tags, model_path=None, model_offset=(0, 0, 0), model_rot=(0, 0, 0)):
    root = parse(open(path).read())[0]
    root[1] = Str(newname)
    for p in find(root, 'property'):
        if p[1] == 'Value':
            p[2] = Str(newname)
    for key, val in (('descr', descr), ('tags', tags)):
        n = find1(root, key)
        if n:
            n[1] = Str(val)
        else:
            root.insert(5, [key, Str(val)])
    if not find1(root, 'attr'):
        root.insert(6, ['attr', 'through_hole'])
    root[:] = [n for n in root if not (isinstance(n, list) and n[0] == 'model')]
    if model_path:
        root.append(parse(model(model_path, model_offset, model_rot))[0])
    write_fp(newname, dump(root))

# ================================================================ parts

symbols = []

# --- Teensy 4.1 (XenGi symbol + footprint, MIT) ---------------------------
symbols.append(vendored_symbol(
    os.path.join(VENDOR, 'teensy', 'teensy.kicad_sym'), 'Teensy4.1', 'Teensy_4.1',
    f'{LIBNAME}:Teensy41',
    'https://www.pjrc.com/store/teensy41.html',
    'PJRC Teensy 4.1, i.MX RT1062 Cortex-M7 600 MHz, 3.3 V logic (not 5 V tolerant). '
    'Through-hole pins 1-48 (two rows of 24, 0.6 in apart), SD/USB-host/Ethernet pads 49-67.',
    'teensy pjrc imxrt1062 cortex-m7', power_out_pins=('46', '47')))   # 3V3 regulator output and GND drive the power nets
vendored_footprint(os.path.join(VENDOR, 'teensy', 'Teensy41.kicad_mod'), 'Teensy41',
                   'Teensy 4.1, 2.4 x 0.7 in, 2x24 pins at 2.54 mm pitch, rows 15.24 mm apart; '
                   'pin 1 (GND) at the USB end. Footprint by XenGi/teensy.pretty (MIT).',
                   'teensy pjrc', MODEL + 'Teensy_4.1_Assembly.wrl')   # coloured VRML; KiCad swaps in the .step for STEP export

# --- DFRobot Beetle RP2350 (DFR1188) --------------------------------------
beetle_left = [('1', 'GND', 'power_in'), ('2', '3V3', 'power_out'), ('3', 'GPIO0', 'bidirectional'),
               ('4', 'GPIO1', 'bidirectional'), ('5', 'GPIO4', 'bidirectional'), ('6', 'GPIO5', 'bidirectional'),
               ('7', 'GPIO8', 'bidirectional'), ('8', 'GPIO9', 'bidirectional')]
beetle_right = [('16', 'BAT', 'passive'), ('15', 'GND', 'power_in'), ('14', 'VCC', 'passive'),
                ('13', 'GPIO27/ADC1', 'bidirectional'), ('12', 'GPIO26/ADC0', 'bidirectional'),
                ('11', 'GPIO19', 'bidirectional'), ('10', 'GPIO18', 'bidirectional'), ('9', 'GPIO16', 'bidirectional')]
symbols.append(box_symbol(
    'Beetle_RP2350_DFR1188', 'U', beetle_left, beetle_right,
    f'{LIBNAME}:Beetle_RP2350_DFR1188_THT',
    'https://wiki.dfrobot.com/SKU_DFR1188_Beetle_RP2350',
    'DFRobot Beetle RP2350 (DFR1188): RP2350A, USB-C, TP4057 LiPo charger (BAT), RT9080 3.3 V LDO, '
    '20.5 x 25 mm, 16 castellated pads. Pad order per DFRobot CAD; VCC is the USB 5 V rail.',
    'rp2350 dfrobot beetle', 'Beetle_RP2350*'))
# Pad geometry from DFRobot's DFR1188 CAD release (V1.0), redrawn here in a pad-centred frame: 2 x 8 pads at 2.54 mm,
# rows 17.78 mm apart (THT) or 19.28 mm apart (castellation pads), board 20.5 x 25 mm with the USB-C 1.65 mm proud of the top edge.
for kind, pad in (('THT', lambda n, x, y: pad_tht(n, x, y, 1.5, 0.9, 'rect' if n == 1 else 'circle')),
                  ('SMD', lambda n, x, y: pad_smd(n, x, y, 3.0, 1.6))):
    items = []
    px = 8.89 if kind == 'THT' else 9.64
    for i in range(8):
        items.append(pad(i + 1, -px, -8.89 + 2.54 * i))
        items.append(pad(16 - i, px, -8.89 + 2.54 * i))
    for layer in ('F.Fab', 'F.SilkS'):
        w = 0.1 if layer == 'F.Fab' else 0.12
        items.append(fp_rect(-10.25, -11.42, 10.25, 13.58, layer, w))
        items.append(fp_rect(-4.5, -13.07, 4.5, -11.42, layer, w))                     # USB-C
    items.append(fp_rect(-11.4, -13.3, 11.4, 13.85, 'F.CrtYd', 0.05))
    items.append(fp_text('1=GND 3V3 0 1 4 5 8 9 | 16=BAT GND VCC 27 26 19 18 9=16', 0, 10.5, 'F.Fab', 0.6, 0.1))
    items.append(fp_text('${REFERENCE}', 0, 0, 'F.Fab'))
    write_fp('Beetle_RP2350_DFR1188_' + kind, footprint(
        'Beetle_RP2350_DFR1188_' + kind,
        'DFRobot Beetle RP2350 (DFR1188), ' + ('through-hole pads for header mounting' if kind == 'THT' else
        'SMD pads for soldering the castellations flat') + '; pad 1 = GND at top-left with USB-C at top. '
        'Pad pitch and row spacing from DFRobot DFR1188 CAD V1.0; outline from the dimension drawing.',
        'rp2350 dfrobot beetle', 'through_hole' if kind == 'THT' else 'smd', items, -15, 15.5))

# --- 2.8" ILI9341 SPI TFT module, lcdwiki MSP2806/MSP2807 ------------------
tft_left = [('1', 'VCC', 'power_in'), ('2', 'GND', 'power_in'), ('3', 'CS', 'input'), ('4', 'RESET', 'input'),
            ('5', 'DC', 'input'), ('6', 'SDI(MOSI)', 'input'), ('7', 'SCK', 'input'), ('8', 'LED', 'input'),
            ('9', 'SDO(MISO)', 'output')]
tft_right = [('10', 'T_CLK', 'input'), ('11', 'T_CS', 'input'), ('12', 'T_DIN', 'input'), ('13', 'T_DO', 'output'),
             ('14', 'T_IRQ', 'output'), None, ('15', 'SD_CS', 'input'), ('16', 'SD_MOSI', 'input'),
             ('17', 'SD_MISO', 'output'), ('18', 'SD_SCK', 'input')]
symbols.append(box_symbol(
    'TFT_2.8in_ILI9341_SPI_MSP2806', 'DS', tft_left, tft_right,
    f'{LIBNAME}:TFT_2.8in_ILI9341_SPI_MSP2806',
    'http://www.lcdwiki.com/2.8inch_SPI_Module_ILI9341_SKU:MSP2807',
    '2.8 inch 240x320 TFT, ILI9341, 4-wire SPI, 14-pin header J2 (1-14) and 4-pin micro SD header J4 (15-18). '
    'Touch pins 10-14 are present on the header; the no-touch variant (MSP2806) leaves the XPT2046 unpopulated. '
    'VCC 3.3-5 V (onboard LDO), logic 3.3 V.', 'tft lcd ili9341 spi 2.8', 'TFT_2.8in*'))

items = []
# outline, front view, header J2 along the bottom edge (lcdwiki MSP2806_Size.pdf)
for layer in ('F.Fab', 'F.SilkS'):
    items.append(fp_rect(-25, -43, 25, 43, layer, 0.1 if layer == 'F.Fab' else 0.12))
items.append(fp_rect(-25.25, -43.25, 25.25, 43.25, 'F.CrtYd', 0.05))
items.append(fp_rect(-25, -33.7, 25, 35.5, 'F.Fab', 0.1))          # LCD glass 50 x 69.2
items.append(fp_rect(-21.6, -30.3, 21.6, 27.3, 'F.Fab', 0.1))      # active area 43.2 x 57.6 (vertical position approx.)
items.append(fp_text('2.8in TFT 240x320 active area', 0, 0, 'F.Fab', 1.5, 0.2))
for i in range(14):
    items.append(pad_tht(i + 1, -16.51 + 2.54 * i, 41.0, shape='rect' if i == 0 else 'circle'))
for i in range(4):
    items.append(pad_tht(15 + i, -3.81 + 2.54 * i, -36.6, shape='rect' if i == 0 else 'circle'))
for x in (-22, 22):
    for y in (-40.0, 36.08):
        items.append(pad_npth(x, y, 3.2))
        items.append(fp_circle(x, y, 2.35, 'F.Fab', 0.1))
items.append(fp_text('J2: 1=VCC 2=GND 3=CS 4=RESET 5=DC 6=MOSI 7=SCK 8=LED 9=MISO 10-14=touch', 0, 38.5, 'F.Fab', 0.8, 0.12))
items.append(fp_text('J4: 15=SD_CS 16=SD_MOSI 17=SD_MISO 18=SD_SCK', 0, -38.8, 'F.Fab', 0.8, 0.12))
items.append(fp_text('${REFERENCE}', 0, -10, 'F.Fab'))
write_fp('TFT_2.8in_ILI9341_SPI_MSP2806', footprint(
    'TFT_2.8in_ILI9341_SPI_MSP2806',
    '2.8 inch ILI9341 SPI TFT module, 50 x 86 mm PCB, 14-pin header 2.00 mm from the bottom edge starting 8.49 mm from '
    'the left, 4-pin SD header 6.40 mm from the top centred, four 3.2 mm holes on a 44 x 76.08 mm pattern 3 mm from '
    'the top/side edges. Dimensions from lcdwiki MSP2806_Size.pdf V1.0 (2024-04-11).',
    'tft lcd ili9341 2.8', 'through_hole', items, -45, 45))

# --- 1.28" round GC9A01, 7-pin header -------------------------------------
gc_left = [('1', 'VCC', 'power_in'), ('3', 'SCL', 'input'), ('4', 'SDA', 'input'), ('5', 'DC', 'input'),
           ('6', 'CS', 'input'), ('7', 'RST', 'input'), ('2', 'GND', 'power_in')]
symbols.append(box_symbol(
    'GC9A01_Round_1.28in_7pin', 'DS', gc_left, [],
    f'{LIBNAME}:GC9A01_Round_1.28in_7pin', '',
    '1.28 inch round 240x240 IPS TFT, GC9A01, 4-wire SPI, 7-pin 2.54 mm header (VCC GND SCL SDA DC CS RST). '
    '3.3 V logic. CS may be tied low on the module (R8), RST can float.', 'gc9a01 round tft spi 1.28', 'GC9A01*'))
items = []
R = 18.75
yt = -math.sqrt(R * R - 13.5 * 13.5)
for layer in ('F.Fab', 'F.SilkS'):
    w = 0.1 if layer == 'F.Fab' else 0.12
    items.append(fp_circle(0, 0, R, layer, w))
    items.append(fp_line(-13.5, -26.25, 13.5, -26.25, layer, w))
    items.append(fp_line(-13.5, -26.25, -13.5, yt, layer, w))
    items.append(fp_line(13.5, -26.25, 13.5, yt, layer, w))
items.append(fp_rect(-19, -26.5, 19, 19, 'F.CrtYd', 0.05))
items.append(fp_circle(0, 0, 16.2, 'F.Fab', 0.1))                   # 32.4 mm active area
for i in range(7):
    items.append(pad_tht(i + 1, -7.62 + 2.54 * i, -23.75, shape='rect' if i == 0 else 'circle'))
for x in (-11.5, 11.5):
    items.append(pad_npth(x, -23.75, 2.2))
items.append(fp_text('1=VCC GND SCL SDA DC CS 7=RST', 0, -20.5, 'F.Fab', 0.8, 0.12))
items.append(fp_text('outline approx: verify with calipers', 0, 5, 'F.Fab', 0.8, 0.12))
items.append(fp_text('${REFERENCE}', 0, -5, 'F.Fab'))
items.append(model(MODEL + 'GC9A01_Round_1.28in_7pin.wrl'))       # built by tools/build_models.py in this frame
write_fp('GC9A01_Round_1.28in_7pin', footprint(
    'GC9A01_Round_1.28in_7pin',
    '1.28 inch round GC9A01 module with 7-pin 2.54 mm header on a rectangular tab. Header geometry exact; '
    'round outline (dia 37.5), tab (27 x 7.5) and M2 holes at +/-11.5 mm are estimates from photos and seller '
    'listings (38 x 45.5 mm overall). Verify before cutting a panel.',
    'gc9a01 round tft 1.28', 'through_hole', items, -28.5, 21))

# --- KY-040 rotary encoder module (right-angle 5-pin header) ---------------
ky_left = [('2', '+', 'power_in'), ('5', 'CLK', 'output'), ('4', 'DT', 'output'), ('3', 'SW', 'output'),
           ('1', 'GND', 'power_in')]
symbols.append(box_symbol(
    'KY-040_Rotary_Encoder_Module', 'SW', ky_left, [],
    f'{LIBNAME}:KY-040_Module_RA_Header', '',
    'KY-040 rotary encoder module: EC11-style encoder with push switch, 10 k pull-ups on CLK and DT to +, '
    'SW pulls to GND when pressed (no pull-up on most boards). 5-pin right-angle 2.54 mm header.',
    'ky-040 rotary encoder module', 'KY-040*'))
items = []
for i in range(5):
    items.append(pad_tht(i + 1, -5.08 + 2.54 * i, 0, shape='rect' if i == 0 else 'circle'))
items.append(fp_rect(-6.35, -1.27, 6.35, 1.27, 'F.SilkS'))
items.append(fp_rect(-9.5, -5.0, 9.5, -3.4, 'F.Fab', 0.1))          # module PCB edge-on (19 wide, 1.6 thick), same header as TK103
items.append(fp_rect(-9.75, -8.0, 9.75, 1.5, 'F.CrtYd', 0.05))
items.append(fp_text('KY-040 stands vertical, board toward -Y', 0, -3.5, 'F.Fab', 0.7, 0.1))
items.append(fp_text('1=GND 2=+ 3=SW 4=DT 5=CLK', 0, 2.8, 'F.Fab', 0.7, 0.1))
items.append(fp_text('${REFERENCE}', 0, -9.5, 'F.Fab', 0.8, 0.12))
items.append(model(MODEL + 'KY-040_Module.wrl'))                  # built by tools/build_models.py in this frame
write_fp('KY-040_Module_RA_Header', footprint(
    'KY-040_Module_RA_Header',
    'Carrier footprint for a KY-040 encoder module with its 5-pin right-angle header: 1x5 2.54 mm through-holes. '
    'The module PCB (approx. 26 x 19 mm) stands perpendicular to this board on the -Y side.',
    'ky-040 encoder module', 'through_hole', items, -11, 4.5))

# --- Waveshare-style RP2040-Zero -------------------------------------------
rpz_edge_left = ['5V', 'GND', '3V3', 'GP29/ADC3', 'GP28/ADC2', 'GP27/ADC1', 'GP26/ADC0', 'GP15', 'GP14']
rpz_bottom = ['GP13', 'GP12', 'GP11', 'GP10', 'GP9']
rpz_edge_right = ['GP8', 'GP7', 'GP6', 'GP5', 'GP4', 'GP3', 'GP2', 'GP1', 'GP0']   # bottom to top
rpz_back = ['GND', 'GP25', 'GP24', 'GP23', 'GP22', 'GP21', 'GP20', 'GP19', 'GP18', 'GP17']
def rpz_type(n):
    return {'5V': 'passive', 'GND': 'power_in', '3V3': 'power_out'}.get(n, 'bidirectional')
nums = {}
k = 1
for n in rpz_edge_left + rpz_bottom + rpz_edge_right + rpz_back:
    nums.setdefault(n, []).append(k); k += 1
sym_left = [(str(nums[n][0]), n, rpz_type(n)) for n in rpz_edge_left] + [None] + \
           [(str(nums[n][0]), n, rpz_type(n)) for n in rpz_bottom]
right_names = ['GP0', 'GP1', 'GP2', 'GP3', 'GP4', 'GP5', 'GP6', 'GP7', 'GP8'] + [None] + \
              ['GP17', 'GP18', 'GP19', 'GP20', 'GP21', 'GP22', 'GP23', 'GP24', 'GP25', 'GND']
sym_right = []
for n in right_names:
    if n is None:
        sym_right.append(None)
    elif n == 'GND':
        sym_right.append(('24', 'GND (back)', 'power_in'))
    else:
        sym_right.append((str(nums[n][0]), n + (' (back)' if n in rpz_back else ''), rpz_type(n)))
symbols.append(box_symbol(
    'RP2040-Zero', 'U', sym_left, sym_right,
    f'{LIBNAME}:RP2040-Zero', 'https://www.waveshare.com/wiki/RP2040-Zero',
    'RP2040-Zero form factor (Waveshare and clones such as QIQIAZI): RP2040, 4 MB flash, USB-C, WS2812 on GP16, '
    '18 x 23.5 mm. Pins 1-23 on the castellated edge (left column 1-9 top-down, bottom row 10-14 left-right, '
    'right column 15-23 bottom-up); pins 24-33 are the back-side solder pads (GND, GP25..GP17).',
    'rp2040 zero waveshare', 'RP2040-Zero*'))
items = []
for layer in ('F.Fab', 'F.SilkS'):
    items.append(fp_rect(-9, -11.75, 9, 11.75, layer, 0.1 if layer == 'F.Fab' else 0.12))
items.append(fp_rect(-9.25, -12.75, 9.25, 12.0, 'F.CrtYd', 0.05))
items.append(fp_rect(-4.5, -12.5, 4.5, -5.0, 'F.Fab', 0.1))         # USB-C
k = 1
for i, n in enumerate(rpz_edge_left):
    items.append(pad_tht(k, -7.62, -10.16 + 2.54 * i, 1.7, 1.0, 'rect' if k == 1 else 'oval')); k += 1
for i, n in enumerate(rpz_bottom):
    items.append(pad_tht(k, -5.08 + 2.54 * i, 10.16, 1.7, 1.0, 'oval')); k += 1
for i, n in enumerate(rpz_edge_right):
    items.append(pad_tht(k, 7.62, 10.16 - 2.54 * i, 1.7, 1.0, 'oval')); k += 1
for i, n in enumerate(rpz_back):
    items.append(pad_smd(k, -5.08, -9.0 + 2.0 * i, 1.6, 1.2, 'B.Cu')); k += 1
items.append(fp_text('1=5V', -7.62, -12.4, 'F.Fab', 0.6, 0.1))
items.append(fp_text('back pads 24-33 approx.', 0, 0, 'F.Fab', 0.7, 0.1))
items.append(fp_text('${REFERENCE}', 0, 3, 'F.Fab', 0.8, 0.12))
write_fp('RP2040-Zero', footprint(
    'RP2040-Zero',
    'Waveshare RP2040-Zero outline 18 x 23.5 mm (R1 corners), 23 castellated edge pins at 2.54 mm pitch, side '
    'columns 15.24 mm apart starting 1.59 mm below the top edge, bottom row ending 3.92 mm from the right edge '
    '(Waveshare dimension drawing). Back-side pads 24-33 (GND, GP25..GP17) are placed from a photo: approximate.',
    'rp2040 zero waveshare', 'through_hole', items, -14, 14))

# --- ESP32-S3-DevKitC-1 (Espressif library, CC-BY-SA 4.0) ------------------
symbols.append(vendored_symbol(
    os.path.join(VENDOR, 'espressif', 'ESP32-S3-DevKitC.kicad_sym'), 'ESP32-S3-DevKitC', 'ESP32-S3-DevKitC-1',
    f'{LIBNAME}:ESP32-S3-DevKitC-1',
    'https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s3/esp32-s3-devkitc-1/user_guide.html',
    'ESP32-S3-DevKitC-1 and pin-compatible clones (e.g. "Gold Edition" N16R8: 16 MB flash, 8 MB octal PSRAM, '
    'CH340K + native USB-C, WS2812 on GPIO48). 2 x 22 pins, rows 22.86 mm apart. Symbol/footprint from '
    'espressif/kicad-libraries (CC-BY-SA 4.0).', 'esp32-s3 devkitc espressif'))
vendored_footprint(os.path.join(VENDOR, 'espressif', 'ESP32-S3-DevKitC.kicad_mod'), 'ESP32-S3-DevKitC-1',
                   'ESP32-S3-DevKitC-1: 2 x 22 through-holes at 2.54 mm, rows 22.86 mm apart; pad 1 (3V3) at origin, '
                   'pad 44 (GND) at the top of the other row. From espressif/kicad-libraries (CC-BY-SA 4.0).',
                   'esp32-s3 devkitc')

# --- Lonely Binary TK103 PCM5102A I2S DAC ----------------------------------
tk_left = [('2', '3V3', 'power_in'), ('3', 'BCK', 'input'), ('4', 'DIN', 'input'), ('5', 'LRCK', 'input'),
           ('1', 'GND', 'power_in')]
tk_right = [('6', 'XSMT', 'input')]
symbols.append(box_symbol(
    'TK103_PCM5102A_I2S_DAC', 'U', tk_left, tk_right,
    f'{LIBNAME}:TK103_Module_RA_Header', 'https://www.ti.com/lit/ds/symlink/pcm5102a.pdf',
    'Lonely Binary TK103: TI PCM5102A stereo DAC, I2S in (BCK, DIN, LRCK; PLL from BCK, no MCLK needed), '
    '3.5 mm line-level jack (2.1 V RMS), 3.3 V supply only, XSMT pulled high by 10 k on board (drive low to mute). '
    '22.4 x 30.4 mm, 6-pin right-angle header.', 'pcm5102a i2s dac audio', 'TK103*'))
items = []
for i in range(6):
    items.append(pad_tht(i + 1, -6.35 + 2.54 * i, 0, shape='rect' if i == 0 else 'circle'))
items.append(fp_rect(-7.62, -1.27, 7.62, 1.27, 'F.SilkS'))
items.append(fp_rect(-11.2, -5.0, 11.2, -3.4, 'F.Fab', 0.1))       # module PCB edge-on (22.4 wide), from the STEP
items.append(fp_rect(-11.5, -8.0, 11.5, 1.5, 'F.CrtYd', 0.05))
items.append(fp_text('TK103 stands vertical, board toward -Y', 0, -3.5, 'F.Fab', 0.7, 0.1))
items.append(fp_text('1=GND 2=3V3 3=BCK 4=DIN 5=LRCK 6=XSMT', 0, 2.8, 'F.Fab', 0.7, 0.1))
items.append(fp_text('${REFERENCE}', 0, -9.5, 'F.Fab', 0.8, 0.12))
# STEP: board centre (45.14, -16.52), header holes at y=-26.32, pins extend to y=-33.57 along -Y, board z 0..1.6.
# Stand it up (verified with kicad-cli pcb render): pins point into the carrier, board 3.4-5 mm on the -Y side.
items.append(model(MODEL + 'TK103_PCM5102A.step', offset=(-45.14, 5.0, 31.71), rotate=(-90, 0, 0)))
write_fp('TK103_Module_RA_Header', footprint(
    'TK103_Module_RA_Header',
    'Carrier footprint for the Lonely Binary TK103 PCM5102A DAC with its 6-pin right-angle header: 1x6 2.54 mm '
    'through-holes, pin 1 = GND. Module pins at 2.54 mm pitch centred on the 22.4 mm board, 5.39 mm above its bottom '
    'edge (from the vendor STEP). The module stands perpendicular to this board on the -Y side.',
    'pcm5102a tk103 dac', 'through_hole', items, -11, 4.5))

# --- MIDI shield (Arduino UNO form factor, marking K194725ASJH) -------------
# Pin numbers follow the stock KiCad Arduino_UNO_R3 symbol/footprint so the shield mates with Module:Arduino_UNO_R3.
midi_left = [('15', 'D0/RX<-MIDI_IN', 'output'), ('16', 'D1/TX->MIDI_OUT', 'input'),
             ('17', 'D2', 'passive'), ('18', 'D3', 'passive'), ('19', 'D4', 'passive'), ('20', 'D5', 'passive'),
             ('21', 'D6', 'passive'), ('22', 'D7', 'passive'), ('23', 'D8', 'passive'), ('24', 'D9', 'passive'),
             ('25', 'D10', 'passive'), ('26', 'D11', 'passive'), ('27', 'D12', 'passive'), ('28', 'D13', 'passive'),
             None, ('5', '+5V', 'power_in'), ('4', '3V3', 'passive'), ('8', 'VIN', 'passive'),
             ('6', 'GND', 'power_in'), ('7', 'GND', 'power_in'), ('29', 'GND', 'power_in')]
midi_right = [('3', '~{RESET}', 'passive'), ('2', 'IOREF', 'passive'), ('30', 'AREF', 'passive'),
              ('9', 'A0', 'passive'), ('10', 'A1', 'passive'), ('11', 'A2', 'passive'), ('12', 'A3', 'passive'),
              ('13', 'SDA/A4', 'passive'), ('14', 'SCL/A5', 'passive'), ('31', 'SDA', 'passive'),
              ('32', 'SCL', 'passive'), ('1', 'NC', 'no_connect')]
symbols.append(box_symbol(
    'MIDI_Shield_DIN5x3_6N138', 'A', midi_left, midi_right,
    'Module:Arduino_UNO_R3_WithMountingHoles', '',
    'Arduino UNO shield with MIDI IN (6N138 optocoupler to D0/RX, ON/OFF switch disconnects it for uploads), '
    'MIDI OUT (D1/TX) and MIDI THRU, three 5-pin DIN jacks, reset button, prototyping rows. Board marking '
    'K194725ASJH. Pin numbers match the KiCad Arduino_UNO_R3 footprint. 31250 baud.',
    'midi shield arduino uno din 6n138', 'Arduino*UNO*R3*'))

# --- ElectroCookie full-size solderable breadboard PCB ---------------------
items = []
BW, BH = 172.72, 52.07
items.append(fp_rect(-BW / 2, -BH / 2, BW / 2, BH / 2, 'F.Fab', 0.1))
items.append(fp_rect(-BW / 2 - 0.25, -BH / 2 - 0.25, BW / 2 + 0.25, BH / 2 + 0.25, 'F.CrtYd', 0.05))
rows_top = {'J': -13.97, 'I': -11.43, 'H': -8.89, 'G': -6.35, 'F': -3.81}
rows_bot = {'E': 3.81, 'D': 6.35, 'C': 8.89, 'B': 11.43, 'A': 13.97}
x0 = -78.74
RAILS = (('T-', -22.86), ('T+', -20.32), ('B+', 20.32), ('B-', 22.86))
TW = 1.3                                                      # back-side strip trace width (nearly pad width, as on the board)
for col in range(1, 64):
    x = x0 + 2.54 * (col - 1)
    for letter, y in list(rows_top.items()) + list(rows_bot.items()):
        strip = ('R' if letter in rows_top else 'L') + str(col)      # holes A-E of a row are one strip (L), F-J another (R)
        items.append(pad_tht(strip, x, y, 1.6, 1.0, 'rect' if letter in 'AJ' and col == 1 else 'circle'))
    for layer in ('B.Cu', 'B.Mask'):                                  # strip traces on the back, exposed/tinned as on the real board
        items.append(fp_line(x, -13.97, x, -3.81, layer, TW))
        items.append(fp_line(x, 3.81, x, 13.97, layer, TW))
    if col == 1 or col % 5 == 0:
        for y in (-16.51, 16.51):
            items.append(fp_text(str(col), x, y, 'F.SilkS', 0.8, 0.12))
for letter, y in list(rows_top.items()) + list(rows_bot.items()):
    for x in (x0 - 2.54, -x0 + 2.54):
        items.append(fp_text(letter, x, y, 'F.SilkS', 0.8, 0.12))
for x, lbl in ((x0 - 3.5, '-'), (-x0 + 3.5, '-')):
    items.append(fp_text(lbl, x, -22.86, 'F.SilkS', 1.0, 0.15))
    items.append(fp_text(lbl, x, 22.86, 'F.SilkS', 1.0, 0.15))
    items.append(fp_text('+', x, -20.32, 'F.SilkS', 1.0, 0.15))
    items.append(fp_text('+', x, 20.32, 'F.SilkS', 1.0, 0.15))
xr0, xr1 = x0 - 2.54, x0 + 2.54 * 63                          # rails run from column 0 to column 64
for col in range(0, 65):
    x = x0 + 2.54 * (col - 1)
    for num, y in RAILS:
        items.append(pad_tht(num, x, y, 1.6, 1.0, 'circle'))
for num, y in RAILS:
    for layer in ('B.Cu', 'B.Mask'):
        items.append(fp_line(xr0, y, xr1, y, layer, TW))
# End jumpers (two pads bridged with solder): the left end joins the outer (-) rails, the right end the inner (+) rails.
for sx, y_rail, num_t, num_b in ((-1, -22.86, 'T-', 'B-'), (1, -20.32, 'T+', 'B+')):
    xe, xj = sx * 84.5, sx * 83.82
    items.append(pad_tht(num_t, xj, -1.27, 1.8, 1.0, 'circle'))
    items.append(pad_tht(num_b, xj, 1.27, 1.8, 1.0, 'circle'))
    for sgn, num in ((-1, num_t), (1, num_b)):
        xr = xr0 if sx < 0 else xr1
        for layer in ('B.Cu', 'B.Mask'):
            items.append(fp_line(xr, sgn * abs(y_rail), xe, sgn * abs(y_rail), layer, TW))
            items.append(fp_line(xe, sgn * abs(y_rail), xe, sgn * 3.0, layer, TW))
            items.append(fp_line(xe, sgn * 3.0, xj, sgn * 1.27, layer, TW))
    items.append(fp_text('rail jumper', sx * 83.82, -3.6 if False else 4.2, 'F.SilkS', 0.6, 0.1))
for x in (-78.74, 0, 78.74):
    items.append(pad_npth(x, 0, 3.2))
    items.append(fp_circle(x, 0, 2.8, 'F.Fab', 0.1))
for x in (-81.28, 81.28):
    for y in (-17.78, 17.78):
        items.append(pad_npth(x, y, 2.2))
items.append(fp_text('ElectroCookie full-size breadboard PCB 172.7 x 52.1 (rows A-E / F-J, 1-63; rails T/B)', 0, 0 - 1.5, 'F.Fab', 1.2, 0.15))
items.append(fp_text('${REFERENCE}', 0, 1.5, 'F.Fab'))
write_fp('ElectroCookie_Breadboard_Full', footprint(
    'ElectroCookie_Breadboard_Full',
    'ElectroCookie full-size solderable breadboard PCB (172.7 x 52.1 mm). 2 x 5 x 63 strip holes at 2.54 mm, '
    'strip rows 7.62 mm across the centre gap, two power rails per side, M3 centre holes at 0 and +/-78.74, M2 '
    'corner holes at (+/-81.28, +/-17.78). Each 5-hole strip is one pad number: L<row> for holes A-E, R<row> for F-J; '
    'rail pads share the names T-/T+/B+/B-. Back-side copper reproduces the strip and rail traces; the two-pad solder '
    'jumpers at each end join the outer (-) rails (left end) and inner (+) rails (right end). '
    'Outline and holes from the ElectroCookie dimension drawing; rail length and jumper positions from photos.',
    'electrocookie breadboard protoboard', 'through_hole', items, -25.5, 25.5, jumpers=True))

# ---------------------------------------------------------------- write sym
os.makedirs(LIB, exist_ok=True)
with open(os.path.join(LIB, LIBNAME + '.kicad_sym'), 'w') as fh:
    fh.write('(kicad_symbol_lib (version 20241209) (generator "tbd-kicad") (generator_version "9.0")\n')
    for s in symbols:
        fh.write('\t' + s.replace('\n', '\n\t') + '\n')
    fh.write(')\n')
print('symbols:', len(symbols))
print('footprints:', sorted(os.listdir(PRETTY)))
