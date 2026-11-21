"""Render a quick preview PNG for each .glb (Cycles CPU) and paste them into one contact sheet."""
import bpy, sys, os, math, glob
from mathutils import Vector
SRC, OUT = sys.argv[1], sys.argv[2]
names = sys.argv[3:] or sorted(os.path.splitext(os.path.basename(p))[0] for p in glob.glob(SRC + '/*.glb'))
os.makedirs(OUT, exist_ok=True)
for n in names:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=f'{SRC}/{n}.glb')
    objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))); mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    ctr = (mn + mx) / 2; size = max(mx - mn)
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); bpy.context.collection.objects.link(cam)
    d = size * 2.1; cam.location = ctr + Vector((d * .62, -d * .78, d * .45))
    cam.rotation_euler = (ctr - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.lens = 50
    bpy.context.scene.camera = cam
    sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); bpy.context.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(35)); sun.data.energy = 3.2
    w = bpy.data.worlds.new('w'); bpy.context.scene.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs[0].default_value = (.92, .9, .98, 1); w.node_tree.nodes['Background'].inputs[1].default_value = .9
    sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = 24; sc.cycles.device = 'CPU'
    sc.render.resolution_x = sc.render.resolution_y = 360; sc.render.filepath = f'{OUT}/{n}.png'
    sc.view_settings.view_transform = 'Standard'
    bpy.ops.render.render(write_still=True)
from PIL import Image, ImageDraw
ims = [(n, Image.open(f'{OUT}/{n}.png')) for n in names]
cols = 6; rows = math.ceil(len(ims) / cols)
sheet = Image.new('RGB', (cols * 360, rows * 380), (240, 238, 248)); dr = ImageDraw.Draw(sheet)
for i, (n, im) in enumerate(ims):
    x, y = (i % cols) * 360, (i // cols) * 380; sheet.paste(im, (x, y)); dr.text((x + 8, y + 362), n, fill=(60, 60, 90))
sheet.save(f'{OUT}/_sheet.png'); print('sheet', len(ims))
