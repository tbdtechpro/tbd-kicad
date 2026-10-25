"""Dump an Eagle .brd: outline wires (layer 20), element placements, through-hole pads with net names, holes."""
import sys, math, xml.etree.ElementTree as ET
root = ET.parse(sys.argv[1]).getroot()
board = root.find('drawing/board')
pk = {}
for lib in board.findall('libraries/library'):
    for p in lib.findall('packages/package'):
        pk[(lib.get('name'), p.get('name'))] = p
def rot_of(s):
    if not s: return 0.0, False
    m = s.startswith('M'); s = s.lstrip('MSR'); return float(s or 0), m
def xf(ex, ey, ang, mir, x, y):
    if mir: x = -x
    a = math.radians(ang); c, s = math.cos(a), math.sin(a)
    return ex + x*c - y*s, ey + x*s + y*c
print('== outline (plain layer 20)')
for w in board.findall('plain/wire'):
    if w.get('layer') == '20':
        print('  wire', w.get('x1'), w.get('y1'), w.get('x2'), w.get('y2'), 'curve', w.get('curve'))
for c in board.findall('plain/circle'):
    if c.get('layer') == '20': print('  circle', c.get('x'), c.get('y'), c.get('radius'))
for h in board.findall('plain/hole'):
    print('  hole', h.get('x'), h.get('y'), h.get('drill'))
nets = {}
for sgn in board.findall('signals/signal'):
    for cr in sgn.findall('contactref'):
        nets[(cr.get('element'), cr.get('pad'))] = sgn.get('name')
print('== elements')
for e in board.findall('elements/element'):
    ang, mir = rot_of(e.get('rot'))
    ex, ey = float(e.get('x')), float(e.get('y'))
    p = pk[(e.get('library'), e.get('package'))]
    tht = p.findall('pad'); holes = p.findall('hole'); smd = p.findall('smd')
    l20 = [w for w in p.findall('wire') if w.get('layer')=='20'] + [c for c in p.findall('circle') if c.get('layer')=='20']
    print(f"  {e.get('name')} value={e.get('value')!r} pkg={e.get('package')} at ({ex},{ey}) rot={e.get('rot')} tht={len(tht)} smd={len(smd)} holes={len(holes)} l20={len(l20)}")
    for pad in tht:
        x, y = xf(ex, ey, ang, mir, float(pad.get('x')), float(pad.get('y')))
        print(f"     pad {pad.get('name')} net={nets.get((e.get('name'), pad.get('name')))} ({x:.3f},{y:.3f}) drill={pad.get('drill')} dia={pad.get('diameter')} shape={pad.get('shape')}")
    for h in holes:
        x, y = xf(ex, ey, ang, mir, float(h.get('x')), float(h.get('y')))
        print(f"     hole ({x:.3f},{y:.3f}) drill={h.get('drill')}")
    for w in l20:
        if w.tag == 'circle':
            x, y = xf(ex, ey, ang, mir, float(w.get('x')), float(w.get('y')))
            print(f"     l20 circle ({x:.3f},{y:.3f}) r={w.get('radius')}")
        else:
            x1, y1 = xf(ex, ey, ang, mir, float(w.get('x1')), float(w.get('y1'))); x2, y2 = xf(ex, ey, ang, mir, float(w.get('x2')), float(w.get('y2')))
            print(f"     l20 wire ({x1:.3f},{y1:.3f})-({x2:.3f},{y2:.3f}) curve={w.get('curve')}")
    if e.get('name').startswith(('JP','J','CONN','HEADER')) or tht:
        pass
print('== silkscreen texts (plain, layers 21/22)')
for t in board.findall('plain/text'):
    if t.get('layer') in ('21','22','25','26','51'):
        print(f"  L{t.get('layer')} ({t.get('x')},{t.get('y')}) rot={t.get('rot')} {t.text!r}")
