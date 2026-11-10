"""Generate projects/psb-1: the ProtoSupplies PSB-1 MCU proto board redrawn as a KiCad project.
  psb-1.kicad_sch        DC-input circuit (jack, JST, filter caps, LED, VIN/V jumper) and the two header blocks
  psb-1.kicad_pcb        the board with the component kit fitted
  psb-1-bare.kicad_pcb   the same board as sold: kit parts marked DNP, no bodies
Geometry comes from tools/psb1_geometry.py; the prototyping grid is the library footprint ProtoSupplies_PSB-1_Grid,
the headers are PSB-1_Header_* footprints and the kit parts are stock KiCad footprints. Run: python3 tools/gen_psb1.py"""
import os, sys, json, copy, uuid, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import psb1_geometry as PG
from sexp import parse, dump, find, find1, Str
import pcbnew

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(ROOT, 'lib')
PROJ = os.path.join(ROOT, 'projects', 'psb-1')
NAME = 'psb-1'
STOCK_SYM = '/usr/share/kicad/symbols/'
STOCK_FP = '/usr/share/kicad/footprints/'
os.makedirs(PROJ, exist_ok=True)


def f(x):
    s = ('%.4f' % x).rstrip('0').rstrip('.')
    return '0' if s in ('-0', '', '-') else s


def U():
    return str(uuid.uuid4())


ROOT_UUID = U()
VNET = PG.v_net_of_col(10)

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
    """Symbol at (x, y) with a stub wire and net label on every pin (or a no-connect when nets maps it to None)."""
    embed(lib, name)
    sym = lib_symbol(lib, name)
    sch.append(sym_instance(f'{lib}:{name}', ref, value, x, y, sym, footprint))
    for num, (pname, px, py, prot) in pins_of(sym).items():
        sx, sy = x + px, y - py
        net = nets.get(num)
        if net is None:
            sch.append(no_connect(sx, sy)); continue
        if prot in (0, 180):                      # horizontal pin: stub away from the body, label at its end
            dx = -1 if prot == 0 else 1
            ex = sx + dx * 7.62
            sch.append(wire(sx, sy, ex, sy)); sch.append(label(net, ex, sy, 0 if dx > 0 else 180))
        else:                                     # vertical pin: stub up/down, then a jog to the right for the label
            dy = 1 if prot == 90 else -1
            ey = sy + dy * 3.81
            sch.append(wire(sx, sy, sx, ey)); sch.append(wire(sx, ey, sx + 5.08, ey)); sch.append(label(net, sx + 5.08, ey, 0))


KITSYM = {k[0]: k for k in PG.KIT}
PLACE = {'P1': (45.72, 69.85), 'J1': (45.72, 110.49), 'C1': (95.25, 80.01), 'C2': (120.65, 80.01), 'R1': (149.86, 64.77),
         'D1': (149.86, 100.33), 'JP1': (195.58, 80.01)}                       # multiples of 1.27 mm keep pins on the grid
for ref, (x, y) in PLACE.items():
    _, lib, fpname, _, _, value, symlib, sym, nets = KITSYM[ref]
    place(ref, symlib, sym, value, x, y, f'{lib}:{fpname}', nets)
place('J2', 'Connector_Generic', 'Conn_02x20_Odd_Even', 'MCU header 2x20', 240.03, 110.49, 'tbd:PSB-1_Header_2x20_Breakout', {})
place('J3', 'Connector_Generic', 'Conn_02x10_Odd_Even', 'staggered 2x10', 275.59, 69.85, 'tbd:PSB-1_Header_2x10_Staggered_Breakout', {})
NOTES = [
    'ProtoSupplies PSB-1 MCU proto board, redrawn from the vendor drawing, CAD renders and the board itself.',
    'DC input: P1 barrel jack (centre +), J1 JST XH, C1 100 uF, C2 100 nF, R1 1 k + LED power indicator.',
    'JP1 bridges VIN to the V bus of the column-10 group with two shunts (vendor: "VIN/V jumper").',
    'The prototyping grid (V/G bus column pairs, G band, V band segments, 3- and 6-hole strips, VIN column) and the',
    'header breakout pads are PCB-only footprints: ProtoSupplies_PSB-1_Grid, PSB-1_Header_2x20_Breakout, PSB-1_Header_2x10_Staggered_Breakout.',
    ('All seven V columns are one net (V).' if PG.V_COMMON else
     'The seven V band segments are drawn as separate copper (V1..V7, the jumper feeds V3); set V_COMMON in tools/psb1_geometry.py if a meter says they are joined.'),
    'J2 and J3 are the MCU header holes; nothing is connected to them on the bare board.',
]
sch.append('(text "%s" (at 20.32 150 0) (effects (font (size 1.778 1.778)) (justify left bottom)) (uuid "%s"))'
           % ('\\n'.join(NOTES).replace('"', '\\"'), U()))
sch_text = ['(kicad_sch (version 20250114) (generator "eeschema") (generator_version "9.0") (uuid "%s") (paper "A4")' % ROOT_UUID,
            '\t(title_block (title "ProtoSupplies PSB-1 MCU proto board with DC input") (date "2026-11-10") (rev "1")'
            ' (comment 1 "Generated by tools/gen_psb1.py"))', '\t(lib_symbols']
for s in lib_symbols:
    sch_text.append('\t\t' + dump(s, 2))
sch_text.append('\t)')
for item in sch:
    sch_text.append('\t' + item.replace('\n', '\n\t'))
sch_text += ['\t(sheet_instances (path "/" (page "1")))', '\t(embedded_fonts no)', ')']
open(os.path.join(PROJ, NAME + '.kicad_sch'), 'w').write('\n'.join(sch_text) + '\n')

# ------------------------------------------------------------------ PCB
mm = pcbnew.FromMM
CX, CY = 100.0, 100.0                                   # board centre on the sheet
PCB = os.path.join(PROJ, NAME + '.kicad_pcb')
board = pcbnew.NewBoard(PCB)
nets = {}


def net(name):
    if name not in nets:
        n = pcbnew.NETINFO_ITEM(board, name); board.Add(n); nets[name] = n
    return nets[name]


def at(c, r):
    x, y = PG.grid(c, r)
    return pcbnew.VECTOR2I(mm(CX + x), mm(CY + y))


def add_fp(path, name, ref, value, nick, dnp=False):
    fp = pcbnew.FootprintLoad(path, name)
    fp.SetFPID(pcbnew.LIB_ID(nick, name)); fp.SetReference(ref); fp.SetValue(value)
    board.Add(fp)
    return fp


def pad_at(fp, num, c, r, rot=0):
    fp.SetOrientationDegrees(rot)
    p = fp.FindPadByNumber(str(num)).GetPosition(); t = at(c, r)
    fp.Move(pcbnew.VECTOR2I(t.x - p.x, t.y - p.y))


def track(layer, netname, w, pts):
    for (c1, r1), (c2, r2) in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(at(c1, r1)); t.SetEnd(at(c2, r2)); t.SetWidth(mm(w))
        t.SetLayer(board.GetLayerID(layer)); t.SetNet(net(netname)); board.Add(t)


# outline: 102 x 102 with 1.5 mm corner radius
H, R = PG.BOARD / 2, PG.CORNER_R
def P(x, y): return pcbnew.VECTOR2I(mm(CX + x), mm(CY + y))
for (x1, y1), (x2, y2) in (((-H + R, -H), (H - R, -H)), ((H, -H + R), (H, H - R)), ((H - R, H), (-H + R, H)), ((-H, H - R), (-H, -H + R))):
    s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT); s.SetStart(P(x1, y1)); s.SetEnd(P(x2, y2))
    s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.1)); board.Add(s)
k = 1 - math.sqrt(0.5)
for sx, sy in ((1, -1), (1, 1), (-1, 1), (-1, -1)):
    s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_ARC)
    start = P(sx * (H - R), sy * H) if sx * sy < 0 else P(sx * H, sy * (H - R))
    end = P(sx * H, sy * (H - R)) if sx * sy < 0 else P(sx * (H - R), sy * H)
    mid = P(sx * (H - R * k), sy * (H - R * k))
    s.SetArcGeometry(start, mid, end); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.1)); board.Add(s)

# prototyping grid, header blocks (PCB-only footprints)
grid_fp = add_fp(os.path.join(LIB, 'tbd.pretty'), 'ProtoSupplies_PSB-1_Grid', 'PB1', 'PSB-1 grid', 'tbd')
grid_fp.SetPosition(P(0, 0))
for pad in grid_fp.Pads():
    if pad.GetNumber():
        pad.SetNet(net(pad.GetNumber()))
grid_fp.SetAttributes(grid_fp.GetAttributes() | pcbnew.FP_BOARD_ONLY | pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES)
j2 = add_fp(os.path.join(LIB, 'tbd.pretty'), 'PSB-1_Header_2x20_Breakout', 'J2', 'MCU header 2x20', 'tbd'); pad_at(j2, 1, PG.HEADER_2X20[0], PG.HEADER_2X20[1])
j3 = add_fp(os.path.join(LIB, 'tbd.pretty'), 'PSB-1_Header_2x10_Staggered_Breakout', 'J3', 'staggered 2x10', 'tbd'); pad_at(j3, 1, PG.HEADER_2X10[0], PG.HEADER_2X10[1])
for fp, key in ((j2, 'H'), (j3, 'K')):
    fp.Reference().SetVisible(False)
    for pad in fp.Pads():
        pad.SetNet(net(key + pad.GetNumber()))
grid_fp.Reference().SetVisible(False)

# kit parts
kit_fps = []
for ref, lib, fpname, (c, r), rot, value, symlib, sym, padnets in PG.KIT:
    fp = add_fp(STOCK_FP + lib + '.pretty', fpname, ref, value, lib)
    pad_at(fp, 1, c, r, rot)
    for pad in fp.Pads():
        if pad.GetNumber() in padnets:
            pad.SetNet(net(padnets[pad.GetNumber()]))
    fp.Reference().SetVisible(False)
    kit_fps.append(fp)

# copper
for layer, netname, pts in PG.copper_runs():
    track(layer, netname, 1.0 if netname in ('G', 'VIN') or netname.startswith('V') else 0.6, pts)
for layer, netname, w, pts in PG.input_runs():
    track(layer, netname, w, pts)
for layer, netname, pts in PG.header_links():
    track(layer, netname, 0.3, pts)

# title text on the back
t = pcbnew.PCB_TEXT(board); t.SetText('PSB-1 redrawn in KiCad\ntbd-kicad'); t.SetPosition(P(35.5, 43.5)); t.SetLayer(pcbnew.B_SilkS)
t.SetTextSize(pcbnew.VECTOR2I(mm(1.3), mm(1.3))); t.SetMirrored(True); board.Add(t)
board.Save(PCB)

# bare variant: kit parts present as holes only
for fp in kit_fps:
    fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_DNP)
    fp.Models().clear()
    fp.SetValue(fp.GetValue() + ' (not fitted)')
board.Save(os.path.join(PROJ, NAME + '-bare.kicad_pcb'))
for stray in (NAME + '-bare.kicad_pro', NAME + '-bare.kicad_prl'):                # pcbnew writes a project next to any new board name
    if os.path.exists(os.path.join(PROJ, stray)):
        os.remove(os.path.join(PROJ, stray))

# project + library tables
pro = {
    "board": {"design_settings": {"defaults": {}, "rules": {"min_clearance": 0.15, "min_track_width": 0.2}}, "layer_presets": [], "viewports": []},
    "boards": [], "cvpcb": {"equivalence_files": []},
    "libraries": {"pinned_footprint_libs": ["tbd"], "pinned_symbol_libs": ["tbd"]},
    "meta": {"filename": NAME + ".kicad_pro", "version": 3},
    "net_settings": {"classes": [{"name": "Default", "clearance": 0.2, "track_width": 0.6, "via_diameter": 0.8, "via_drill": 0.4,
                                  "diff_pair_width": 0.2, "diff_pair_gap": 0.25}], "meta": {"version": 4}},
    "pcbnew": {"page_layout_descr_file": ""}, "schematic": {"legacy_lib_dir": "", "legacy_lib_list": []},
    "sheets": [[ROOT_UUID, "Root"]], "text_variables": {},
}
json.dump(pro, open(os.path.join(PROJ, NAME + '.kicad_pro'), 'w'), indent=2)
for t, ext in (('sym_lib_table', 'kicad_sym'), ('fp_lib_table', 'pretty')):
    open(os.path.join(PROJ, t.replace('_', '-', 1) if False else ('sym-lib-table' if t.startswith('sym') else 'fp-lib-table')), 'w').write(
        f'({t} (version 7)\n  (lib (name "tbd")(type "KiCad")(uri "${{KIPRJMOD}}/../../lib/tbd.{ext}")(options "")(descr "tbd-kicad"))\n)\n')
print('nets:', len(nets), 'footprints:', len(board.GetFootprints()), 'tracks:', len(board.GetTracks()))
print('wrote', PROJ)
