"""Generate projects/midi-shield: the K194725ASJH Arduino UNO MIDI shield (3 x DIN-5, 6N138) redrawn as a KiCad
project: schematic, layout and (via kicad-cli) a STEP model. Geometry and nets in tools/midi_geometry.py.
Run: python3 tools/gen_midi_shield.py"""
import os, sys, json, copy, uuid, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import midi_geometry as MG
from sexp import parse, dump, find, find1, Str
import pcbnew

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(ROOT, 'lib')
PROJ = os.path.join(ROOT, 'projects', 'midi-shield')
NAME = 'midi-shield'
STOCK_SYM = '/usr/share/kicad/symbols/'
STOCK_FP = '/usr/share/kicad/footprints/'
os.makedirs(PROJ, exist_ok=True)


def f(x):
    s = ('%.4f' % x).rstrip('0').rstrip('.')
    return '0' if s in ('-0', '', '-') else s


def U():
    return str(uuid.uuid4())


ROOT_UUID = U()
# ------------------------------------------------------------------ schematic
_libs = {}


def lib_symbol(lib, name):
    if lib not in _libs:
        _libs[lib] = parse(open(STOCK_SYM + lib + '.kicad_sym').read())[0]
    return [s for s in find(_libs[lib], 'symbol') if s[1] == name][0]


def pins_of(sym):
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


def sym_instance(lib_id, ref, value, x, y, sym, footprint):
    rx, ry = prop_pos(sym, 'Reference'); vx, vy = prop_pos(sym, 'Value')
    props = [f'(property "Reference" "{ref}" (at {f(x + rx)} {f(y - ry)} 0) (effects (font (size 1.27 1.27)) (justify left)))',
             f'(property "Value" "{value}" (at {f(x + vx)} {f(y - vy)} 0) (effects (font (size 1.27 1.27)) (justify left)))',
             f'(property "Footprint" "{footprint}" (at {f(x)} {f(y)} 0) (effects (font (size 1.27 1.27)) (hide yes)))',
             f'(property "Datasheet" "" (at {f(x)} {f(y)} 0) (effects (font (size 1.27 1.27)) (hide yes)))',
             f'(property "Description" "" (at {f(x)} {f(y)} 0) (effects (font (size 1.27 1.27)) (hide yes)))']
    pins = ' '.join(f'(pin "{n}" (uuid "{U()}"))' for n in pins_of(sym))
    return (f'(symbol (lib_id "{lib_id}") (at {f(x)} {f(y)} 0) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid "{U()}")\n\t'
            + '\n\t'.join(props) + f'\n\t{pins}\n\t(instances (project "{NAME}" (path "/{ROOT_UUID}" (reference "{ref}") (unit 1)))))')


def wire(x1, y1, x2, y2):
    return f'(wire (pts (xy {f(x1)} {f(y1)}) (xy {f(x2)} {f(y2)})) (stroke (width 0) (type default)) (uuid "{U()}"))'


def label(name, x, y, rot):
    just = 'left bottom' if rot == 0 else 'right bottom'
    return f'(label "{name}" (at {f(x)} {f(y)} {rot}) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify {just})) (uuid "{U()}"))'


def no_connect(x, y):
    return f'(no_connect (at {f(x)} {f(y)}) (uuid "{U()}"))'


sch, lib_symbols, embedded = [], [], set()


def embed(lib, name):
    if (lib, name) in embedded:
        return
    sym = lib_symbol(lib, name)
    ext = find1(sym, 'extends')
    if ext:
        embed(lib, ext[1])
    s = copy.deepcopy(sym); s[1] = Str(f'{lib}:{name}')
    if ext:
        for i, n in enumerate(s):
            if isinstance(n, list) and n[0] == 'extends':
                s[i] = ['extends', Str(f'{lib}:{ext[1]}')]
    lib_symbols.append(s); embedded.add((lib, name))


def place(ref, lib, name, value, x, y, footprint, nets):
    embed(lib, name)
    sym = lib_symbol(lib, name)
    sch.append(sym_instance(f'{lib}:{name}', ref, value, x, y, sym, footprint))
    for num, (pname, px, py, prot) in pins_of(sym).items():
        sx, sy = x + px, y - py
        net = nets.get(num)
        if net is None:
            sch.append(no_connect(sx, sy)); continue
        if prot in (0, 180):
            dx = -1 if prot == 0 else 1
            ex = sx + dx * 7.62
            sch.append(wire(sx, sy, ex, sy)); sch.append(label(net, ex, sy, 0 if dx > 0 else 180))
        else:
            dy = 1 if prot == 90 else -1
            ey = sy + dy * 3.81
            sch.append(wire(sx, sy, sx, ey)); sch.append(wire(sx, ey, sx + 5.08, ey)); sch.append(label(net, sx + 5.08, ey, 0))


PARTSYM = {'U1': ('Isolator', '6N138'), 'D1': ('Device', 'D'), 'S1': ('Switch', 'SW_Push'), 'S2': ('Switch', 'SW_SPDT')}
SCH_AT = {'COM1': (35.56, 58.42), 'R2': (71.12, 48.26), 'D1': (83.82, 60.96), 'U1': (111.76, 63.5), 'R6': (138.43, 45.72), 'S2': (160.02, 63.5),
          'R1': (121.92, 99.06), 'R5': (138.43, 99.06), 'COM3': (175.26, 101.6), 'R3': (71.12, 134.62), 'R4': (83.82, 134.62), 'COM2': (111.76, 134.62),
          'S1': (38.1, 134.62), 'J1': (228.6, 50.8), 'J2': (228.6, 86.36), 'J3': (266.7, 58.42), 'J4': (266.7, 101.6)}
for ref, lib, fpname, value, pos, rot, nets in MG.PARTS:
    slib, sname = PARTSYM.get(ref, ('Device', 'R'))
    place(ref, slib, sname, value, *SCH_AT[ref], f'{lib}:{fpname}', nets)
for ref, prefix, pos, rot in MG.SOCKETS:
    nets = dict(MG.SOCKET_NETS[prefix]); nets.setdefault('1', None); nets.setdefault('3', None)
    place(ref, 'Connector', 'DIN-5_180degree', f'MIDI {prefix}', *SCH_AT[ref], 'tbd:DIN-5_180deg_PCB_Socket', nets)
HDR_NETS = {'3V3': None, 'VIN': None, 'AREF': None, '5V': '+5V', 'GND': 'GND', 'RESET': 'RESET', 'TX': 'TX', 'RX': 'RX'}
HDR_NETS.update({n: n for n in ['A%d' % i for i in range(6)] + ['D%d' % i for i in range(2, 14)]})   # broken out to the proto rows
for ref, fpname, pos, names in MG.HEADERS:
    n = len(names)
    place(ref, 'Connector_Generic', f'Conn_01x{n:02d}', {'J1': 'UNO power', 'J2': 'UNO analog', 'J3': 'UNO digital 8-13 GND AREF', 'J4': 'UNO digital 0-7'}[ref],
          *SCH_AT[ref], f'Connector_PinHeader_2.54mm:{fpname}', {str(i + 1): HDR_NETS[nm] for i, nm in enumerate(names)})
for i, (ref, x, y, pnets) in enumerate(MG.PROTO_ROWS):
    place(ref, 'Connector_Generic', 'Conn_01x06', ' '.join(pnets) if pnets else 'proto', 190.5 + 12.7 * i, 147.32,
          'Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical', {str(k + 1): n for k, n in enumerate(pnets)} if pnets else {})
NOTES = [
    'Arduino UNO MIDI shield, board marking K194725ASJH 1983-M1, redrawn from the board.',
    'IN: DIN pin 4 -> R2 220 -> 6N138 anode, pin 5 -> cathode, D1 reverse-protects the LED; R6 pulls the open-collector output up to 5 V.',
    'S2 connects the opto output to RX (D0) so the UNO can still be programmed with S2 off. THRU repeats the opto output through R5/R1.',
    'OUT: TX -> R3 220 -> DIN pin 5, 5 V -> R4 220 -> DIN pin 4. S1 resets the UNO. Proto rows: P4 = D2-D7, P5 = D8-D13, P6 = A0-A5 (wired on the back), P7-P10 free holes.',
    'Resistor roles R1/R5/R6 and the 6N138 pin 7 (left open) are read from silkscreen placement and the usual circuit; verify with a meter.',
]
sch.append('(text "%s" (at 20.32 180 0) (effects (font (size 1.778 1.778)) (justify left bottom)) (uuid "%s"))'
           % ('\\n'.join(NOTES).replace('"', '\\"'), U()))
sch_text = ['(kicad_sch (version 20250114) (generator "eeschema") (generator_version "9.0") (uuid "%s") (paper "A4")' % ROOT_UUID,
            '\t(title_block (title "Arduino UNO MIDI shield K194725ASJH (3 x DIN-5, 6N138)") (date "2026-11-10") (rev "1")'
            ' (comment 1 "Generated by tools/gen_midi_shield.py"))', '\t(lib_symbols']
for s in lib_symbols:
    sch_text.append('\t\t' + dump(s, 2))
sch_text.append('\t)')
for item in sch:
    sch_text.append('\t' + item.replace('\n', '\n\t'))
sch_text += ['\t(sheet_instances (path "/" (page "1")))', '\t(embedded_fonts no)', ')']
open(os.path.join(PROJ, NAME + '.kicad_sch'), 'w').write('\n'.join(sch_text) + '\n')

# ------------------------------------------------------------------ PCB
mm = pcbnew.FromMM
OX, OY = 100.0, 100.0                                   # power pin 1 on the sheet
PCB = os.path.join(PROJ, NAME + '.kicad_pcb')
board = pcbnew.NewBoard(PCB)
board.GetDesignSettings().m_CopperEdgeClearance = mm(0.25)
nets = {}


def net(name):
    if name not in nets:
        n = pcbnew.NETINFO_ITEM(board, name); board.Add(n); nets[name] = n
    return nets[name]


def P(x, y):
    return pcbnew.VECTOR2I(mm(OX + x), mm(OY + y))


def add_fp(path, name, ref, value, nick, back=False):
    fp = pcbnew.FootprintLoad(path, name)
    fp.SetFPID(pcbnew.LIB_ID(nick, name)); fp.SetReference(ref); fp.SetValue(value)
    board.Add(fp)
    if back:
        fp.Flip(P(0, 0), False)
    return fp


def pad_at(fp, num, x, y, rot=0):
    fp.SetOrientationDegrees(rot)
    p = fp.FindPadByNumber(str(num)).GetPosition(); t = P(x, y)
    fp.Move(pcbnew.VECTOR2I(t.x - p.x, t.y - p.y))


def orient(fp, num_a, num_b, x, y, direction):
    """Place pad num_a at (x, y) with the rotation that sends pad num_b in the given unit direction (dx, dy)."""
    best = None
    for rot in (0, 90, 180, 270):
        pad_at(fp, num_a, x, y, rot)
        a = fp.FindPadByNumber(str(num_a)).GetPosition(); b = fp.FindPadByNumber(str(num_b)).GetPosition()
        dx, dy = b.x - a.x, b.y - a.y
        score = dx * direction[0] + dy * direction[1]
        if best is None or score > best[0]:
            best = (score, rot)
    pad_at(fp, num_a, x, y, best[1])


def centre_at(fp, x, y, rot=0):
    fp.SetOrientationDegrees(rot)
    bb = fp.GetBoundingBox(False, False); c = bb.GetCenter(); t = P(x, y)
    fp.Move(pcbnew.VECTOR2I(t.x - c.x, t.y - c.y))


def set_nets(fp, padnets):
    for pad in fp.Pads():
        n = padnets.get(pad.GetNumber())
        if n:
            pad.SetNet(net(n))


# outline
B = MG.BOARD; R = B['corner']
k = 1 - math.sqrt(0.5)
for (x1, y1), (x2, y2) in (((B['x0'] + R, B['y0']), (B['x1'] - R, B['y0'])), ((B['x1'], B['y0'] + R), (B['x1'], B['y1'] - R)),
                           ((B['x1'] - R, B['y1']), (B['x0'] + R, B['y1'])), ((B['x0'], B['y1'] - R), (B['x0'], B['y0'] + R))):
    s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT); s.SetStart(P(x1, y1)); s.SetEnd(P(x2, y2)); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.1)); board.Add(s)
for cx, cy, sx, sy in ((B['x1'], B['y0'], 1, -1), (B['x1'], B['y1'], 1, 1), (B['x0'], B['y1'], -1, 1), (B['x0'], B['y0'], -1, -1)):
    s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_ARC)
    a = P(cx - sx * R, cy) if sx * sy < 0 else P(cx, cy - sy * R)
    b = P(cx, cy - sy * R) if sx * sy < 0 else P(cx - sx * R, cy)
    s.SetArcGeometry(a, P(cx - sx * R * k, cy - sy * R * k), b); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.1)); board.Add(s)

# UNO headers on the back (pins point down into the UNO), proto rows on the front without bodies
for ref, fpname, (x, y), names in MG.HEADERS:
    fp = add_fp(STOCK_FP + 'Connector_PinHeader_2.54mm.pretty', fpname, ref, 'UNO ' + names[0] + '..' + names[-1], 'Connector_PinHeader_2.54mm', back=True)
    orient(fp, 1, 2, x, y, (1, 0))                        # pins run toward +X whatever the flip does to the rotation
    set_nets(fp, {str(i + 1): HDR_NETS[nm] for i, nm in enumerate(names)})
    fp.Reference().SetVisible(False)
for ref, x, y, pnets in MG.PROTO_ROWS:
    fp = add_fp(STOCK_FP + 'Connector_PinHeader_2.54mm.pretty', 'PinHeader_1x06_P2.54mm_Vertical', ref, 'proto', 'Connector_PinHeader_2.54mm')
    orient(fp, 1, 2, x, y, (0, 1)); fp.Models().clear()   # rows run toward +Y (from the digital edge toward the power edge)
    fp.Reference().SetVisible(False)
    if pnets:
        set_nets(fp, {str(k + 1): n for k, n in enumerate(pnets)})
for ref, lib, fpname, value, (x, y), rot, padnets in MG.PARTS:
    path = os.path.join(LIB, 'tbd.pretty') if lib == 'tbd' else STOCK_FP + lib + '.pretty'
    fp = add_fp(path, fpname, ref, value, lib)
    if ref == 'U1':
        pad_at(fp, 1, x, y, rot)
    elif ref == 'S2':
        pad_at(fp, 2, x, y, rot)
    else:
        centre_at(fp, x, y, rot)
    set_nets(fp, padnets)
for ref, prefix, (x, y), rot in MG.SOCKETS:
    fp = add_fp(os.path.join(LIB, 'tbd.pretty'), 'DIN-5_180deg_PCB_Socket', ref, f'MIDI {prefix}', 'tbd')
    pad_at(fp, 2, x, y, rot); set_nets(fp, MG.SOCKET_NETS[prefix])
# routing: Freerouting's result is kept as midi-shield.ses next to the board and re-imported on every regeneration
# (KiCad's MCP autoroute tool or Freerouting itself, via the Specctra DSN export, produces it)
SES = os.path.join(PROJ, NAME + '.ses')
if os.path.exists(SES):
    pcbnew.ImportSpecctraSES(board, SES)
t = pcbnew.PCB_TEXT(board); t.SetText('K194725ASJH MIDI shield\nredrawn in KiCad - tbd-kicad'); t.SetPosition(P(23, -3.6)); t.SetLayer(pcbnew.B_SilkS)
t.SetTextSize(pcbnew.VECTOR2I(mm(0.9), mm(0.9))); t.SetMirrored(True); board.Add(t)
board.Save(PCB)
pro = {"board": {"design_settings": {"defaults": {}, "rules": {"min_clearance": 0.15, "min_track_width": 0.2, "min_copper_edge_clearance": 0.25}}, "layer_presets": [], "viewports": []},
       "boards": [], "cvpcb": {"equivalence_files": []}, "libraries": {"pinned_footprint_libs": ["tbd"], "pinned_symbol_libs": ["tbd"]},
       "meta": {"filename": NAME + ".kicad_pro", "version": 3},
       "net_settings": {"classes": [{"name": "Default", "clearance": 0.2, "track_width": 0.4, "via_diameter": 0.8, "via_drill": 0.4,
                                     "diff_pair_width": 0.2, "diff_pair_gap": 0.25}], "meta": {"version": 4}},
       "pcbnew": {"page_layout_descr_file": ""}, "schematic": {"legacy_lib_dir": "", "legacy_lib_list": []},
       "sheets": [[ROOT_UUID, "Root"]], "text_variables": {}}
json.dump(pro, open(os.path.join(PROJ, NAME + '.kicad_pro'), 'w'), indent=2)
open(os.path.join(PROJ, 'sym-lib-table'), 'w').write('(sym_lib_table (version 7)\n  (lib (name "tbd")(type "KiCad")(uri "${KIPRJMOD}/../../lib/tbd.kicad_sym")(options "")(descr "tbd-kicad"))\n)\n')
open(os.path.join(PROJ, 'fp-lib-table'), 'w').write('(fp_lib_table (version 7)\n  (lib (name "tbd")(type "KiCad")(uri "${KIPRJMOD}/../../lib/tbd.pretty")(options "")(descr "tbd-kicad"))\n)\n')
print('nets:', len(nets), 'footprints:', len(board.GetFootprints()))
print('wrote', PROJ)
