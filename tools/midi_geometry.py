"""Geometry and circuit of the K194725ASJH Arduino UNO MIDI shield (3 x DIN-5, 6N138), shared by gen_lib.py and
gen_midi_shield.py. Frame: the UNO header pattern as in KiCad's own Arduino_Uno shield template, i.e. a true top
view with the USB end at -X: the R3 power header's pin 1 (NC) position is the origin, pins along +X at 2.54 mm,
analog header from x = 22.86, digital header at y = -48.26 (AREF at x = -4.06 ... D0 at x = 35.56). The shield is the
older 6+6 / 8+8 pattern (no NC/IOREF, no SDA/SCL pins). Positions come from photos of both board sides rectified
through the header pads (about +/-0.5 mm) unless marked measured."""
P = 2.54
DIG_Y = -48.26
# board outline: 57.2 x 53.0 mm by calipers; both header rows sit 2.37 mm from their edges, the USB-end edge is
# 2.37 mm beyond the AREF pin and the far edge 2.5 mm beyond the P8 proto row (photos)
BOARD = {'x0': -6.43, 'x1': 50.77, 'y0': -50.63, 'y1': 2.37, 'corner': 1.0}

# UNO headers: ref, stock footprint, pin 1 position, pin names (pin 1 first, along +X)
HEADERS = [
    ('J1', 'PinHeader_1x06_P2.54mm_Vertical', (5.08, 0.0), ['RESET', '3V3', '5V', 'GND', 'GND', 'VIN']),
    ('J2', 'PinHeader_1x06_P2.54mm_Vertical', (22.86, 0.0), ['A0', 'A1', 'A2', 'A3', 'A4', 'A5']),
    ('J3', 'PinHeader_1x08_P2.54mm_Vertical', (-4.06, DIG_Y), ['AREF', 'GND', 'D13', 'D12', 'D11', 'D10', 'D9', 'D8']),
    ('J4', 'PinHeader_1x08_P2.54mm_Vertical', (17.78, DIG_Y), ['D7', 'D6', 'D5', 'D4', 'D3', 'D2', 'TX', 'RX']),
]
# prototyping rows along the far edge, one continuous 2.54 mm line of 18 holes per row starting on the digital
# header line (pin 1 = square pad at the digital-header end). The inner row is a header breakout wired on the back:
# P4 = D2..D7, P5 = D8..D13, P6 = A0..A5 (trace fans read from the back photo); P10/P9/P7 and the extra P8 row are
# free holes beside them. ref, pin 1 position, nets (None = unconnected)
PROTO_ROWS = [('P4', 43.18, -48.26, ['D2', 'D3', 'D4', 'D5', 'D6', 'D7']), ('P10', 45.72, -48.26, None),
              ('P5', 43.18, -33.02, ['D8', 'D9', 'D10', 'D11', 'D12', 'D13']), ('P9', 45.72, -33.02, None),
              ('P6', 43.18, -17.78, ['A0', 'A1', 'A2', 'A3', 'A4', 'A5']), ('P7', 45.72, -17.78, None), ('P8', 48.26, -17.78, None)]

# DIN-5 socket PCB pattern: outer pins (1, 3) 16 mm apart with pin 2 between them (measured), the MIDI pair (4, 5)
# 9.5 mm apart in a second row 2.5 mm further from the face (measured); that front row is 14.5 mm behind the face.
# Three shell lugs toward the face: a pair under the pins 4/5 and one on the centre line (back photo). Opening
# toward -Y, pin 2 at the origin.
DIN = {'pins': {'2': (0.0, 0.0), '1': (-8.0, 0.0), '3': (8.0, 0.0), '4': (-4.75, 2.5), '5': (4.75, 2.5)},
       'lugs': ((-4.75, -10.5), (4.75, -10.5), (0.0, -8.0)), 'lug_drill': 1.5, 'pin_drill': 1.1,
       'body_w': 18.0, 'body_d': 17.0, 'body_h': 15.5, 'face_from_pin2': -14.5, 'overhang': 0.0}
# socket placements: ref, net prefix, pin 2 position, rotation (0 = opening toward -Y; 90 = toward -X, the USB edge)
# IN and OUT open on the USB-end edge; THRU opens toward the power/analog edge with its face just inboard of the
# analog header pads.
SOCKETS = [('COM1', 'IN', (8.07, -36.2), 90), ('COM2', 'OUT', (8.07, -17.2), 90), ('COM3', 'THRU', (26.85, -17.0), 180)]

# other parts: ref, lib, footprint, value, position (pad 1 for U1, pad 2 for S2, centre otherwise), rotation, pad -> net.
# All six resistors are marked 221 (220 R).
SLIDE = {'pitch': 2.5, 'lug_spacing': 10.0, 'body': (8.6, 3.6, 5.0)}
PARTS = [
    ('U1', 'Package_DIP', 'DIP-8_W7.62mm', '6N138', (19.4, -32.8), 0,
     {'1': None, '2': 'IN_A', '3': 'IN_K', '4': None, '5': 'GND', '6': 'OPTO_OUT', '7': None, '8': '+5V'}),
    ('D1', 'Diode_SMD', 'D_MiniMELF', '1N4148', (16.0, -32.7), 270, {'1': 'IN_A', '2': 'IN_K'}),       # band toward -Y
    ('R2', 'Resistor_SMD', 'R_0805_2012Metric', '220', (15.6, -28.3), 90, {'1': 'IN_4', '2': 'IN_A'}),
    ('R1', 'Resistor_SMD', 'R_0805_2012Metric', '220', (14.9, -24.3), 90, {'1': '+5V', '2': 'THRU_4'}),
    ('R5', 'Resistor_SMD', 'R_0805_2012Metric', '220', (17.3, -24.3), 90, {'1': 'OPTO_OUT', '2': 'THRU_5'}),
    ('R3', 'Resistor_SMD', 'R_0805_2012Metric', '220', (15.1, -17.8), 90, {'1': 'TX', '2': 'OUT_5'}),
    ('R4', 'Resistor_SMD', 'R_0805_2012Metric', '220', (14.9, -12.5), 90, {'1': '+5V', '2': 'OUT_4'}),
    ('R6', 'Resistor_SMD', 'R_0805_2012Metric', '220', (30.2, -23.2), 0, {'1': '+5V', '2': 'OPTO_OUT'}),
    ('S1', 'Button_Switch_THT', 'SW_PUSH_6mm', 'RESET', (22.5, -39.2), 90, {'1': 'RESET', '2': 'GND'}),
    ('S2', 'tbd', 'SW_Slide_SPDT_P2.5mm_Lugs', 'RX ON/OFF', (31.0, -31.5), 90, {'1': 'RX', '2': 'OPTO_OUT', '3': None}),
]
SOCKET_NETS = {'IN': {'4': 'IN_4', '5': 'IN_K', '2': None}, 'OUT': {'4': 'OUT_4', '5': 'OUT_5', '2': 'GND'},
               'THRU': {'4': 'THRU_4', '5': 'THRU_5', '2': 'GND'}}
