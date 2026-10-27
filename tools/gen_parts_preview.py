"""Generate projects/parts-preview: a mock PCB that places every library part not used by teensy-panel, so the
footprints and 3D models can be looked at in the KiCad 3D viewer. The small modules sit on the ProtoSupplies PSB-1
grid (pad 1 on a grid hole, no nets); the large boards sit beside it. Run: python3 tools/gen_parts_preview.py"""
import os, shutil, json
import pcbnew

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'projects', 'parts-preview')
LIB = os.path.join(ROOT, 'lib', 'tbd.pretty')
STOCK = '/usr/share/kicad/footprints/Module.pretty'
MODEL = '${KIPRJMOD}/../../lib/3d/'
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


# board outline 270 x 150
rect = pcbnew.PCB_SHAPE(board)
rect.SetShape(pcbnew.SHAPE_T_RECT)
rect.SetStart(pcbnew.VECTOR2I(mm(0), mm(0)))
rect.SetEnd(pcbnew.VECTOR2I(mm(270), mm(150)))
rect.SetLayer(pcbnew.Edge_Cuts)
rect.SetWidth(mm(0.1))
board.Add(rect)

# PSB-1 carrier and the modules plugged into its grid
PSB = (60.0, 75.0)
def grid(c, r):
    return PSB[0] + (c - 18.5) * 2.54, PSB[1] + (r - 18.5) * 2.54
psb = add(LIB, 'ProtoSupplies_PSB-1', 'PB1'); centre_at(psb, *PSB)
for name, ref, num, c, r, rot in (('RP2040-Zero', 'U2', 1, 13, 7, 0),
                                  ('Beetle_RP2350_DFR1188_THT', 'U1', 1, 21, 7, 0),
                                  ('Adafruit_TXB0104_Breakout', 'U3', 1, 13, 18, 0),
                                  ('Adafruit_BSS138_Level_Shifter', 'U4', 1, 21, 18, 0),
                                  ('Adafruit_PCM510x_I2S_DAC', 'U5', 1, 14, 33, 0),
                                  ('Jack_3.5mm_Kycon_STX-3120-3B_Horizontal', 'J1', 1, 34, 30, 180)):
    fp = add(LIB, name, ref, rot); pad_at(fp, num, *grid(c, r))

# larger boards beside it
esp = add(LIB, 'ESP32-S3-DevKitC-1', 'A1', 90); centre_at(esp, 165, 24)
tft = add(LIB, 'TFT_2.8in_ILI9341_SPI_MSP2806', 'DS1'); centre_at(tft, 232, 82)
uno = add(STOCK, 'Arduino_UNO_R3_WithMountingHoles', 'A2', 0, 'Module', MODEL + 'MIDI_Shield_UNO.wrl'); centre_at(uno, 158, 100)
uno.SetValue('MIDI_Shield_DIN5x3_6N138')
logo = add(LIB, 'Logo_TBD_Full_40mm', 'G1'); centre_at(logo, 232, 18)
star = add(LIB, 'Logo_Star_10mm', 'G2'); centre_at(star, 258, 140)
board.Save(PCB)

# project file and library tables (same layout as teensy-panel)
src = os.path.join(ROOT, 'projects', 'teensy-panel')
for t in ('sym-lib-table', 'fp-lib-table'):
    shutil.copy(os.path.join(src, t), os.path.join(OUT, t))
pro = json.load(open(os.path.join(src, 'teensy-panel.kicad_pro')))
pro['meta']['filename'] = 'parts-preview.kicad_pro'
json.dump(pro, open(os.path.join(OUT, 'parts-preview.kicad_pro'), 'w'), indent=2)
print('wrote', PCB, 'footprints:', len(board.GetFootprints()))
