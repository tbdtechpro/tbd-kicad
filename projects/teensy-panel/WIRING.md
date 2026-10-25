# teensy-panel: wiring on the ElectroCookie board

Teensy 4.1 socketed with the left header in **C1-C24** and the right header in **G1-G24**, micro-USB at row 1,
micro-SD at row 24. Each row's A-E holes are one strip, so a Teensy pin in column C is reachable at **A** or **B**
of the same row; a pin in column G is reachable at **H, I or J**.

Pin assignments are the ones tested in cheap-comp-midi-pcb (`ui/README.md`, `xtragravy/bench/teensy41/README.md`).

## Teensy pin to hole

| Teensy | Row | Free holes | Signal |
|---|---|---|---|
| GND | C1 | A1, B1 | GND |
| D2 | C4 | A4, B4 | ENC_CLK |
| D3 | C5 | A5, B5 | ENC_DT |
| D4 | C6 | A6, B6 | ENC_SW |
| D7 (OUT1A) | C9 | A9, B9 | I2S_DIN |
| D8 | C10 | A10, B10 | LCD_RST |
| D9 | C11 | A11, B11 | LCD_DC |
| D10 | C12 | A12, B12 | LCD_CS |
| D11 (MOSI) | C13 | A13, B13 | SPI_MOSI |
| 3.3 V | C15 | A15, B15 | +3V3 |
| VIN | G1 | H1, I1, J1 | not used |
| GND | G2 | H2, I2, J2 | GND |
| 3.3 V | G3 | H3, I3, J3 | +3V3 |
| D21 (BCLK1) | G6 | H6, I6, J6 | I2S_BCK |
| D20 (LRCLK1) | G7 | H7, I7, J7 | I2S_LRCK |
| D13 (SCK) | G14 | H14, I14, J14 | SPI_SCK |
| GND | G15 | H15, I15, J15 | GND |

Full column map: C1 GND, C2 D0, C3 D1, ... C14 D12, C15 3.3V, C16 D24 ... C24 D32;
G1 VIN, G2 GND, G3 3.3V, G4 D23, G5 D22, ... G14 D13, G15 GND, G16 D41 ... G24 D33.

## Module connections

The jumper wires are routed hole-to-hole in `WIRES.md` (generated with the PCB; 20 wires with cut lengths). Summary:

| Module pin | Net | From hole | To hole |
|---|---|---|---|
| GC9A01 VCC / GND | +3V3 / GND | right + rail (row 31) / right - rail (row 39) | I32 / G33 |
| GC9A01 SCL | SPI_SCK | H14 | H34 |
| GC9A01 SDA / DC / CS / RST | SPI_MOSI / LCD_DC / LCD_CS / LCD_RST | A13 / A11 / A12 / A10 | I35 / I36 / I37 / I38 |
| KY-040 + / GND | +3V3 / GND | right + rail (row 53) / right - rail (row 54) | H57 / I56 |
| KY-040 CLK / DT / SW | ENC_CLK / ENC_DT / ENC_SW | A4 / A5 / A6 | I60 / I59 / I58 |
| TK103 3V3 / GND | +3V3 / GND | left + rail (row 58) / left - rail (row 57) | C52 / C53 |
| TK103 BCK / LRCK / DIN | I2S_BCK / I2S_LRCK / I2S_DIN | H6 / H7 / A9 | E51 / E49 / B50 |
| TK103 XSMT | +3V3 | E52 (its own 3V3 strip) | D48 |
| Rails | +3V3 / GND | J3 / J2 | right + rail (row 3) / right - rail (row 2); bridge both end jumpers to feed the left rails |

## Suggested socket positions (as placed in `teensy-panel.kicad_pcb`)

- **GC9A01**: 7-pin socket in **J32-J38** (J32 VCC, J33 GND, J34 SCL, J35 SDA, J36 DC, J37 CS, J38 RST). The round body then sits over the board centre,
  overhanging the A-side edge by about 2.5 mm. Wire from the I/H holes of rows 32-38.
- **TK103**: 6-pin socket in **A48-A53** (pin 1 = GND at A53, XSMT at A48); the module stands up facing the left rails.
  Wire from B48-B53.
- **KY-040**: 5-pin socket in **J56-J60** (pin 1 = GND at J56); the module stands up facing the right rails.
  Wire from H/I of rows 56-60.
- Rails: feed the left rails from A15 (+ rail = 3.3 V) and A1 (- rail = GND), the right rails from J3 and J2.

The PCB also carries the female sockets as PCB-only footprints (they are not in the schematic, so do not run
"Update PCB from Schematic" without re-adding them): J1/J2 = the two 24-pin Teensy sockets at C1 and G1, J3 = 7-pin
at J32, J4 = 6-pin at A48, J5 = 5-pin at J56. The 3D view shows the Teensy and modules raised on them.

Open the PCB in KiCad to see the wiring as a ratsnest: every airwire is one jumper wire to solder. The module
footprints overlap the breadboard pads on purpose, so ignore DRC on this board.
