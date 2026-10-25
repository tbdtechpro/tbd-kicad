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
| TK103 PCM5102A I2S DAC | `TK103_PCM5102A_I2S_DAC` | `TK103_Module_RA_Header` + STEP | exact (vendor STEP) |
| MIDI shield (K194725ASJH) | `MIDI_Shield_DIN5x3_6N138` | stock `Module:Arduino_UNO_R3_WithMountingHoles` | exact (UNO header pattern) |
| ElectroCookie full breadboard | none (mechanical) | `ElectroCookie_Breadboard_Full` | outline/holes exact, rail length approximate |

Redistributable vendored sources live in `lib/vendor/` (Teensy: MIT; Espressif: CC-BY-SA 4.0); 3D models in `lib/3d/`. Vendor documents and models without redistribution terms (DFRobot CAD/PDFs, lcdwiki drawing, Waveshare images, Lonely Binary guide and STEP) stay in the private overlay repo and are only linked here. Footprints reference models as
`${KIPRJMOD}/../../lib/3d/...`, which resolves for any project under `projects/<name>/`.

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
