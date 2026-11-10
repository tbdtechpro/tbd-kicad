# Component reference

Everything in `lib/tbd.kicad_sym` and `lib/tbd.pretty/`, with the source of every
dimension and what is still unverified. Regenerate the library with `python3 tools/gen_lib.py`.

| Part | Symbol | Footprint | Geometry confidence |
|---|---|---|---|
| Teensy 4.1 | `Teensy_4.1` (67 pins) | `Teensy41` + STEP | exact (XenGi libraries, MIT) |
| DFRobot Beetle RP2350 | `Beetle_RP2350_DFR1188` | `Beetle_RP2350_DFR1188_THT`, `_SMD` | exact (pad pitch/rows from DFRobot CAD V1.0, redrawn) |
| 2.8" ILI9341 SPI TFT | `TFT_2.8in_ILI9341_SPI_MSP2806` | `TFT_2.8in_ILI9341_SPI_MSP2806` | exact (lcdwiki MSP2806_Size.pdf) |
| 1.28" round GC9A01, 7-pin | `GC9A01_Round_1.28in_7pin` | `GC9A01_Round_1.28in_7pin` | header exact, outline approximate |
| KY-040 encoder module | `KY-040_Rotary_Encoder_Module` | `KY-040_Module_RA_Header` | header exact, module size approximate |
| RP2040-Zero form factor | `RP2040-Zero` | `RP2040-Zero` | edge pins exact (Waveshare drawing), back pads approximate |
| ESP32-S3-DevKitC-1 | `ESP32-S3-DevKitC-1` | `ESP32-S3-DevKitC-1` | exact (Espressif library, CC-BY-SA 4.0) |
| Waveshare RP2350B-Plus-W | `RP2350B-Plus-W` | `RP2350B-Plus-W` + VRML/STEP | pins exact (Waveshare drawing), back pads from photos |
| TK103 PCM5102A I2S DAC | `TK103_PCM5102A_I2S_DAC` | `TK103_Module_RA_Header` + STEP | exact (vendor STEP) |
| MIDI shield (K194725ASJH) | `MIDI_Shield_DIN5x3_6N138` | stock `Module:Arduino_UNO_R3_WithMountingHoles` | exact (UNO header pattern) |
| ElectroCookie full breadboard | none (mechanical) | `ElectroCookie_Breadboard_Full` | outline/holes exact, rail length approximate |
| Adafruit PCM510x I2S DAC | `Adafruit_PCM510x_I2S_DAC` | `Adafruit_PCM510x_I2S_DAC` + VRML/STEP | exact (Adafruit EagleCAD board) |
| Adafruit TXB0104 breakout | `Adafruit_TXB0104_Level_Shifter` | `Adafruit_TXB0104_Breakout` + VRML/STEP | exact (Adafruit EagleCAD board) |
| Adafruit BSS138 4-ch level shifter | `Adafruit_BSS138_4ch_Level_Shifter` | `Adafruit_BSS138_Level_Shifter` + VRML/STEP | exact (Adafruit EagleCAD board) |
| Kycon STX-3120-3B 3.5 mm jack | `AudioJack_3.5mm_STX-3120-3B` | `Jack_3.5mm_Kycon_STX-3120-3B_Horizontal` + VRML/STEP | exact (Kycon drawing) |
| Sharp PC900V photocoupler | `PC900V` | stock `Package_DIP:DIP-6_W7.62mm` | exact (Sharp drawing) |
| Toshiba TLP2962 photocoupler | `TLP2962` | stock `Package_DIP:DIP-8_W7.62mm` | exact (Toshiba drawing) |
| ProtoSupplies PSB-1 proto board | none (mechanical) | `ProtoSupplies_PSB-1`, `_DCKit`, `_Grid`, `PSB-1_Header_*` + STEP | outline/holes/grid exact, input-section parts +/-0.15 mm, V-rail continuity unverified |

Redistributable vendored sources live in `lib/vendor/` (Teensy: MIT; Espressif: CC-BY-SA 4.0; Adafruit EagleCAD boards: CC-BY-SA 3.0); 3D models in `lib/3d/`. Vendor documents and models without redistribution terms (DFRobot CAD/PDFs, lcdwiki drawing, Waveshare images, Lonely Binary guide and STEP) stay in the private overlay repo and are only linked here. Footprints reference models as
`${TBD_KICAD_DIR}/lib/3d/...`; set the `TBD_KICAD_DIR` path variable to the checkout (Preferences > Configure Paths).

## Teensy 4.1 (PJRC)

- i.MX RT1062, Cortex-M7 600 MHz, 8 MB flash, micro SD, USB host and device, Ethernet PHY, bottom pads for
  PSRAM and flash. 3.3 V logic, pins are not 5 V tolerant. 3.3 V regulator output rated 250 mA.
- Board 60.96 x 17.78 mm (2.4 x 0.7 in). Two rows of 24 pins at 2.54 mm, rows 15.24 mm (0.6 in) apart.
- Symbol/footprint numbering (XenGi): pins 1-24 are the left column with USB at the top (1 = GND, 2 = D0 ...
  15 = 3V3, 16-24 = D24-D32); pins 25-48 are the right column from the SD end upward (25 = D33 ... 34 = GND,
  35 = D13 ... 46 = 3V3, 47 = GND, 48 = VIN); 49 = VUSB; 50-54 = VBAT/3V3/GND/PROGRAM/ON_OFF; 55-59 USB host;
  60-65 Ethernet; 66-67 USB device D-/D+.
- Pins 46 (3V3) and 47 (GND) are typed power output so they drive the power nets in ERC.
- The XenGi STEP is uncoloured (two fused solids). `tools/build_models.py` writes `Teensy_4.1_Assembly.wrl`
  coloured by face height (board green, parts black, USB and SD shells silver); the footprint references the
  `.wrl` and KiCad substitutes the `.step` on STEP export.
- References: PJRC pinout cards 11a/11b, Teensy 4.1 schematic and dimension drawings (pjrc.com), NXP IMXRT1060 RM/CEC/errata.

## DFRobot Beetle RP2350 (DFR1188)

- RP2350A, USB-C, TP4057 LiPo charger with BAT pad, RT9080 3.3 V LDO, BOOT and RST buttons, user LED on GPIO 25.
  20.5 x 25 mm, 1.0 mm PCB.
- Pads (DFRobot CAD): 1-8 left column top to bottom = GND, 3V3, GPIO0, 1, 4, 5, 8, 9; 9-16 right column bottom
  to top = GPIO16, 18, 19, 26, 27, VCC, GND, BAT. VCC is the USB 5 V rail.
- DFRobot's "datasheet" download is Raspberry Pi's RP2350 chip datasheet, not a board document. Wiki: https://wiki.dfrobot.com/SKU_DFR1188_Beetle_RP2350

## 2.8" ILI9341 SPI TFT (DIANN listing; lcdwiki MSP2806 no-touch / MSP2807 touch)

- 240 x 320, ILI9341V, 4-wire SPI, 5 V or 3.3 V supply (onboard LDO), 3.3 V logic. micro SD socket on SPI.
- PCB 50.00 x 86.00 mm. Holes 3.2 mm (4.7 mm ring) on a 44.00 x 76.08 mm pattern, 3.00 mm from the top and
  side edges. 14-pin header J2 2.00 mm from the bottom edge, pin 1 (VCC) 8.49 mm from the left edge. 4-pin SD
  header J4 6.40 mm from the top edge, centred. LCD glass 50.0 x 69.2 starting 9.30 mm from the top; active area
  43.2 x 57.6.
- Pins: 1 VCC, 2 GND, 3 CS, 4 RESET, 5 DC, 6 SDI(MOSI), 7 SCK, 8 LED, 9 SDO(MISO), 10 T_CLK, 11 T_CS, 12 T_DIN,
  13 T_DO, 14 T_IRQ; 15 SD_CS, 16 SD_MOSI, 17 SD_MISO, 18 SD_SCK. The no-touch board keeps the touch pins on
  the header with the XPT2046 unpopulated.
- The 2.4" module (lcdwiki MSP2402) is the smaller sibling: 42.72 x 77.18 mm, same pinout.

## 1.28" round GC9A01, 7-pin (Teyleten Robot listing)

- 240 x 240 IPS, GC9A01, 4-wire SPI, 3.3 V. Pins: 1 VCC, 2 GND, 3 SCL, 4 SDA, 5 DC, 6 CS, 7 RST
  (VCC has the square pad). Silkscreen note: R8 pulls CS low so CS and RST may be left unconnected.
- Footprint: header exact (2.54 mm, pin 1 at x = -7.62). Round outline dia 37.5 mm, tab 27 x 7.5 mm, M2 holes
  at +/-11.5 mm from the header centre are estimates from photos and listings (38 x 45.5 mm overall).
  **Measure the module before cutting a panel.**
- 3D model `lib/3d/GC9A01_Round_1.28in_7pin.wrl/.step` (built by `tools/build_models.py`): PCB, glass, 7-pin
  male header underneath; same estimates as the footprint.

## KY-040 rotary encoder module

- EC11-style encoder with push switch, 10 k pull-ups on CLK and DT to "+", SW shorts to GND when pressed.
  5-pin right-angle header: 1 GND, 2 +, 3 SW, 4 DT, 5 CLK (numbering is ours; the module has no numbers).
- The footprint is a carrier: a 1x5 pin row where the module plugs in, standing perpendicular on the -Y side.
  Module PCB about 26 x 19 mm (listings disagree; not measured).
- 3D model `lib/3d/KY-040_Module.wrl/.step` is built by `tools/build_models.py` from those estimates: board, EC11
  body, bushing, 6 mm shaft, right-angle pins. Knob not modelled.

## RP2040-Zero form factor (QIQIAZI board)

- Your board is an RP2040 (4 MB flash, WS2812 on GP16, USB-C, BOOT/RESET). The listing image that came with it
  shows an RP2350A sibling; the footprint is the same either way.
- 18.00 x 23.50 mm, R1 corners (Waveshare drawing): side columns 15.24 mm apart starting 1.59 mm below the top
  edge; bottom row ends 3.92 mm from the right edge. Pins 1-9 left (5V, GND, 3V3, GP29, 28, 27, 26, 15, 14),
  10-14 bottom (GP13..GP9), 15-23 right bottom-up (GP8..GP0).
- Back solder pads 24-33 (GND, GP25..GP17) are placed from a photo at 2.0 mm pitch: approximate.

## Waveshare RP2350B-Plus-W

- RP2350B (dual Cortex-M33 / Hazard3 at 150 MHz, 520 KB SRAM), 16 MB W25Q128 flash, Raspberry Pi Radio Module 2
  (Wi-Fi 4, BT 5.2) on GP36 WL_ON, GP37 WL_D, GP38 WL_CS, GP39 WL_CLK, USB-C, BOOT and RESET buttons, ME6217 3.3 V
  LDO (CE on 3V3_EN, pulled to VSYS), MBR230 Schottky from VBUS to VSYS, VSYS sense on GP46 via a FET divider,
  VBUS detect through the radio module's GPIO2. LED2 (red) on GP23, LED1 (red) on the radio module's WL_GPIO0.
  PSRAM footprint on the back is unpopulated, CS on GP47. 41 GPIO on pads: GP0-22 and GP40-42 (ADC0-2) on the
  40-pin Pico 2 W edge pattern, GP24-35 and GP43-45 on 15 back pads. No SWD pads. All from the Waveshare schematic.
- Pin 1-40 names follow the Pico 2 W except pins 31/32/34 = GP40/GP41/GP42 (RP2350B puts the ADC on GP40-47).
  Back pads are pins 41-55 in GPIO order (41 = GP24 ... 52 = GP35, 53-55 = GP43-45).
- Geometry: 21.00 x 51.00 mm board (Waveshare drawing; calipers 51.0), pins at 2.54 mm pitch in rows 17.78 mm apart,
  first pin 1.25 mm from the top edge; USB-C 8.95 mm wide, 1.3 mm proud; radio module 16.0 mm wide with the antenna
  end 4.92 mm past the bottom edge on the drawing, 5.7 mm by calipers (the footprint uses 5.7). Back pads 1.5 mm
  square on a 2.54 mm grid centred on the board, three rows about 0.5 mm below pins 24/23/22, read from photos
  (private overlay `reference/photos/rp2350b-plus-w/`): +/-0.3 mm. Front-frame column order, left to right:
  GP24-26, GP27-29, GP30-32, GP33-35, GP43-45 (top to bottom within a column).
- 3D body from `tools/build_models.py`: board, castellations, headers, USB-C, buttons, LDO, RP2350B, crystal, the
  radio module with its antenna overhang, flash and PSRAM site and the labelled pads on the back.

## ESP32-S3-DevKitC-1 "Gold Edition" N16R8

- ESP32-S3-WROOM-1 N16R8 (16 MB flash, 8 MB octal PSRAM), CH340K UART USB-C and native USB-C, WS2812 on
  GPIO 48, AMS1117-3.3. 2 x 22 pins at 2.54 mm, rows 22.86 mm apart, board 62.74 x 25.40 mm.
- GPIO 35-37 are taken by the octal PSRAM; GPIO 0/3/45/46 are strapping pins.
- Symbol and footprint are Espressif's (CC-BY-SA 4.0), converted from the KiCad 10 file format.

## Lonely Binary TK103 I2S DAC

- TI PCM5102A, 112 dB, line level 2.1 V RMS on a 3.5 mm jack, 3.0-3.6 V supply only. PLL locks to BCK, so no
  MCLK: use 16-bit slots at 32 kHz and up or 32-bit slots at 16 kHz. XSMT pulled high by 10 k on board; a
  GPIO driving it low mutes with a ramp.
- Pins (right-angle header): 1 GND, 2 3V3, 3 BCK, 4 DIN, 5 LRCK, 6 XSMT.
- From the vendor STEP (lonelybinary.com, kept in the private overlay as `lib/3d/TK103_PCM5102A.step`): board 22.37 x 30.37 mm, R3 corners; header holes 0.9 mm at 2.54 mm pitch centred,
  5.39 mm above the bottom edge; two 4.8 mm openings 3.2 mm in from each side at mid-height; jack centred on
  the top edge, 6 mm wide, protruding 1.5 mm.
- The standing 3D model in `TK103_Module_RA_Header` was checked with `kicad-cli pcb render`: pins through the pads, board edge on the carrier, 3.4-5 mm from the pin row.

## MIDI shield (board marking K194725ASJH)

- Arduino UNO shield: three 5-pin DIN (IN, OUT, THRU), 6N138 optocoupler on the input, slide switch that
  disconnects MIDI IN from D0/RX so sketches can still be uploaded, reset button, prototyping rows.
- Symbol pin numbers match KiCad's `Arduino_UNO_R3` symbol and `Module:Arduino_UNO_R3*` footprints.

## ElectroCookie full-size breadboard PCB

- 172.7 x 52.1 mm. Row strips A-E and F-J, columns 1-63, 2.54 mm pitch, 7.62 mm across the centre gap. Two
  power rails per side. M3 centre holes at the column-1, column-32 and column-63 positions on the centre line;
  M2 corner holes 162.6 x 35.6 mm apart.
- Footprint pads: `L<n>` = holes A-E of row n (one net), `R<n>` = holes F-J, rails `T+`/`T-`/`B+`/`B-`
  (columns 0-64). Back-side copper reproduces the strip traces and the rail traces.
- Rail jumpers: two pads at each end on the centre line. The left end's pair is wired to the two outer (-) rails,
  the right end's pair to the two inner (+) rails; bridge a pair with solder to join left and right rails.
  Positions are read from photos (about 2.5 mm inside the M3 hole, 2.54 mm apart).
- Drawn horizontally (row 1 left, A at the bottom); rotate 270 in pcbnew for the vertical, row-1-up view.

## Adafruit PCM5102 / PCM5100 I2S DAC breakout (6250 / 6251)

- TI PCM5102A (112 dB) or PCM5100A (100 dB), pin-compatible boards. VIN 3.3-5 V through an AP2127 3.3 V LDO whose
  output is on the 3V pin; logic is 3.3 V only. I2S in on BCK/WSEL/DIN, MCK optional (PLL from BCK). Line-level
  Lout/Rout plus a PJ-332A 3.5 mm jack: not AC-coupled, 1 k load minimum, not for headphones. DE (de-emphasis),
  FIL (filter), MU (mute, pull low), FM (format, high = left-justified) have onboard 10 k pulls.
- Geometry from the Adafruit EagleCAD board (`lib/vendor/adafruit/PCM510x-I2S-DAC/`, CC-BY-SA): 30.48 x 20.32 mm,
  R2.54 corners, plated 2.5 mm holes at (+/-12.7, +/-7.62). 8-pin header VIN GND WSEL DIN BCK Lout G Rout at
  y = +7.62 (x = -8.89 ... +8.89), 6-pin header DE FIL MCK MU FM 3V at y = -7.62 (x = -6.35 ... +6.35), 1.0 mm drills.
  Jack body on the right edge, barrel 1.6 mm proud. Symbol pins are numbered 1-8 and 9-14 in that silkscreen order.
- 3D model built by `tools/build_models.py` (black PCB on headers, jack, chip, regulator).

## Adafruit TXB0104 bi-directional level shifter breakout (1875)

- TI TXB0104, auto direction sensing, LV 1.2-3.6 V, HV 1.7-5.5 V, OE pulled up on board. Not for I2C or any bus with
  pull-ups under 50 k.
- From the Adafruit EagleCAD board (`lib/vendor/adafruit/TXB0104-Breakout/`): 12.7 x 17.78 mm, R2.54 corners, two 1x6
  headers at x = +/-5.08, pins at y = -6.35 ... +6.35, 1.0 mm drills, no mounting hole. Left top to bottom LV A1 A2 A3
  A4 OE (pins 1-6), right HV B1 B2 B3 B4 GND (pins 7-12).

## Adafruit 4-channel BSS138 level shifter (757)

- Four BSS138 FETs with 10 k pull-ups to LV and HV (NXP AN10441 scheme): I2C-safe, LV down to 1.8 V, HV to 10 V,
  slow (SPI under about 2 MHz). The two GND pins are joined on the board.
- From the Adafruit EagleCAD board (`lib/vendor/adafruit/BSS138-4ch-Level-Shifter/`): 15.24 x 20.45 mm, headers at
  x = +/-5.08 with pins at y = -6.35 ... +6.35 (the header row centre is 10.16 mm above the bottom edge, 10.29 below
  the top). Left LV A1 A2 A3 A4 GND (1-6), right HV B1 B2 B3 B4 GND (7-12).

## Kycon STX-3120-3B 3.5 mm stereo jack (Adafruit 1699)

- All-plastic right-angle jack, spring contacts, no switch pins (the 5B variant adds pins 3 and 4). Adafruit sells it
  as the "breadboard-friendly" jack: the 5.0 mm pin spacing fits 0.1" holes.
- From the Kycon drawing (STX3120.pdf, private overlay `reference/docs/`): body 12.0 wide, 10.0 tall, 14.1 deep of
  which 3.5 is the 6.8 mm bezel; plug hole 3.6 mm at 6.5 mm above the PCB. Pin 1 (sleeve) centred 3.0 mm behind the
  bezel; pins 2 (tip, left looking into the jack) and 5 (ring) 5.0 mm further back at +/-5.0 mm; pins 1.0 x 0.5 mm
  (1.1 mm drills). Footprint origin at pin 1, opening toward -Y; place it so the bezel clears the board edge.

## ProtoSupplies PSB-1 MCU proto board with DC input

- 102 x 102 mm FR-4, 1.6 mm, ENIG, 1.5 mm corner radius, four 3.5 mm holes on a 91.44 mm square (vendor dimension
  drawing). The 2.54 mm grid is 38 x 38 positions centred on the board; the holes sit half a pitch outside the outer
  rows/columns (checked on the vendor CAD renders and the board). 1.02 mm plated holes, 1.78 mm pads.
- Layout, from the CAD renders and photos of the board (private overlay `reference/photos/psb-1/`), column C / row R
  from 0 at the top-left, all in `tools/psb1_geometry.py`: 2x20 header at rows 0-1, columns 3-22 (pin 1 bottom-left,
  odd pins in row 1) with breakout pads in rows 2-3 (row 2 joins the odd pins straight down on the back, row 3 the
  even pins by a front-side trace swinging between the columns); staggered 2x10 header at columns 25-34 (even pins and
  their breakouts 1.27 mm to the right) with breakout rows 2-3; ground band (back-side trace) at row 4 and V band
  segments (front-side) at row 5, feed pad pairs at columns 3 8 15 22 29 34; V/G column pairs at C0/1, 5/6, 10/11,
  18/19, 26/27, 31/32, 36/37; 3-hole strips at C2-4, C7-9 (rows 6-24), C28-30, C33-35 (rows 6-33); 6-hole strips at
  C12-17 and C20-25 (rows 6-37); 2x2 VIN/V jumper at C9-10 rows 26-27 (top row = V of column 10, two shunts bridge
  VIN to it); VIN column at C10 rows 28-37.
- DC input section, bottom-left: P1 barrel jack on the GCT DCJ200-10-A pattern (centre pin 6.3 mm from the sleeve pin,
  switch pin 4.8 mm to the side; the stock KiCad footprint matches the slots on the board), J1 JST XH 2-pin (+ at the
  bottom), C1 100 uF at 2 mm pitch (+ at the bottom), C2 100 nF, R1 1 k at 10.16 mm, 3 mm LED. Nets from the vendor
  schematic. The LED anode is the upper pad: the back-side trace from R1 ends there, although the "+" silk sits by the
  lower pad. Positions +/-0.15 mm from the render.
- Library pieces: `ProtoSupplies_PSB-1` (full carrier, pads named by net, no 3D), `ProtoSupplies_PSB-1_DCKit` (same
  pads plus the stock 3D models of the kit parts in place), `ProtoSupplies_PSB-1_Grid` (grid only, no copper graphics,
  for the layout), `PSB-1_Header_2x20_Breakout` and `PSB-1_Header_2x10_Staggered_Breakout` (pin 1 at the origin).
  Pad names: `H1-H40`, `K1-K20`, `G`, `V1-V7` (left to right, the jumper feeds V3), `VIN`, `LED`, `a<row>`..`f<row>`
  (rows 1-38). Copper lines in the carrier footprints only illustrate the buses.
- `projects/psb-1` is the board redrawn: schematic (kit parts and headers, buses as labels), `psb-1.kicad_pcb` with the
  kit fitted and `psb-1-bare.kicad_pcb` with the kit parts DNP. All bus, strip, breakout and input traces are tracks;
  ERC is clean and DRC is clean apart from the jack and LED courtyards touching, as on the real board.
  `lib/3d/ProtoSupplies_PSB-1.step` (bare) and `ProtoSupplies_PSB-1_DCKit.step` are exported from the two boards.
- **Still unverified:** whether the seven V band segments are joined (drawn separate; `V_COMMON`), and whether the
  two pads of a feed pair sit on one copper strip (drawn separate; `FEED_PAIRS_JOINED` is reserved, not yet wired in).

## Sharp PC900V (PC900V0NSZXF) OPIC photocoupler

- IRED coupled to an OPIC detector with a built-in regulator and amplifier: digital open-collector output, "normal
  OFF" (output high with no LED current, low above the threshold IFHL of about 1.1 mA typ., 2 mA max), TTL/LSTTL
  compatible, VCC 3-15 V, IOL up to 16 mA at 0.4 V, tPHL/tPLH 2-6 us. 5 kVrms isolation. Sharp recommends 10 nF or
  more between VCC and GND close to the device and warns against taking any pin below GND.
- 6-pin DIP: body 7.12 x 6.5 mm, 7.62 mm row spacing, 2.54 mm pitch, 0.5 x 0.6 mm leads 2.9 mm long; pins 1 anode,
  2 cathode, 3 NC, 4 VO, 5 GND, 6 VCC (Sharp sheet D2-A05302EN, outline 1). Stock `Package_DIP:DIP-6_W7.62mm`
  matches; the SMT gull-wing variants (PC900V0NIPXF) use `Package_DIP:SMDIP-6_W9.53mm` instead.
- The symbol draws the LED, the isolation barrier and the inverting output; the NC pin sits on the bottom edge as
  type no-connect.

## Toshiba TLP2962 photocoupler

- IRED coupled to a high-speed photo-IC: inverting open-collector output (LED on = output low), 15 MBd typ., input
  threshold 5 mA max, VCC 2.7-5.5 V, 4 mA supply, internal Faraday shield (20 kV/us common-mode immunity), 5 kVrms
  isolation, -40 to 125 C. Toshiba asks for a 0.1 uF ceramic between pins 8 and 5 within 1 cm of the pins.
- 8-pin DIP 11-10C4S: body 9.66 x 6.4 mm, 7.62 mm row, 2.54 mm pitch, 0.5 x 0.25 mm leads; pins 2 anode, 3 cathode,
  5 GND, 6 VO, 8 VCC, 1/4/7 NC (Toshiba sheet rev 4.0, 2016-12-14). Stock `Package_DIP:DIP-8_W7.62mm` matches.

