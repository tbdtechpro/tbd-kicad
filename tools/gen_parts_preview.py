"""Generate projects/parts-preview: a mock PCB that places every library part not used by teensy-panel, so the
footprints and 3D models can be looked at in the KiCad 3D viewer. The small modules sit on the ProtoSupplies PSB-1
grid (pad 1 on a grid hole, no nets); the large boards sit beside it. Run: python3 tools/gen_parts_preview.py"""
import os, shutil, json, re
import pcbnew

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'projects', 'parts-preview')
LIB = os.path.join(ROOT, 'lib', 'tbd.pretty')
STOCK = '/usr/share/kicad/footprints/Module.pretty'
MODEL = '${TBD_KICAD_DIR}/lib/3d/'          # set TBD_KICAD_DIR to the checkout in Preferences > Configure Paths
os.makedirs(OUT, exist_ok=True)
PCB = os.path.join(OUT, 'parts-preview.kicad_pcb')
board = pcbnew.NewBoard(PCB)
mm = pcbnew.FromMM


def add(lib, name, ref, rot=0, nick='tbd', model=None):
    fp = pcbnew.FootprintLoad(lib, name)
    fp.SetFPID(pcbnew.LIB_ID(nick, name))
    fp.SetReference(ref)
    board.Add(fp)
    fp.SetOrientationDegrees(rot)
    if model:
        m = pcbnew.FP_3DMODEL()
        m.m_Filename = model
        fp.Models().push_back(m)
    return fp


def centre_at(fp, cx, cy):
    bb = fp.GetBoundingBox(False, False)
    c = bb.GetCenter()
    fp.Move(pcbnew.VECTOR2I(mm(cx) - c.x, mm(cy) - c.y))


def pad_at(fp, num, x, y):
    p = fp.FindPadByNumber(str(num)).GetPosition()
    fp.Move(pcbnew.VECTOR2I(mm(x) - p.x, mm(y) - p.y))


# board outline 290 x 150
rect = pcbnew.PCB_SHAPE(board)
rect.SetShape(pcbnew.SHAPE_T_RECT)
rect.SetStart(pcbnew.VECTOR2I(mm(0), mm(0)))
rect.SetEnd(pcbnew.VECTOR2I(mm(290), mm(150)))
rect.SetLayer(pcbnew.Edge_Cuts)
rect.SetWidth(mm(0.1))
board.Add(rect)

# PSB-1 carrier and the modules plugged into its grid
PSB = (60.0, 75.0)
def grid(c, r):
    return PSB[0] + (c - 18.5) * 2.54, PSB[1] + (r - 18.5) * 2.54
# the PSB-1 is a separate board: show it as its STEP model on 6 mm standoffs instead of copper on this board
STANDOFF = 6.0
RAISED = ['PB1']                                  # footprints whose models are lifted by STANDOFF after saving
psb = pcbnew.FOOTPRINT(board); psb.SetFPID(pcbnew.LIB_ID('tbd', 'ProtoSupplies_PSB-1_Model')); psb.SetReference('PB1'); psb.SetValue('ProtoSupplies PSB-1')
board.Add(psb); psb.SetPosition(pcbnew.VECTOR2I(mm(PSB[0]), mm(PSB[1])))
# the library STEP is board-only; for the preview export a copy with pads, tracks and silkscreen next to the project
# (24 MB, kept out of git, rebuilt here when missing)
DETAIL = os.path.join(OUT, 'ProtoSupplies_PSB-1_detail.step')
if not os.path.exists(DETAIL):
    import subprocess
    subprocess.run(['kicad-cli', 'pcb', 'export', 'step', '--subst-models', '--no-dnp', '--include-pads', '--include-tracks',
                    '--include-silkscreen', '--fuse-shapes', '--user-origin', '100x100mm', '-f', '-o', DETAIL,
                    os.path.join(ROOT, 'projects', 'psb-1', 'psb-1-bare.kicad_pcb')], check=True,
                   env=dict(os.environ, TBD_KICAD_DIR=ROOT))
m = pcbnew.FP_3DMODEL(); m.m_Filename = '${KIPRJMOD}/ProtoSupplies_PSB-1_detail.step'
m.m_Offset = pcbnew.VECTOR3D(0.0, 0.0, 0.0)          # exported with --user-origin at the board centre (sheet 100, 100)
psb.Models().push_back(m)
psb.Reference().SetVisible(False); psb.Value().SetVisible(False)
for sx in (-1, 1):
    for sy in (-1, 1):
        so = add(LIB, 'Standoff_M3_H6mm', 'H%d' % (len(board.GetFootprints())), 0)
        centre_at(so, PSB[0] + sx * 45.72, PSB[1] + sy * 45.72); so.Reference().SetVisible(False)
for name, ref, num, c, r, rot in (('RP2040-Zero', 'U2', 1, 13, 7, 0),
                                  ('Beetle_RP2350_DFR1188_THT', 'U1', 1, 21, 7, 0),
                                  ('Adafruit_TXB0104_Breakout', 'U3', 1, 13, 18, 0),
                                  ('Adafruit_BSS138_Level_Shifter', 'U4', 1, 21, 18, 0),
                                  ('Adafruit_PCM510x_I2S_DAC', 'U5', 1, 14, 33, 0),
                                  ('Jack_3.5mm_Kycon_STX-3120-3B_Horizontal', 'J1', 1, 34, 30, 180)):
    fp = add(LIB, name, ref, rot); pad_at(fp, num, *grid(c, r))
    RAISED.append(ref)                                # the module sits on the raised PSB-1

# larger boards beside it
esp = add(LIB, 'ESP32-S3-DevKitC-1', 'A1', 90); centre_at(esp, 165, 24)
tft = add(LIB, 'TFT_2.8in_ILI9341_SPI_MSP2806', 'DS1'); centre_at(tft, 222, 82)
rpw = add(LIB, 'RP2350B-Plus-W', 'U6'); centre_at(rpw, 263, 48)
oled = add(LIB, 'OLED_1.5in_SH1107_128x128_I2C', 'DS2'); centre_at(oled, 270, 112)
for name, ref, x in (('TRRS_3.5mm_Jack_Breakout', 'J2', 18), ('WS2812_RGB_LED_Module', 'D1', 38), ('MicroSD_Card_Module_SPI_3V3', 'J3', 61),
                     ('USB-C_Breakout_16P_6pin', 'J4', 87), ('SW_Push_6x6mm_2pin_P5.08mm', 'SW1', 103)):
    centre_at(add(LIB, name, ref), x, 137)
uno = add(LIB, 'MIDI_Shield_K194725ASJH', 'A2'); centre_at(uno, 158, 100)
logo = add(LIB, 'Logo_TBD_Full_40mm', 'G1'); centre_at(logo, 222, 18)
star = add(LIB, 'Logo_Star_10mm', 'G2'); centre_at(star, 282, 143)
board.Save(PCB)
# lift the 3D models of the PSB-1 and the modules on it (the swig wrapper does not expose the model offsets)
text = open(PCB).read()
def lift(block):
    return re.sub(r'\(model (.*?)\(offset\s*\(xyz\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s*\)',
                  lambda m: f'(model {m.group(1)}(offset (xyz {m.group(2)} {m.group(3)} {float(m.group(4)) + STANDOFF:g})', block, flags=re.S)
parts = re.split(r'(?=\n\t\(footprint )', text)
for i, blk in enumerate(parts):
    m = re.search(r'\(property "Reference" "([^"]+)"', blk)
    if m and m.group(1) in RAISED:
        parts[i] = lift(blk)
open(PCB, 'w').write(''.join(parts))

# project file and library tables (same layout as teensy-panel)
src = os.path.join(ROOT, 'projects', 'teensy-panel')
for t in ('sym-lib-table', 'fp-lib-table'):
    shutil.copy(os.path.join(src, t), os.path.join(OUT, t))
pro = json.load(open(os.path.join(src, 'teensy-panel.kicad_pro')))
pro['meta']['filename'] = 'parts-preview.kicad_pro'
json.dump(pro, open(os.path.join(OUT, 'parts-preview.kicad_pro'), 'w'), indent=2)
print('wrote', PCB, 'footprints:', len(board.GetFootprints()))
