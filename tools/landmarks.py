"""kâşif — pastel low-poly landmark miniatures, built procedurally with Blender (bpy) and exported as .glb.
Run: python3 landmarks.py <outdir>
Every model stands on a round pastel plinth (board-game piece look), base at z=0, Z up (glTF exporter turns it Y-up).
"""
import bpy, bmesh, math, sys, os
from mathutils import Vector, Matrix

OUT = sys.argv[1] if len(sys.argv) > 1 else 'out'
os.makedirs(OUT, exist_ok=True)

PAL = {
    'cream': '#F6EFE3', 'sand': '#E9D3AE', 'sand2': '#DCC197', 'stone': '#DAD4CA', 'white': '#FBFAF7',
    'terra': '#E8A592', 'rose': '#F2B8C6', 'blush': '#EBC2B5', 'lav': '#B9B0E8', 'lav2': '#9F96D6', 'slate': '#8E8AAE',
    'mint': '#A8DCC7', 'green': '#9CCB9A', 'green2': '#7FB98A', 'sky': '#A9CBEB', 'gold': '#F1CE7E', 'red': '#E58F84',
    'wood': '#B58E73', 'bronze': '#CFA98A', 'copper': '#9ED3C2', 'dome': '#A7AACB', 'ink': '#6E6A8E', 'plinth': '#EDE7F6',
}
_mats = {}
def mat(key):
    if key in _mats: return _mats[key]
    h = PAL[key].lstrip('#'); rgb = [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    m = bpy.data.materials.new(key); m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = (*lin, 1); b.inputs['Roughness'].default_value = 0.85
    try: b.inputs['Metallic'].default_value = 0.0
    except Exception: pass
    _mats[key] = m; return m

def _fin(o, m, rot=None):
    o.data.materials.append(mat(m))
    if rot: o.rotation_euler = rot
    return o

def box(sx, sy, sz, x=0, y=0, z=0, m='cream', rot=None):
    """box with its BOTTOM at z"""
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z + sz / 2))
    o = bpy.context.object; o.scale = (sx, sy, sz); return _fin(o, m, rot)

def cyl(r, h, x=0, y=0, z=0, m='cream', v=12, r2=None, rot=None):
    """cylinder / cone / frustum with its BOTTOM at z (r2 = top radius)"""
    if r2 is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=v, radius=r, depth=h, location=(x, y, z + h / 2))
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=v, radius1=r, radius2=r2, depth=h, location=(x, y, z + h / 2))
    return _fin(bpy.context.object, m, rot)

def cone(r, h, x=0, y=0, z=0, m='cream', v=12, rot=None): return cyl(r, h, x, y, z, m, v, 0, rot)

def sph(r, x=0, y=0, z=0, m='cream', seg=14, ring=8, sz=1.0):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=ring, radius=r, location=(x, y, z))
    o = bpy.context.object; o.scale = (1, 1, sz); return _fin(o, m)

def dome(r, x=0, y=0, z=0, m='dome', seg=16, sz=1.0):
    """upper hemisphere with its base circle at z"""
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=10, radius=r)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -1e-4], context='VERTS')
    edges = [e for e in bm.edges if e.is_boundary]
    if edges: bmesh.ops.contextual_create(bm, geom=edges)
    me = bpy.data.meshes.new('dome'); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new('dome', me); bpy.context.collection.objects.link(o)
    o.location = (x, y, z); o.scale = (1, 1, sz); return _fin(o, m)

def prism(w, d, h, x=0, y=0, z=0, m='terra', rot=None):
    """triangular gable prism: ridge along Y, width w (X), depth d (Y), height h, bottom at z"""
    bm = bmesh.new()
    pts = [(-w/2, -d/2, 0), (w/2, -d/2, 0), (0, -d/2, h), (-w/2, d/2, 0), (w/2, d/2, 0), (0, d/2, h)]
    vs = [bm.verts.new(p) for p in pts]
    for f in [(0, 1, 2), (5, 4, 3), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)]: bm.faces.new([vs[i] for i in f])
    me = bpy.data.meshes.new('prism'); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new('prism', me); bpy.context.collection.objects.link(o); o.location = (x, y, z)
    return _fin(o, m, rot)

def ring(r_out, r_in, h, x=0, y=0, z=0, m='cream', v=32, sx=1, sy=1):
    """flat annulus (tube) with bottom at z; sx/sy squash it into an ellipse"""
    bm = bmesh.new()
    def circle(r, zz): return [bm.verts.new((math.cos(2*math.pi*i/v)*r*sx, math.sin(2*math.pi*i/v)*r*sy, zz)) for i in range(v)]
    ob, ot, ib, it = circle(r_out, 0), circle(r_out, h), circle(r_in, 0), circle(r_in, h)
    for i in range(v):
        j = (i + 1) % v
        bm.faces.new([ob[i], ob[j], ot[j], ot[i]]); bm.faces.new([ib[j], ib[i], it[i], it[j]])
        bm.faces.new([ot[i], ot[j], it[j], it[i]]); bm.faces.new([ob[j], ob[i], ib[i], ib[j]])
    me = bpy.data.meshes.new('ring'); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new('ring', me); bpy.context.collection.objects.link(o); o.location = (x, y, z)
    return _fin(o, m)

def plinth(r=1.0, m='plinth', top='mint'):
    cyl(r, .08, m=m, v=40); cyl(r * .97, .035, z=.08, m=top, v=40)
    return .115

def tree(x, y, z, s=1.0, m='green'):
    cyl(.025 * s, .12 * s, x, y, z, 'wood', 6); cone(.09 * s, .22 * s, x, y, z + .08 * s, m, 7)

def palm(x, y, z, s=1.0):
    cyl(.02 * s, .4 * s, x, y, z, 'wood', 6, r2=.015 * s)
    for k in range(6):
        a = k * math.pi / 3
        box(.24 * s, .05 * s, .012 * s, x + math.cos(a) * .1 * s, y + math.sin(a) * .1 * s, z + .37 * s, 'green2', rot=(0, .35, a))

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True); _mats.clear()

def export(name):
    for o in bpy.context.scene.objects: o.select_set(o.type == 'MESH')
    bpy.context.view_layer.objects.active = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
    bpy.ops.object.join()
    o = bpy.context.object; o.name = name
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    bpy.ops.object.shade_flat()
    path = os.path.join(OUT, name + '.glb')
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_apply=True, export_yup=True,
                              export_texcoords=False, export_normals=True, export_materials='EXPORT', export_extras=False)
    print('exported', name, os.path.getsize(path))

# ----------------------------------------------------------------------------------------- landmarks
def ayasofya():
    z = plinth(1.05, top='mint')
    box(1.5, 1.3, .42, z=z, m='blush'); box(1.1, 1.62, .32, z=z, m='blush')
    box(.9, .9, .2, z=z + .42, m='blush')
    for sx in (-1, 1):
        for sy in (-1, 1): box(.2, .2, .26, sx * .5, sy * .5, z + .32, 'terra')
    cyl(.4, .1, z=z + .62, m='blush', v=24)
    dome(.42, z=z + .72, sz=.62, seg=24)
    for sy in (-1, 1): dome(.3, 0, sy * .45, z + .5, sz=.55)
    for sx, sy in ((-.78, -.7), (.78, -.7), (-.78, .7), (.78, .7)):
        cyl(.055, 1.15, sx, sy, z, 'cream', 10); ring(.085, .05, .03, sx, sy, z + .78, 'cream', 12)
        ring(.085, .05, .03, sx, sy, z + 1.0, 'cream', 12); cone(.065, .3, sx, sy, z + 1.15, 'dome', 10)
    for x in (-.95, .95): tree(x, 0, z, .9)

def peribacasi():
    z = plinth(1.0, top='sand')
    for x, y, h, r in ((-.35, .1, .95, .26), (.18, -.2, 1.2, .24), (.48, .3, .75, .22), (-.05, .45, .6, .2)):
        cyl(r, h, x, y, z, 'sand', 9, r2=r * .35)
        cyl(r * .55, .12, x, y, z + h - .02, 'wood', 9, r2=r * .2)
    for x, y in ((-.4, -.25), (.08, -.48)): box(.05, .02, .08, x, y - .2, z + .2, 'ink')
    # hot-air balloons
    for bx, by, bz, s, c in ((.1, .1, 1.75, 1, 'rose'), (-.55, -.2, 1.4, .7, 'lav'), (.6, -.35, 1.2, .55, 'gold')):
        sph(.24 * s, bx, by, bz, c, 12, 8, 1.15)
        cyl(.12 * s, .1 * s, bx, by, bz - .3 * s, c, 12, r2=.05 * s)
        box(.08 * s, .08 * s, .06 * s, bx, by, bz - .42 * s, 'wood')

def kolezyum():
    z = plinth(1.1, top='green')
    sx, sy, R, n = 1.0, .78, .86, 30
    ring(R, R - .22, .04, z=z, m='stone', sx=sx, sy=sy)
    for tier in range(3):
        zz = z + .04 + tier * .2
        for i in range(n):
            a = 2 * math.pi * i / n
            if tier == 2 and (a < .35 or a > 2.6): continue      # ruined side
            px, py = math.cos(a) * R * sx, math.sin(a) * R * sy
            box(.065, .14, .16, px, py, zz, 'sand', rot=(0, 0, math.atan2(py / sy ** 2, px / sx ** 2)))
        ring(R + .02, R - .2, .04, z=zz + .16, m='sand2', sx=sx, sy=sy) if tier < 2 else None
    for i in range(n):
        a = 2 * math.pi * i / n
        if .35 <= a <= 2.6: box(.16, .1, .12, math.cos(a) * (R - .02) * sx, math.sin(a) * (R - .02) * sy, z + .64, 'sand2', rot=(0, 0, a))
    ring(R - .2, R - .45, .1, z=z, m='sand2', sx=sx, sy=sy)
    box(.7, .38, .03, z=z + .04, m='blush')

def eyfel():
    z = plinth(.95, top='green')
    c = 'bronze'
    for sx in (-1, 1):
        for sy in (-1, 1):
            o = box(.12, .12, .78, sx * .32, sy * .32, z, c); o.rotation_euler = (sy * .33, -sx * .33, 0)
    box(.74, .74, .07, z=z + .62, m=c)
    for s in (-1, 1):
        prism(.58, .06, .14, 0, s * .34, z + .48, 'bronze')
        prism(.58, .06, .14, s * .34, 0, z + .48, 'bronze', rot=(0, 0, math.pi / 2))
    cyl(.3, .78, z=z + .69, m=c, v=4, r2=.12, rot=(0, 0, math.pi / 4))
    box(.32, .32, .05, z=z + 1.45, m=c)
    cyl(.14, .72, z=z + 1.5, m=c, v=4, r2=.035, rot=(0, 0, math.pi / 4))
    cyl(.035, .18, z=z + 2.2, m='cream', v=6); cone(.02, .14, z=z + 2.38, m='gold', v=6)
    for x, y in ((-.7, .2), (.7, -.2), (-.6, -.45), (.62, .45)): tree(x, y, z, .9)

def sagrada():
    z = plinth(1.0, top='sand')
    box(1.0, .7, .55, z=z, m='sand'); prism(1.0, .7, .3, z=z + .55, m='sand2', rot=(0, 0, math.pi / 2))
    def spire(x, y, h, r, tip):
        cyl(r, h * .55, x, y, z, 'sand', 10, r2=r * .82); cyl(r * .82, h * .45, x, y, z + h * .55, 'sand', 10, r2=r * .12)
        for k in range(3): ring(r * .9 - k * .02, r * .6, .02, x, y, z + h * (.3 + k * .18), 'sand2', 10)
        sph(r * .45, x, y, z + h + r * .2, tip, 8, 6)
    for x in (-.36, -.12, .12, .36): spire(x, -.42, 1.35 + (abs(x) < .2) * .2, .1, 'gold')
    for x in (-.3, .3): spire(x, .4, 1.25, .1, 'rose')
    spire(0, .05, 2.05, .15, 'lav'); spire(-.32, .05, 1.6, .11, 'mint'); spire(.32, .05, 1.6, .11, 'mint')
    for x in (-.7, .7): tree(x, -.5, z, .9)

def partenon():
    z = plinth(1.05, top='green')
    cyl(.95, .25, z=z, m='stone', v=9, r2=.8)            # acropolis rock
    z += .25
    for k, (w, d) in enumerate(((1.25, .72), (1.17, .64), (1.09, .56))): box(w, d, .04, z=z + k * .04, m='white')
    z += .12
    cols = [(-.5 + i * (1.0 / 7), s * .24) for i in range(8) for s in (-1, 1)] + [(s * .5, -.24 + j * .48 / 5) for s in (-1, 1) for j in range(1, 5)]
    for x, y in cols: cyl(.032, .42, x, y, z, 'white', 8)
    # ruined: one corner missing
    box(1.08, .54, .07, z=z + .42, m='cream'); box(1.04, .5, .04, z=z + .49, m='white')
    prism(.54, 1.04, .12, z=z + .53, m='cream', rot=(0, 0, math.pi / 2))
    for x, y in ((-.7, .45), (.75, -.4)): tree(x, y, z - .37, .8, 'green2')

def piramit():
    z = plinth(1.1, top='sand')
    cyl(.72, .85, -.2, .1, z, 'gold', 4, r2=0, rot=(0, 0, math.pi / 4))
    cyl(.55, .65, .55, -.35, z, 'sand', 4, r2=0, rot=(0, 0, math.pi / 4))
    cyl(.34, .4, .62, .55, z, 'sand2', 4, r2=0, rot=(0, 0, math.pi / 4))
    # sphinx
    box(.42, .12, .1, -.55, -.62, z, 'sand2'); box(.13, .13, .16, -.36, -.62, z + .06, 'sand2'); box(.1, .15, .04, -.36, -.62, z + .2, 'lav')
    for x, y in ((.95, .05), (-.9, .55)): palm(x, y, z, .8)

def kutubiye():
    z = plinth(1.0, top='sand')
    box(.42, .42, 1.25, z=z, m='terra')
    for zz in (.35, .7, 1.0): box(.44, .44, .04, z=z + zz, m='blush')
    for s in (-1, 1):
        box(.1, .02, .16, 0, s * .215, z + .8, 'mint'); box(.02, .1, .16, s * .215, 0, z + .8, 'mint')
    for i in range(4):
        for j in (-1, 0, 1): box(.06, .06, .07, j * .14 if i < 2 else (1 if i == 2 else -1) * .18, (1 if i == 0 else -1) * .18 if i < 2 else j * .14, z + 1.25, 'terra')
    box(.22, .22, .25, z=z + 1.25, m='terra'); dome(.12, z=z + 1.5, m='mint', sz=.8)
    for k, r in enumerate((.045, .035, .025)): sph(r, 0, 0, z + 1.63 + k * .075, 'gold', 8, 6)
    box(.9, .3, .2, .1, .45, z, 'blush')
    for x, y in ((-.65, -.3), (.65, -.35), (-.6, .5)): palm(x, y, z, .9)

def pagoda():
    z = plinth(1.0, top='green')
    box(.7, .7, .08, z=z, m='stone'); zz = z + .08
    for k in range(5):
        w = .5 - k * .07
        box(w, w, .2, z=zz, m='cream'); box(w * .9, .02, .1, 0, -w / 2 - .005, zz + .05, 'wood')
        cyl((w + .28) * .71, .09, z=zz + .2, m='red', v=4, r2=(w * .55) * .71, rot=(0, 0, math.pi / 4))
        zz += .29
    cyl(.025, .45, z=zz, m='gold', v=8)
    for k in range(5): ring(.05, .02, .015, 0, 0, zz + .08 + k * .06, 'gold', 8)
    # torii (Fushimi Inari)
    for x in (-.25, .25): cyl(.035, .5, x, -.75, z, 'red', 8)
    box(.7, .06, .05, 0, -.75, z + .5, 'red'); box(.6, .05, .04, 0, -.75, z + .4, 'red'); box(.78, .08, .03, 0, -.75, z + .55, 'ink')
    for x, y in ((-.7, .3), (.7, .35), (.65, -.2)): tree(x, y, z, .9, 'rose')     # sakura

def watarun():
    z = plinth(1.0, top='sky')
    box(1.2, 1.2, .1, z=z, m='white'); z2 = z + .1
    def prang(x, y, s, base):
        zz = base
        for k, (r, h, c) in enumerate(((.3, .18, 'white'), (.24, .16, 'lav'), (.19, .15, 'white'), (.15, .14, 'mint'), (.11, .13, 'white'))):
            cyl(r * s, h * s, x, y, zz, c, 12, r2=r * s * .85); zz += h * s
        cyl(.09 * s, .5 * s, x, y, zz, 'cream', 12, r2=.01 * s); sph(.02 * s, x, y, zz + .5 * s, 'gold', 6, 4)
    prang(0, 0, 1.25, z2)
    for sx in (-1, 1):
        for sy in (-1, 1): prang(sx * .45, sy * .45, .55, z2)
    for x in (-.85, .85): palm(x, .6, z, .75)

def ozgurluk():
    z = plinth(.9, top='green')
    cyl(.6, .1, z=z, m='stone', v=11); z += .1                 # star fort (simplified)
    box(.42, .42, .32, z=z, m='stone'); box(.34, .34, .32, z=z + .32, m='cream'); box(.4, .4, .05, z=z + .64, m='stone')
    z += .69; c = 'copper'
    cyl(.17, .72, z=z, m=c, v=10, r2=.1)                       # robe
    cyl(.1, .14, z=z + .72, m=c, v=10, r2=.07)                 # shoulders
    sph(.075, 0, 0, z + .93, c, 10, 8, 1.1)                     # head
    for k in range(7):
        a = -math.pi / 2 + (k - 3) * .38
        cone(.018, .14, math.cos(a) * .07, math.sin(a) * .07 - .01, z + .95, c, 5, rot=(math.sin(a) * -1.1, math.cos(a) * 1.1, 0))
    o = cyl(.035, .38, .1, 0, z + .78, c, 8); o.rotation_euler = (0, .25, 0)    # raised arm
    cyl(.04, .08, .19, 0, z + 1.13, c, 8); cone(.04, .1, .19, 0, z + 1.21, 'gold', 8)  # torch
    box(.04, .12, .16, -.14, .02, z + .5, c, rot=(0, -.2, 0))                    # tablet
    for x, y in ((-.62, .3), (.6, -.35)): tree(x, y, z - .79, .8)

def gunes():
    z = plinth(1.05, top='green')
    for k, w in enumerate((1.25, 1.02, .8, .6, .42)): box(w, w, .15, z=z + k * .15, m='sand' if k % 2 == 0 else 'sand2')
    box(.2, .1, .08, z=z + .75, m='terra')
    o = box(.18, .78, .03, 0, -.45, z + .28, 'terra'); o.rotation_euler = (-.83, 0, 0)
    for x, y in ((-.85, -.3), (.85, .35)): cyl(.06, .3, x, y, z, 'green2', 7, r2=.05)   # cacti

def machupicchu():
    z = plinth(1.1, top='green')
    o = cone(.55, 1.45, .25, .45, z, 'green2', 7); o.scale = (1, .8, 1)       # Huayna Picchu
    cone(.4, .9, -.45, .55, z, 'green', 6)
    for k in range(5):
        r = .95 - k * .12
        box(r * 1.6, .28, .06, -.1, -.35 + k * .07, z + k * .06, 'green' if k % 2 else 'green2')
    for x, y in ((-.5, -.25), (-.2, -.15), (.1, -.25), (.35, -.08), (-.35, .05)):
        box(.14, .11, .08, x, y, z + .3, 'stone'); prism(.14, .12, .07, x, y, z + .38, 'wood', rot=(0, 0, math.pi / 2))
    sph(.06, -.7, -.5, z + .06, 'cream', 8, 6)                                     # llama-ish
    box(.04, .03, .1, -.66, -.5, z + .06, 'cream')

def safranbolu():
    z = plinth(.95, top='green')
    box(.9, .7, .32, z=z, m='white')
    for x in (-.25, .25): box(.12, .02, .16, x, -.355, z + .06, 'ink')
    box(.16, .02, .24, 0, -.355, z, 'wood')
    box(1.06, .86, .34, z=z + .32, m='cream')                        # upper floor (çıkma)
    for x in (-.53, -.18, .18, .53): box(.03, .87, .34, x, 0, z + .32, 'wood')
    box(1.07, .87, .03, z=z + .32, m='wood'); box(1.07, .87, .03, z=z + .63, m='wood')
    for x in (-.35, 0, .35): box(.14, .02, .18, x, -.44, z + .4, 'sky')
    box(.42, .18, .3, 0, -.5, z + .34, 'cream'); box(.44, .2, .03, 0, -.5, z + .34, 'wood')   # cumba
    for x in (-.1, .1): box(.12, .02, .16, x, -.6, z + .4, 'sky')
    cyl(.82, .32, z=z + .66, m='terra', v=4, r2=.05, rot=(0, 0, math.pi / 4)); o = bpy.context.object; o.scale = (1.0, .82, 1)
    box(.08, .08, .2, .25, .15, z + .8, 'white')
    for x, y in ((-.7, -.4), (.72, .3)): tree(x, y, z, .9)

def bigben():
    z = plinth(.85, top='green')
    box(.36, .36, 1.15, z=z, m='sand')
    for zz in (.3, .6, .9): box(.38, .38, .03, z=z + zz, m='gold')
    box(.42, .42, .3, z=z + 1.15, m='sand2')
    for a in range(4):
        ang = a * math.pi / 2; dx, dy = math.cos(ang) * .215, math.sin(ang) * .215
        cyl(.13, .02, dx, dy, z + 1.3 - .01, 'white', 16, rot=(math.pi / 2, 0, ang + math.pi / 2)); bpy.context.object.location = (dx, dy, z + 1.3)
        cyl(.02, .025, dx * 1.04, dy * 1.04, z + 1.3, 'ink', 6, rot=(math.pi / 2, 0, ang + math.pi / 2)); bpy.context.object.location = (dx * 1.05, dy * 1.05, z + 1.3)
    box(.34, .34, .2, z=z + 1.45, m='sand')
    cyl(.27, .55, z=z + 1.65, m='slate', v=4, r2=.03, rot=(0, 0, math.pi / 4))
    for sx in (-1, 1):
        for sy in (-1, 1): cone(.03, .2, sx * .17, sy * .17, z + 1.62, 'gold', 4)
    cone(.02, .14, z=z + 2.2, m='gold', v=6)
    box(.9, .3, .32, -.6 + .3, .45, z, 'sand2'); prism(.3, .9, .12, -.3, .45, z + .32, 'slate', rot=(0, 0, math.pi / 2))

def tacmahal():
    z = plinth(1.1, top='green')
    box(1.3, 1.3, .1, z=z, m='white'); z += .1
    box(.8, .8, .5, z=z, m='white')
    for sx in (-1, 1): box(.02, .3, .32, sx * .405, 0, z + .04, 'lav'); box(.3, .02, .32, 0, sx * .405, z + .04, 'lav')
    cyl(.26, .12, z=z + .5, m='white', v=16); sph(.3, 0, 0, z + .72, 'white', 16, 10, 1.15)
    cone(.03, .2, z=z + 1.04, m='gold', v=6)
    for sx in (-1, 1):
        for sy in (-1, 1):
            cyl(.11, .08, sx * .28, sy * .28, z + .5, 'white', 8); dome(.1, sx * .28, sy * .28, z + .58, 'white', 10)
            cyl(.04, .85, sx * .58, sy * .58, z, 'white', 8, r2=.032); dome(.05, sx * .58, sy * .58, z + .85, 'white', 8)
            ring(.055, .03, .02, sx * .58, sy * .58, z + .45, 'cream', 8)
    box(.12, 1.0, .02, 0, -.95, z - .1, 'sky')                                      # reflecting pool
    for y in (-.6, -1.0): tree(-.25, y, z - .1, .7, 'green2'); tree(.25, y, z - .1, .7, 'green2')

def isa():
    z = plinth(1.0, top='green')
    o = cone(.85, 1.0, 0, 0, z, 'green2', 8); o.scale = (1, .75, 1)                  # Corcovado
    z += .95
    box(.16, .16, .14, z=z, m='stone'); z += .14
    cyl(.1, .62, z=z, m='white', v=10, r2=.07)
    box(.95, .08, .07, z=z + .52, m='white')
    for sx in (-1, 1): box(.08, .07, .06, sx * .47, 0, z + .5, 'white')
    sph(.06, 0, 0, z + .67, 'white', 10, 8, 1.15)

def opera():
    z = plinth(1.05, top='sky')
    box(1.3, .7, .12, z=z, m='blush')
    def shell(x, y, s, rot):
        o = sph(.36 * s, x, y, z + .12, 'white', 12, 8)
        o.scale = (.45, 1, 1.25); o.rotation_euler = (0, rot, 0)
    for k, (x, s) in enumerate(((-.42, 1), (-.18, .85), (.02, .7))): shell(x, -.12, s, -.5)
    for k, (x, s) in enumerate(((.25, .8), (.44, .65))): shell(x, .2, s, -.5)
    box(1.6, .5, .015, 0, -.6, z - .06, 'sky')

def basil():
    z = plinth(.95, top='stone')
    box(.9, .9, .3, z=z, m='terra')
    def onion(x, y, h, r, c):
        cyl(r * .75, h, x, y, z + .3, 'cream', 10); sph(r, x, y, z + .3 + h + r * .6, c, 12, 8, 1.2)
        cone(r * .55, r * 1.1, x, y, z + .3 + h + r * 1.4, c, 10); cone(.012, .12, x, y, z + .3 + h + r * 2.4, 'gold', 4)
    cyl(.15, .9, z=z + .3, m='terra', v=8); cone(.18, .45, z=z + 1.2, m='green', v=8); cone(.015, .12, z=z + 1.65, m='gold', v=4)
    for (x, y, c) in ((.3, .3, 'mint'), (-.3, .3, 'rose'), (.3, -.3, 'gold'), (-.3, -.3, 'lav')): onion(x, y, .3, .13, c)
    for (x, y, c) in ((0, .36, 'sky'), (0, -.36, 'red'), (.36, 0, 'green'), (-.36, 0, 'blush')): onion(x, y, .18, .1, c)

def burj():
    z = plinth(.85, top='sky')
    tiers = [(.3, .5), (.25, .45), (.2, .45), (.15, .4), (.11, .35), (.07, .3)]
    zz = z
    for k, (r, h) in enumerate(tiers):
        for a in range(3):
            ang = a * 2 * math.pi / 3 + k * .2
            cyl(r * .55, h, math.cos(ang) * r * .5, math.sin(ang) * r * .5, zz, 'sky' if k % 2 else 'white', 8)
        cyl(r * .55, h + .04, z=zz, m='white', v=8); zz += h
    cyl(.025, .45, z=zz, m='white', v=6, r2=.004)

def anitkabir():
    z = plinth(1.05, top='green')
    box(1.4, .9, .12, z=z, m='stone'); z += .12
    box(1.0, .6, .36, z=z, m='cream')
    for i in range(10): cyl(.03, .34, -.45 + i * .1, -.31, z, 'white', 8)
    for sx in (-1, 1):
        for j in range(3): cyl(.03, .34, sx * .5, -.2 + j * .2, z, 'white', 8)
    box(1.06, .66, .07, z=z + .34, m='stone'); box(.98, .58, .05, z=z + .41, m='cream')
    for x in (-.5, .5): box(.04, .04, .1, x, -.6, z, 'gold')
    box(.18, .9, .02, 0, -.85, z - .12, 'stone')
    for x in (-.75, .75): tree(x, .35, z - .12, .9, 'green2')

def pisa():
    z = plinth(.85, top='green')
    grp = []
    for k in range(7):
        r, h = .2 if k < 6 else .15, .2 if k < 6 else .18
        grp.append(cyl(r, h, 0, 0, z + k * .2, 'white', 14))
        grp.append(ring(r + .03, r - .02, .025, 0, 0, z + k * .2 + h - .025, 'cream', 14))
        for i in range(10):
            a = 2 * math.pi * i / 10
            grp.append(cyl(.015, h - .04, math.cos(a) * (r + .015), math.sin(a) * (r + .015), z + k * .2 + .01, 'cream', 5))
    for o in grp:
        o.location = (Matrix.Rotation(.09, 4, 'Y') @ Vector(o.location - Vector((0, 0, z)))) + Vector((0, 0, z))
        o.rotation_euler = (0, .09, 0)
    box(.9, .4, .25, -.1, .55, z, 'white'); prism(.4, .9, .12, -.1, .55, z + .25, 'terra', rot=(0, 0, math.pi / 2))

def galata():
    z = plinth(.85, top='green')
    cyl(.26, 1.05, z=z, m='stone', v=16, r2=.24)
    for zz in (.35, .7): ring(.27, .2, .03, 0, 0, z + zz, 'sand2', 16)
    for k in range(8):
        a = 2 * math.pi * k / 8
        box(.04, .02, .14, math.cos(a) * .245, math.sin(a) * .245, z + .55, 'ink', rot=(0, 0, a + math.pi / 2))
    cyl(.28, .08, z=z + 1.05, m='cream', v=16)
    for k in range(12):
        a = 2 * math.pi * k / 12; box(.05, .02, .12, math.cos(a) * .25, math.sin(a) * .25, z + 1.13, 'sky', rot=(0, 0, a + math.pi / 2))
    cyl(.25, .12, z=z + 1.13, m='cream', v=16)
    cone(.3, .5, z=z + 1.25, m='dome', v=16); cone(.015, .1, z=z + 1.75, m='gold', v=6)
    for x, y in ((-.6, .2), (.6, -.25)): tree(x, y, z, .85)

MODELS = dict(ayasofya=ayasofya, galata=galata, peribacasi=peribacasi, kolezyum=kolezyum, eyfel=eyfel, sagrada=sagrada, partenon=partenon,
              piramit=piramit, kutubiye=kutubiye, pagoda=pagoda, watarun=watarun, ozgurluk=ozgurluk, gunes=gunes, machupicchu=machupicchu,
              safranbolu=safranbolu, bigben=bigben, tacmahal=tacmahal, isa=isa, opera=opera, basil=basil, burj=burj, anitkabir=anitkabir, pisa=pisa)

only = sys.argv[2:] or list(MODELS)
for name in only:
    reset(); MODELS[name](); export(name)
