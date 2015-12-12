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

def get_world_from_file(context,drop_filepath):
    link = True if context.scene.worldlib.link_or_append == 'LINK' else False
    path, image_file = os.path.split(drop_filepath)
    category_name = os.path.basename(path)
    img_file_name, img_ext = os.path.splitext(image_file) 
    files = os.listdir(path)
    
    for file in files:
        blendname, ext = os.path.splitext(file)
        if ext == ".blend":
            blendfile_path = os.path.join(path,file)
            with bpy.data.libraries.load(blendfile_path, link, False) as (data_from, data_to):
                for world in data_from.worlds:
                    if world == img_file_name:
                        if world not in bpy.data.worlds:
                            data_to.worlds = [world]
                            break
                    
            for world in data_to.worlds:
                world.worldlib.category_name = category_name
                world.worldlib.material_name = img_file_name
                return world

def get_world_library_path():
    addon = bpy.context.user_preferences.addons['worldlib'].preferences
    if addon.path == "" or not os.path.isdir(addon.path):
        path, exe = os.path.split(bpy.app.binary_path)
        return os.path.join(get_addon_path(),"Worlds")
    else:
        return addon.path

def get_addon_path():
    path, filename = os.path.split(os.path.normpath(__file__))
    return path

def get_template_world():
    path = get_world_library_path()
    return os.path.join(path,"template.blend")

def get_thumbnail_path():
    path = get_world_library_path()
    return os.path.join(path,'thumbnail.blend')

def append_template_world():
    with bpy.data.libraries.load(get_template_world(), False, False) as (data_from, data_to):
        for world in data_from.worlds:
            data_to.worlds = [world]
            break
    for world in data_to.worlds:
        return world
    
def save_world_script(source_file,world_name,target_file):
    """ source_file: file that contains the world you want to save
        world_name: name of the world that you want to render
        target_file: the path to save blend file
    """
    path = get_addon_path()
    file = open(os.path.join(path,"temp.py"),'w')
    file.write("import bpy\n")
    file.write("with bpy.data.libraries.load(r'" + source_file + "', False, True) as (data_from, data_to):\n")
    file.write("    for world in data_from.worlds:\n")
    file.write("        if world == '" + world_name + "':\n")
    file.write("            data_to.worlds = [world]\n")
    file.write("            break\n")
    file.write("for world in data_to.worlds:\n")
    file.write("    bpy.context.scene.world = world\n")
    file.write("    bpy.ops.wm.save_as_mainfile(filepath=r'" + target_file + "')\n")
    file.close()
    return os.path.join(path,'temp.py')
    
def create_thumbnail_script(source_file,world_name,thumbnail_path):
    """ source_file: file that contains the world you want to create the thumbnail for
        world_name: name of the world that you want to render
        thumbnail_path: the path to save the rendered thumbnail
    """
    path = get_addon_path()
    file = open(os.path.join(path,"temp.py"),'w')
    file.write("import bpy\n")
    file.write("with bpy.data.libraries.load(r'" + source_file + "', False, True) as (data_from, data_to):\n")
    file.write("    for world in data_from.worlds:\n")
    file.write("        if world == '" + world_name + "':\n")
    file.write("            data_to.worlds = [world]\n")
    file.write("            break\n")
    file.write("for world in data_to.worlds:\n")
    file.write("    bpy.context.scene.world = world\n")
    file.write("    render = bpy.context.scene.render\n")
    file.write("    render.use_file_extension = True\n")
    file.write("    render.filepath = r'" + thumbnail_path + "'\n")
    file.write("    bpy.ops.render.render(write_still=True)\n")
    file.close()
    return os.path.join(path,'temp.py')
