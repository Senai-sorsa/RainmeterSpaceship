"""Offline Blender (Cycles) render of the cockpit shell, 2560x1600, orthographic so the layout cannot move.
Run: blender.exe -b --factory-startup -P tools/blender/cockpit_scene.py -- --layout tools/frame_src/layout_polys.json
       --curve tools/frame_src/curve.json --out Skins/Spaceship/@Resources/Images/Render --samples 256
Writes only PNGs into --out: hull, corners, light_screens, light_trim, light_orb, glass_reflect.
Each light pass is its own render (key lights off, one emitter group on, neutral hull) in grayscale."""
import argparse
import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector, geometry

ap = argparse.ArgumentParser()
ap.add_argument("--layout", required=True)
ap.add_argument("--curve", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--samples", type=int, default=256)
ap.add_argument("--percent", type=int, default=100)
ap.add_argument("--only", default="")
A = ap.parse_args(sys.argv[sys.argv.index("--") + 1:])
L = json.loads(Path(A.layout).read_text())
C = json.loads(Path(A.curve).read_text())
OUT = Path(A.out).resolve()
CW, CH = L["canvas"]["w"], L["canvas"]["h"]
RAD = C["radius"]
THICK, BEVEL = 40, 6

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene


def zc(x, r=RAD):
    return -((x - CW / 2) ** 2) / (2 * r)


SAG_T, SAG_B = C["edgeSag"]["top"], C["edgeSag"]["bottom"]


def bow(pts):
    """Barrel curve: every long, near-horizontal edge inside the canvas gets a parabolic bow, the top ones bulging up and
    the bottom ones down (the glass grows, the HUD stays in it). Endpoints stay, so shared edges stay shared."""
    out = []
    for i, a in enumerate(pts):
        b = pts[(i + 1) % len(pts)]
        out.append(tuple(a))
        dx, dy = b[0] - a[0], b[1] - a[1]
        sag = -SAG_T if a[1] < CH / 2 else SAG_B
        if sag and abs(dx) > 400 and abs(dy) < 0.25 * abs(dx) and 0 < a[1] < CH and 0 < b[1] < CH:
            n = int(abs(dx) // 60)
            for k in range(1, n):
                t = k / n
                out.append((a[0] + dx * t, a[1] + dy * t + sag * (1 - (2 * t - 1) ** 2)))
    return out


def V(p):
    return Vector((p[0], CH - p[1], 0))


def area(pts):
    return sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts))) / 2


def plate(name, outer, holes=(), thick=THICK, lift=0.0, res=140, r=RAD, bevel=BEVEL, mat=None):
    """Flat polygon (with holes) -> subdivided -> bent into a cylinder -> solidified -> bevelled."""
    outer = bow(outer) if len(outer) < 40 else outer
    holes = [bow(h) for h in holes]
    o = [V(p) for p in outer]
    if area([(v.x, v.y) for v in o]) < 0:
        o.reverse()
    polys = [o]
    for h in holes:
        hv = [V(p) for p in h]
        if area([(v.x, v.y) for v in hv]) > 0:
            hv.reverse()
        polys.append(hv)
    pts = [v for p in polys for v in p]
    tris = geometry.tessellate_polygon(polys)
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in pts], [], [tuple(t) for t in tris])
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    bm = bmesh.new()
    bm.from_mesh(me)
    for _ in range(7):
        long_e = [e for e in bm.edges if e.calc_length() > res]
        if not long_e:
            break
        bmesh.ops.subdivide_edges(bm, edges=long_e, cuts=1, use_grid_fill=True)
        bmesh.ops.triangulate(bm, faces=bm.faces[:])
    for v in bm.verts:
        v.co.z = zc(v.co.x, r) + lift
    ext = bmesh.ops.extrude_face_region(bm, geom=bm.faces[:])  # vertical walls: the silhouette stays exact
    bmesh.ops.translate(bm, verts=[g for g in ext["geom"] if isinstance(g, bmesh.types.BMVert)], vec=(0, 0, -thick))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(me)
    bm.free()
    if bevel:
        b = ob.modifiers.new("bevel", "BEVEL")
        b.width, b.segments, b.angle_limit = bevel, 3, math.radians(35)
    if mat:
        ob.data.materials.append(mat)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    try:
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35))
    except Exception:
        bpy.ops.object.shade_smooth()
    ob.select_set(False)
    return ob


def principled(name, base, metal, rough, noise=False, seams=False, ao=True):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    n = m.node_tree.nodes
    n.clear()
    out = n.new("ShaderNodeOutputMaterial")
    bsdf = n.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Metallic"].default_value = metal
    bsdf.inputs["Roughness"].default_value = rough
    col = n.new("ShaderNodeRGB")
    col.outputs[0].default_value = (*base, 1)
    last = col.outputs[0]

    def mul(a, b):
        mx = n.new("ShaderNodeMix")
        mx.data_type, mx.blend_type = "RGBA", "MULTIPLY"
        mx.inputs[0].default_value = 1.0
        m.node_tree.links.new(a, mx.inputs[6])
        m.node_tree.links.new(b, mx.inputs[7])
        return mx.outputs[2]
    if ao:
        ao_n = n.new("ShaderNodeAmbientOcclusion")
        ao_n.inputs["Distance"].default_value = 26
        last = mul(last, ao_n.outputs["Color"])
    if seams:  # panel seams: thin dark lines on a brick grid in canvas units
        br = n.new("ShaderNodeTexBrick")
        br.inputs["Scale"].default_value = 0.0016
        br.inputs["Mortar Size"].default_value = 0.012
        br.inputs["Brick Width"].default_value = 1.0
        br.inputs["Row Height"].default_value = 0.55
        br.inputs["Color1"].default_value = (1, 1, 1, 1)
        br.inputs["Color2"].default_value = (0.93, 0.93, 0.93, 1)
        br.inputs["Mortar"].default_value = (0.75, 0.75, 0.75, 1)
        tc = n.new("ShaderNodeTexCoord")
        m.node_tree.links.new(tc.outputs["Object"], br.inputs["Vector"])
        last = mul(last, br.outputs["Color"])
    if noise:
        nz = n.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = 0.012
        nz.inputs["Detail"].default_value = 6
        tc2 = n.new("ShaderNodeTexCoord")
        m.node_tree.links.new(tc2.outputs["Object"], nz.inputs["Vector"])
        mr = n.new("ShaderNodeMapRange")
        mr.inputs["To Min"].default_value, mr.inputs["To Max"].default_value = 0.30, 0.50
        m.node_tree.links.new(nz.outputs["Fac"], mr.inputs["Value"])
        m.node_tree.links.new(mr.outputs["Result"], bsdf.inputs["Roughness"])
    m.node_tree.links.new(last, bsdf.inputs["Base Color"])
    m.node_tree.links.new(bsdf.outputs[0], out.inputs[0])
    return m


def emission(name, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    n = m.node_tree.nodes
    n.clear()
    e = n.new("ShaderNodeEmission")
    e.inputs["Strength"].default_value = strength
    o = n.new("ShaderNodeOutputMaterial")
    m.node_tree.links.new(e.outputs[0], o.inputs[0])
    return m


# ---- geometry
metal = principled("gunmetal", (0.06, 0.065, 0.072), 1.0, 0.38, noise=True, seams=False)
corner_mat = principled("corner", (0.025, 0.03, 0.036), 0.9, 0.3)
neutral = principled("neutral", (0.8, 0.8, 0.8), 0.0, 0.6, ao=False)
hull = plate("hull", [(-300, -300), (CW + 300, -300), (CW + 300, CH + 300), (-300, CH + 300)], L["windows"], mat=metal)
struts = [plate("strut%d" % i, s, thick=14, lift=10, bevel=3, mat=metal) for i, s in enumerate(L["struts"])]
bez_hull = [plate("bz%d" % i, b, lift=-1, mat=metal) for i, b in enumerate(L["bezels"])]
bez_corner = [plate("bc%d" % i, b, thick=30, lift=30, mat=corner_mat) for i, b in enumerate(L["bezels"])]
glass = [plate("gl%d" % i, w, thick=1, lift=80, r=2600, bevel=0,
               mat=principled("glass", (0, 0, 0), 0.0, 0.07, ao=False)) for i, w in enumerate(L["windows"])]
for g in glass:  # pure mirror
    g.data.materials[0].node_tree.nodes["Principled BSDF"].inputs["Specular IOR Level"].default_value = 1.0

# ---- emitters (invisible to the camera, they only light the hull)
E_SCREENS, E_TRIM, E_ORB, E_GHOST = [], [], [], []


def emitter_plane(name, x, y, w, h, z, strength, bucket):
    bpy.ops.mesh.primitive_plane_add(size=1, location=(x + w / 2, CH - (y + h / 2), z))
    ob = bpy.context.object
    ob.name = name
    ob.scale = (w, h, 1)
    ob.rotation_euler.x = math.pi
    ob.data.materials.append(emission(name, strength))
    ob.visible_camera = False
    bucket.append(ob)
    return ob


K_SCREEN = 0.12
for zid, pct in L["spill"].items():
    if zid not in L["zones"] or zid == "C_sphere":
        continue
    x, y, w, h = L["zones"][zid]
    emitter_plane("sc_" + zid, x, y, w, h, zc(x + w / 2) + 90, pct * K_SCREEN, E_SCREENS)
    emitter_plane("gh_" + zid, x, y, w, h, 700, pct * 0.4, E_GHOST)
for i, path in enumerate(L["trim"]):  # thin strips along each Decor path
    for a, b in zip(path, path[1:]):
        ln = math.hypot(b[0] - a[0], b[1] - a[1])
        if ln < 1:
            continue
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        bpy.ops.mesh.primitive_plane_add(size=1, location=(mx, CH - my, zc(mx) + 14))
        ob = bpy.context.object
        ob.scale = (ln, 8, 1)
        ob.rotation_euler = (math.pi, 0, -math.atan2(-(b[1] - a[1]), b[0] - a[0]))
        ob.data.materials.append(emission("trim", 10))
        ob.visible_camera = False
        E_TRIM.append(ob)
ox, oy, ow, oh = L["zones"]["C_sphere"]
bpy.ops.mesh.primitive_circle_add(radius=70, fill_type="NGON", location=(ox + ow / 2, CH - (oy + oh / 2), zc(ox + ow / 2) + 140))
orb = bpy.context.object
orb.rotation_euler.x = math.pi
orb.data.materials.append(emission("orb", 28))
orb.visible_camera = False
E_ORB.append(orb)

# ---- keys, camera, world
sun_key = bpy.data.objects.new("key", bpy.data.lights.new("key", "SUN"))
sun_rim = bpy.data.objects.new("rim", bpy.data.lights.new("rim", "SUN"))
for s, rot, col, e in ((sun_key, (math.radians(38), 0, math.radians(-35)), (0.85, 0.93, 1.0), 2.4),
                       (sun_rim, (math.radians(62), 0, math.radians(140)), (1.0, 0.72, 0.5), 0.6)):
    bpy.context.collection.objects.link(s)
    s.rotation_euler = rot
    s.data.color, s.data.energy, s.data.angle = col, e, math.radians(2.5)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
bpy.context.collection.objects.link(cam)
cam.location = (CW / 2, CH / 2, 2500)
cam.data.type, cam.data.ortho_scale, cam.data.clip_end = "ORTHO", CW, 6000
scene.camera = cam
world = bpy.data.worlds.new("w")
world.use_nodes = True
scene.world = world

r = scene.render
r.engine = "CYCLES"
r.resolution_x, r.resolution_y, r.resolution_percentage = CW, CH, A.percent
r.image_settings.file_format, r.image_settings.color_depth = "PNG", "8"
r.dither_intensity = 1.0
scene.view_settings.view_transform, scene.view_settings.look = "Standard", "None"
scene.cycles.samples, scene.cycles.seed, scene.cycles.use_denoising = A.samples, 7, True
scene.cycles.device = "CPU"
try:
    pref = bpy.context.preferences.addons["cycles"].preferences
    for t in ("OPTIX", "CUDA", "HIP"):
        try:
            pref.compute_device_type = t
            pref.get_devices()
            if any(d.type == t for d in pref.devices):
                for d in pref.devices:
                    d.use = d.type == t
                scene.cycles.device = "GPU"
                break
        except Exception:
            continue
except Exception:
    pass
print("RENDER DEVICE", scene.cycles.device)


def world_strength(v):
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Strength"].default_value = v
    bg.inputs["Color"].default_value = (0.35, 0.42, 0.5, 1) if v else (0, 0, 0, 1)


def show(objs_on):
    for o in [hull, *struts, *bez_hull, *bez_corner, *glass, sun_key, sun_rim, *E_SCREENS, *E_TRIM, *E_ORB, *E_GHOST]:
        o.hide_render = o not in objs_on


def render(name, objs, color_mode, transparent, world_v, exposure=0.0, neutral_hull=False):
    show(objs)
    for o in (hull, *struts, *bez_hull):
        o.data.materials[0] = neutral if neutral_hull else metal
    scene.render.film_transparent = transparent
    scene.render.image_settings.color_mode = color_mode
    scene.view_settings.exposure = exposure
    world_strength(world_v)
    scene.render.filepath = str(OUT / (name + ".png"))
    bpy.ops.render.render(write_still=True)
    print("WROTE", scene.render.filepath)


base = [hull, *struts, *bez_hull]
passes = {
    "hull": lambda: render("hull", base + [sun_key, sun_rim], "RGBA", True, 0.22),
    "corners": lambda: render("corners", [*bez_corner, sun_key, sun_rim], "RGBA", True, 0.22),
    "light_screens": lambda: render("light_screens", base + E_SCREENS, "BW", False, 0, neutral_hull=True),
    "light_trim": lambda: render("light_trim", base + E_TRIM, "BW", False, 0, neutral_hull=True),
    "light_orb": lambda: render("light_orb", base + E_ORB, "BW", False, 0, neutral_hull=True),
    "glass_reflect": lambda: render("glass_reflect", glass + E_GHOST, "BW", False, 0),
}
OUT.mkdir(parents=True, exist_ok=True)
for k, fn in passes.items():
    if not A.only or k in A.only.split(","):
        fn()
