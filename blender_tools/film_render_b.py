import bpy, os
BASE = os.path.join(os.path.expanduser("~"), "Downloads", "BalloonTest")
bpy.ops.wm.open_mainfile(filepath=os.path.join(BASE, "balloon_film.blend"))
sc = bpy.context.scene
out = os.path.join(BASE, "frames_film")
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, 50
try: sc.eevee.taa_render_samples = 12
except Exception: pass
sc.render.image_settings.media_type = 'IMAGE'; sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 92
sc.render.filepath = os.path.join(out, "f_####")
sc.render.use_overwrite = False; sc.render.use_placeholder = True
sc.frame_start = 1600   # start from the back half; placeholders stop double work
bpy.ops.render.render(animation=True)
sc.frame_start = 1
bpy.ops.render.render(animation=True)
open(os.path.join(BASE, "render_done_b.txt"), "w").write("done")
