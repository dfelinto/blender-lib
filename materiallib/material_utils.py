# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
import os
import fd

def get_material_from_file(context,drop_filepath):
    link = False
    if context.scene.materiallib.link_or_append == 'LINK':
        link = True
    path, image_file = os.path.split(drop_filepath)
    category_name = os.path.basename(path)
    img_file_name, img_ext = os.path.splitext(image_file) 
    files = os.listdir(path)
    
    if img_file_name in bpy.data.materials:
        return bpy.data.materials[img_file_name]
    
    possible_files = []
    # Add the blend file with the same name to the list first so it
    # is searched first just in case there are duplicate materials.
    if img_file_name + ".blend" in files:
        possible_files.append(os.path.join(path,img_file_name + ".blend"))
    
    for file in files:
        blendname, ext = os.path.splitext(file)
        if ext == ".blend":
            possible_files.append(os.path.join(path,file))
            
    for file in possible_files:
        with bpy.data.libraries.load(file, link, False) as (data_from, data_to):
            for material in data_from.materials:
                if material == img_file_name:
                    data_to.materials = [material]
                    break
                    
        for mat in data_to.materials:
            mat.materiallib.category_name = category_name
            mat.materiallib.material_name = img_file_name
            return mat

def get_addon_path():
    path, filename = os.path.split(os.path.normpath(__file__))
    return path

def get_material_library_path():
    addon = bpy.context.user_preferences.addons['materiallib'].preferences
    if addon.path == "" or not os.path.isdir(addon.path):
        return os.path.join(get_addon_path(),"Materials")
    else:
        return addon.path
    
def get_images_from_material(mat):
    images = []
    for node in mat.node_tree.nodes:
        if node.type == 'TEX_IMAGE':
            images.append(node.image)
    return images
    
def set_object_materials(obj):
    for slot in obj.materiallib.material_slots:
        print(slot)
    
def assign_material_to_object(obj,material,index_list=None):
    if material:
        if len(obj.material_slots) == 0:
            bpy.ops.fd_material.add_material_slot(object_name=obj.name)
        for index, slot in enumerate(obj.material_slots):
            if index_list:
                if index in index_list:
                    slot.material = material
                    obj.materiallib.material_slots[index].category_name = material.materiallib.category_name
                    obj.materiallib.material_slots[index].material_name = material.materiallib.material_name
            else:
                slot.material = material
                obj.materiallib.material_slots[index].category_name = material.materiallib.category_name
                obj.materiallib.material_slots[index].material_name = material.materiallib.material_name

def sync_material_slots(obj):
    for slot in obj.materiallib.material_slots:
        obj.materiallib.material_slots.remove(0)
    
    for mat_slot in obj.material_slots:
        slot = obj.materiallib.material_slots.add()
        
def get_thumbnail_path():
    filepath = os.path.join(get_material_library_path(),'thumbnail.blend')
    if os.path.isfile(filepath):
        return filepath
        
def save_material_script(source_file,material_name,target_file):
    path = get_addon_path()
    file = open(os.path.join(path,"temp.py"),'w')
    file.write("import bpy\n")
    file.write("with bpy.data.libraries.load(r'" + source_file + "', False, True) as (data_from, data_to):\n")
    file.write("    for mat in data_from.materials:\n")
    file.write("        if mat == '" + material_name + "':\n")
    file.write("            data_to.materials = [mat]\n")
    file.write("            break\n")
    file.write("for mat in data_to.materials:\n")
    file.write("    mat.use_fake_user = True\n")
    file.write("bpy.ops.wm.save_as_mainfile(filepath=r'" + target_file + "')\n")
    file.close()
    return os.path.join(path,'temp.py')

def create_thumbnail_script(source_file,material_name,thumbnail_path):
    path = get_addon_path()
    file = open(os.path.join(path,"temp.py"),'w')
    file.write("import bpy\n")
    file.write("import fd\n")
    file.write("with bpy.data.libraries.load(r'" + source_file + "', False, True) as (data_from, data_to):\n")
    file.write("    for mat in data_from.materials:\n")
    file.write("        if mat == '" + material_name + "':\n")
    file.write("            data_to.materials = [mat]\n")
    file.write("            break\n")
    file.write("for mat in data_to.materials:\n")
    file.write("    bpy.ops.mesh.primitive_cube_add()\n")
    file.write("    obj = bpy.context.scene.objects.active\n")
    file.write("    obj.dimensions = (fd.inches(24),fd.inches(24),fd.inches(24))\n")
    file.write("    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)\n")
    file.write("    mod = obj.modifiers.new('bevel','BEVEL')\n")
    file.write("    mod.segments = 5\n")
    file.write("    mod.width = .05\n")
    file.write("    bpy.ops.object.modifier_apply(modifier='bevel')\n")
    file.write("    bpy.ops.fd_object.unwrap_mesh(object_name=obj.name)\n")
    file.write("    bpy.ops.fd_object.add_material_slot(object_name=obj.name)\n")
    file.write("    for slot in obj.material_slots:\n")
    file.write("        slot.material = mat\n")
    file.write("    bpy.context.scene.objects.active = obj\n")
    file.write("    bpy.ops.view3d.camera_to_view_selected()\n")
    file.write("    render = bpy.context.scene.render\n")
    file.write("    render.use_file_extension = True\n")
    file.write("    render.filepath = r'" + thumbnail_path + "'\n")
    file.write("    bpy.ops.render.render(write_still=True)\n")
    file.close()
    return os.path.join(path,'temp.py')