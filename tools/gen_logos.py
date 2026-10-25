#!/usr/bin/env python3
"""Turn artwork into KiCad silkscreen logo footprints.

    python3 tools/gen_logos.py artwork/logos.json [outdir]

Each spec entry names a source image, how to pick the ink (light-on-dark, or red/alpha), an optional region of the
image, the output widths in mm and the potrace smoothing.  Ink is traced with potrace (GeoJSON backend), scaled,
and holes are fractured with KiCad's own polygon engine so every piece is one filled fp_poly on F.SilkS.  The
footprints carry no pads and are excluded from the BOM and position files, like KiCad's Image Converter output."""
import os, sys, json, uuid, subprocess, tempfile
import numpy as np
from PIL import Image, ImageDraw
import pcbnew

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def f(x):
    s = ('%.4f' % x).rstrip('0').rstrip('.')
    return '0' if s in ('-0', '', '-') else s


def ink_mask(path, mode):
    a = np.array(Image.open(path).convert('RGBA')).astype(int)
    if mode == 'light':                       # white/colour graphics on a black background
        return (a[..., 3] > 128) & (a[..., :3].max(axis=2) > 90)
    if mode == 'red':                         # red artwork on transparent/white
        return (a[..., 3] > 128) & (a[..., 0] > 120) & (a[..., 1] < 140)
    if mode == 'dark':                        # black mask on white
        return (a[..., 3] > 128) & (a[..., :3].max(axis=2) < 128)
    raise ValueError(mode)


def region(mask, spec):
    """Restrict a mask to a named region: x/y limits in pixels, or 'right_top' / 'right_bottom' split at the gap."""
    m = mask.copy()
    r = spec.get('region')
    if not r:
        return m
    if 'x_max' in r:
        m[:, r['x_max']:] = False
    if 'x_min' in r:
        m[:, :r['x_min']] = False
    if r.get('split') in ('top', 'bottom'):   # split the remaining ink at the widest horizontal gap
        rows = np.where(m.any(axis=1))[0]
        gaps = [(rows[i + 1] - rows[i], rows[i], rows[i + 1]) for i in range(len(rows) - 1) if rows[i + 1] - rows[i] > 5]
        g = max(gaps)
        cut = (g[1] + g[2]) // 2
        if r['split'] == 'top':
            m[cut:, :] = False
        else:
            m[:cut, :] = False
    return m


def trace(mask, alphamax, turd):
    ys, xs = np.where(mask)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    crop = mask[y0:y1, x0:x1]
    with tempfile.TemporaryDirectory() as d:
        pbm, gj = os.path.join(d, 'in.pbm'), os.path.join(d, 'out.json')
        Image.fromarray(np.where(crop, 0, 255).astype(np.uint8)).save(pbm)
        subprocess.run(['potrace', '-b', 'geojson', '-a', str(alphamax), '-O', '0.2', '-t', str(turd), '-o', gj, pbm],
                       check=True, capture_output=True)
        feats = json.load(open(gj))['features']
    polys = []
    for ft in feats:
        rings = ft['geometry']['coordinates']
        polys.append([[(x, crop.shape[0] - y) for x, y in ring] for ring in rings])   # potrace y is up; flip to y-down
    return polys, crop.shape[1], crop.shape[0]


def fracture(polys, scale, w_px, h_px):
    """Scale to mm, centre on the bounding box, fracture holes, return list of point lists (mm)."""
    ps = pcbnew.SHAPE_POLY_SET()
    for rings in polys:
        for k, ring in enumerate(rings):
            chain = pcbnew.SHAPE_LINE_CHAIN()
            for x, y in ring:
                chain.Append(pcbnew.VECTOR2I(int(round((x - w_px / 2) * scale * 1e6)), int(round((y - h_px / 2) * scale * 1e6))))
            chain.SetClosed(True)
            if k == 0:
                ps.AddOutline(chain)
            else:
                ps.AddHole(chain)
    try:
        ps.Fracture()
    except TypeError:
        ps.Fracture(pcbnew.SHAPE_POLY_SET.PM_FAST)
    out = []
    for i in range(ps.OutlineCount()):
        o = ps.Outline(i)
        out.append([(o.CPoint(j).x / 1e6, o.CPoint(j).y / 1e6) for j in range(o.PointCount())])
    return out


def footprint(name, descr, polys_mm, layer='F.SilkS'):
    U = lambda: str(uuid.uuid4())
    lines = [f'(footprint "{name}" (version 20241229) (generator "pcbnew") (generator_version "9.0") (layer "F.Cu")',
             f'\t(descr "{descr}")', '\t(tags "logo silkscreen")',
             f'\t(property "Reference" "G***" (at 0 0 0) (layer "F.Fab") (hide yes) (uuid "{U()}") (effects (font (size 1 1) (thickness 0.15))))',
             f'\t(property "Value" "{name}" (at 0 0 0) (layer "F.Fab") (hide yes) (uuid "{U()}") (effects (font (size 1 1) (thickness 0.15))))',
             f'\t(property "Footprint" "" (at 0 0 0) (layer "F.Fab") (hide yes) (uuid "{U()}") (effects (font (size 1 1) (thickness 0.15))))',
             f'\t(property "Datasheet" "" (at 0 0 0) (layer "F.Fab") (hide yes) (uuid "{U()}") (effects (font (size 1 1) (thickness 0.15))))',
             f'\t(property "Description" "{descr}" (at 0 0 0) (layer "F.Fab") (hide yes) (uuid "{U()}") (effects (font (size 1 1) (thickness 0.15))))',
             '\t(attr board_only exclude_from_pos_files exclude_from_bom)']
    for pts in polys_mm:
        xy = ' '.join(f'(xy {f(x)} {f(y)})' for x, y in pts)
        lines.append(f'\t(fp_poly (pts {xy}) (stroke (width 0) (type solid)) (fill yes) (layer "{layer}") (uuid "{U()}"))')
    lines += ['\t(embedded_fonts no)', ')']
    return '\n'.join(lines) + '\n'


def main():
    spec_path = sys.argv[1]
    base = os.path.dirname(os.path.abspath(spec_path))
    outdir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, 'lib', 'tbd.pretty')
    os.makedirs(outdir, exist_ok=True)
    for spec in json.load(open(spec_path)):
        mask = region(ink_mask(os.path.join(base, spec['image']), spec['ink']), spec)
        polys, w_px, h_px = trace(mask, spec.get('alphamax', 1.0), spec.get('turdsize', 8))
        for width in spec['widths']:
            scale = width / w_px
            polys_mm = fracture(polys, scale, w_px, h_px)
            name = f"{spec['name']}_{f(width)}mm"
            descr = f"{spec['description']} Silkscreen logo, {f(width)} x {f(h_px * scale)} mm, {len(polys_mm)} polygons."
            open(os.path.join(outdir, name + '.kicad_mod'), 'w').write(footprint(name, descr, polys_mm))
            print(f'{name}: {f(width)} x {f(h_px * scale)} mm, {sum(len(p) for p in polys_mm)} points')


if __name__ == '__main__':
    main()
