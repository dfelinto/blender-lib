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
import inspect

def get_addon_path():
    path, filename = os.path.split(os.path.normpath(__file__))
    return path

def get_group_from_file(context,drop_filepath):
    link = False if context.scene.grouplib.link_or_append == 'APPEND' else True
    path, image_file = os.path.split(drop_filepath)
    path2, category_name = os.path.split(path)
    img_file_name, img_ext = os.path.splitext(image_file)
    files = os.listdir(path)
    for file in files:
        blendname, ext = os.path.splitext(file)
        if ext == ".blend":
            blendfile_path = os.path.join(path,file)
            with bpy.data.libraries.load(blendfile_path, link, False) as (data_from, data_to):
                for group in data_from.groups:
                    if group == img_file_name:
                        data_to.groups = [group]
                        break

            for grp in data_to.groups:
                grp.grouplib.category_name = category_name
                return grp

def get_group_library_path():
    addon = bpy.context.user_preferences.addons['grouplib'].preferences
    if addon.path == "" or not os.path.isdir(addon.path):
        return os.path.join(get_addon_path(),"Groups")
    else:
        return addon.path

def get_thumbnail_path():
    filepath = os.path.join(get_group_library_path(),'thumbnail.blend')
    if os.path.isfile(filepath):
        return filepath
    
def save_group_script(source_file,group_name,target_file):
    path = get_addon_path()
    file = open(os.path.join(path,"temp.py"),'w')
    file.write("import bpy\n")
    file.write("with bpy.data.libraries.load(r'" + source_file + "', False, True) as (data_from, data_to):\n")
    file.write("    for grp in data_from.groups:\n")
    file.write("        if grp == '" + group_name + "':\n")
    file.write("            data_to.groups = [grp]\n")
    file.write("            break\n")
    file.write("for grp in data_to.groups:\n")
    file.write("    for obj in grp.objects:\n")
    file.write("        bpy.context.scene.objects.link(obj)\n")
    file.write("bpy.ops.wm.save_as_mainfile(filepath=r'" + target_file + "')\n")
    file.close()
    return os.path.join(path,'temp.py')

def create_thumbnail_script(source_file,group_name,thumbnail_path):
    path = get_addon_path()
    file = open(os.path.join(path,"temp.py"),'w')
    file.write("import bpy\n")
    file.write("with bpy.data.libraries.load(r'" + source_file + "', False, True) as (data_from, data_to):\n")
    file.write("    for grp in data_from.groups:\n")
    file.write("        if grp == '" + group_name + "':\n")
    file.write("            data_to.groups = [grp]\n")
    file.write("            break\n")
    file.write("for grp in data_to.groups:\n")
    file.write("    for obj in grp.objects:\n")
    file.write("        bpy.context.scene.objects.link(obj)\n")
    file.write("        obj.select = True\n")
    file.write("    bpy.ops.view3d.camera_to_view_selected()\n")
    file.write("    render = bpy.context.scene.render\n")
    file.write("    render.use_file_extension = True\n")
    file.write("    render.filepath = r'" + thumbnail_path + "'\n")
    file.write("    bpy.ops.render.render(write_still=True)\n")
    file.close()
    return os.path.join(path,'temp.py')
