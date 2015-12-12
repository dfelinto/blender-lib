import bpy
with bpy.data.libraries.load(r'/Users/dfelinto/Documents/Projects/2015/einteriores/testes/torus.blend', False, True) as (data_from, data_to):
    for obj in data_from.objects:
        if obj == 'Torus':
            data_to.objects = [obj]
            break
for obj in data_to.objects:
    bpy.context.scene.objects.link(obj)
    bpy.ops.wm.save_as_mainfile(filepath=r'/Users/dfelinto/Documents/Projects/2015/einteriores/Fluid_Designer_2015_R3_OSX/blender.app/Contents/Resources/2.74/scripts/addons/objectlib/Objects/Books/Torus.blend')
