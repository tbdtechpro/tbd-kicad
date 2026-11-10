"""Convert the user's VRML 1.0 DIN-5 socket model into the library's VRML 2.0 (0.1 inch units) and, under FreeCAD,
a STEP, in the DIN-5_180deg_PCB_Socket footprint frame: pin 2 at the origin, opening toward footprint -Y, board at
z = 0. The housing is scaled to the measured socket (midi_geometry.DIN) and the pins and lugs are redrawn at the pad positions. Source frame (metres): x lateral, y up with the board surface at y = -8.9 mm, +z toward the face, pin row at
z = 6.5 mm with pin 2 at x = -1.55 mm. Run: python3 tools/convert_din5_vrml.py <source.wrl>  (VRML only), or
freecad.cmd tools/convert_din5_vrml.py <source.wrl> for VRML + STEP."""
import os, re, sys
SRC = sys.argv[-1]
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'lib', '3d', 'DIN-5_PCB_Socket')
BLACK, SILVER = (0.10, 0.10, 0.10), (0.78, 0.78, 0.80)
PIN2 = (-1.55, -8.9, 6.5)                               # source mm: pin 2 x, board surface y, pin row z


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import midi_geometry as MG
NATIVE = (21.2, 12.5, 19.0)                             # the source socket: width, face ahead of the pin row, height
TARGET = (MG.DIN['body_w'], -MG.DIN['face_from_pin2'], MG.DIN['body_h'])   # the sockets on the shield (photos/calipers)
SCALE = tuple(t / n for t, n in zip(TARGET, NATIVE))


def transform(p):
    x, y, z = (v * 1000 for v in p)
    x3, y3, z3 = -(x - PIN2[0]), z - PIN2[2], y - PIN2[1]   # 3D frame: x right, y toward the face (fp -Y), z up
    return (x3 * SCALE[0], y3 * SCALE[1], z3 * SCALE[2])   # housing scaled to the measured socket


def parse(src):
    blocks = []
    for m in re.finditer(r'Coordinate3\s*\{\s*point\s*\[(.*?)\]\s*\}', src, re.S):
        pts = [transform(tuple(map(float, p.split()))) for p in m.group(1).strip().rstrip(',').split(',') if p.strip()]
        body = re.search(r'IndexedFaceSet\s*\{(.*?)\n\}', src[m.end():], re.S).group(1)
        idx = [int(v) for v in re.search(r'coordIndex\s*\[(.*?)\]', body, re.S).group(1).replace('\n', ' ').split(',') if v.strip()]
        faces, cur = [], []
        for v in idx:
            if v == -1:
                if cur: faces.append(cur); cur = []
            else: cur.append(v)
        if cur: faces.append(cur)
        blocks.append((pts, faces))
    # drop the source's pin stubs (entirely below the board) and add pins and lugs at the footprint's pad positions
    blocks = [b for b in blocks if max(pt[2] for pt in b[0]) > 0]
    def leg(x, y, w, d, z0, z1):
        pts = [(x - w, y - d, z0), (x + w, y - d, z0), (x + w, y + d, z0), (x - w, y + d, z0),
               (x - w, y - d, z1), (x + w, y - d, z1), (x + w, y + d, z1), (x - w, y + d, z1)]
        faces = [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]
        return (pts, faces)
    for num, (x, y) in MG.DIN['pins'].items():
        blocks.append(leg(x, -y, 0.35, 0.35, -3.0, 2.5))
    for x, y in MG.DIN['lugs']:
        blocks.append(leg(x, -y, 0.5, 0.25, -3.0, 1.5))
    return blocks


def colour_of(i, pts):
    """Housing blocks are the two big ones; everything else is metal (pins, lugs, contacts)."""
    return BLACK if len(pts) > 300 else SILVER


def write_vrml(blocks, path):
    out = ['#VRML V2.0 utf8', '# DIN-5 180-degree PCB socket, converted from the user library model; units 0.1 inch']
    for i, (pts, faces) in enumerate(blocks):
        c = colour_of(i, pts)
        out.append('Shape { appearance Appearance { material Material { diffuseColor %.3f %.3f %.3f specularColor 0.3 0.3 0.3 shininess 0.3 } }' % c)
        out.append(' geometry IndexedFaceSet { solid FALSE coord Coordinate { point [')
        out.append(','.join('%.4f %.4f %.4f' % (x / 2.54, y / 2.54, z / 2.54) for x, y, z in pts))
        out.append('] } coordIndex [')
        out.append(','.join(','.join(str(v) for v in f) + ',-1' for f in faces))
        out.append('] } }')
    open(path, 'w').write('\n'.join(out) + '\n')


def write_step(blocks, path):
    import FreeCAD, Part, Mesh
    shapes = []
    for i, (pts, faces) in enumerate(blocks):
        tris = []
        for f in faces:
            for k in range(1, len(f) - 1):
                tris.append((pts[f[0]], pts[f[k]], pts[f[k + 1]]))
        m = Mesh.Mesh(tris)
        sh = Part.Shape(); sh.makeShapeFromMesh(m.Topology, 0.02)
        try:
            sh = Part.makeSolid(sh)
        except Exception:
            pass
        shapes.append(sh)
    doc = FreeCAD.newDocument('din')
    for i, sh in enumerate(shapes):
        o = doc.addObject('Part::Feature', 'b%d' % i); o.Shape = sh
    import Import
    Import.export(doc.Objects, path)


blocks = parse(open(SRC).read())
write_vrml(blocks, OUT + '.wrl'); print('wrote', OUT + '.wrl', len(blocks), 'shapes')
try:
    import FreeCAD
    write_step(blocks, OUT + '.step'); print('wrote', OUT + '.step')
except ImportError:
    print('no FreeCAD: STEP not written')
