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

def get_object_from_file(context,drop_filepath):
    link = False if context.scene.objectlib.link_or_append == 'APPEND' else True
    path, image_file = os.path.split(drop_filepath)
    path2, category_name = os.path.split(path)
    path3, library_name = os.path.split(path2)
    img_file_name, img_ext = os.path.splitext(image_file)
    files = os.listdir(path)

    for file in files:
        blendname, ext = os.path.splitext(file)
        if ext == ".blend":
            blendfile_path = os.path.join(path,file)
            with bpy.data.libraries.load(blendfile_path, link, False) as (data_from, data_to):
                for object in data_from.objects:   
                    if object == img_file_name:         
                        data_to.objects = [object]              
                        break
                        
            for obj in data_to.objects:
                obj.objectlib.library_name = library_name
                obj.objectlib.category_name = category_name
                obj.objectlib.object_name = img_file_name
                return obj
    
def get_thumbnail_path():
    path = get_object_library_path()
    return os.path.join(path,'thumbnail.blend')
    
def get_addon_path():
    path, filename = os.path.split(os.path.normpath(__file__))
    return path
    
def get_object_library_path():
    addon = bpy.context.user_preferences.addons['objectlib'].preferences
    if addon.path == "" or not os.path.isdir(addon.path):
        path, exe = os.path.split(bpy.app.binary_path)
        return os.path.join(get_addon_path(),"Objects")
    else:
        return addon.path

def get_z_rotation(obj,z_rotation):
    if obj:
        z_rotation += obj.rotation_euler.z
        if obj.parent:
            z_rotation += get_z_rotation(obj.parent,z_rotation)
    return z_rotation

def save_object_script(source_file,object_name,target_file):
    path = get_addon_path()
    file = open(os.path.join(path,"temp.py"),'w')
    file.write("import bpy\n")
    file.write("with bpy.data.libraries.load(r'" + source_file + "', False, True) as (data_from, data_to):\n")
    file.write("    for obj in data_from.objects:\n")
    file.write("        if obj == '" + object_name + "':\n")
    file.write("            data_to.objects = [obj]\n")
    file.write("            break\n")
    file.write("for obj in data_to.objects:\n")
    file.write("    bpy.context.scene.objects.link(obj)\n")
    file.write("    bpy.ops.wm.save_as_mainfile(filepath=r'" + target_file + "')\n")
    file.close()
    return os.path.join(path,'temp.py')

def create_thumbnail_script(source_file,object_name,thumbnail_path):
    path = get_addon_path()
    file = open(os.path.join(path,"temp.py"),'w')
    file.write("import bpy\n")
    file.write("with bpy.data.libraries.load(r'" + source_file + "', False, True) as (data_from, data_to):\n")
    file.write("    for obj in data_from.objects:\n")
    file.write("        if obj == '" + object_name + "':\n")
    file.write("            data_to.objects = [obj]\n")
    file.write("            break\n")
    file.write("for obj in data_to.objects:\n")
    file.write("    bpy.context.scene.objects.link(obj)\n")
    file.write("    obj.select = True\n")
    file.write("    bpy.context.scene.objects.active = obj\n")
    file.write("    bpy.ops.view3d.camera_to_view_selected()\n")
    file.write("    render = bpy.context.scene.render\n")
    file.write("    render.use_file_extension = True\n")
    file.write("    render.filepath = r'" + thumbnail_path + "'\n")
    file.write("    bpy.ops.render.render(write_still=True)\n")
    file.close()
    return os.path.join(path,'temp.py')
