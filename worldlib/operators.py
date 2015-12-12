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

from bpy.types import Operator
from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       BoolVectorProperty,
                       PointerProperty,
                       CollectionProperty,
                       EnumProperty)

from . import world_utils

class OPS_change_directory(Operator):
    bl_idname = "worldlib.change_directory"
    bl_label = "Change Directory"
    bl_options = {'UNDO'}
    
    path = StringProperty(name="Path")
    
    def execute(self, context):
        scene = context.scene
        directory, category = os.path.split(self.path)
        scene.worldlib.active_category_name = category
        fd.update_file_browser_space(context,self.path)
        return {'FINISHED'}
    
class OPS_open(Operator):
    bl_idname = "worldlib.open"
    bl_label = "Open Worlds"
    bl_description = "This will open the world library"
    bl_options = {'UNDO'}
  
    def execute(self, context):
        scene = context.scene
        
        path = world_utils.get_world_library_path()
        
        for category in scene.worldlib.categories:
            scene.worldlib.categories.remove(0)
        
        dirs = os.listdir(path)

        for directory in dirs:
            catpath = os.path.join(path,directory)
            if os.path.isdir(catpath):
                cat = scene.worldlib.categories.add()
                cat.name = directory
                cat.path = catpath
        
        if len(scene.worldlib.categories) > 0:
            category = scene.worldlib.categories[0]
            if context.screen.show_fullscreen:
                fd.update_file_browser_space(context,world_utils.get_world_library_path())
            else:
                bpy.ops.worldlib.change_directory(path=category.path)

        scene.mv.active_addon_name = "World Library"
        return {'FINISHED'}

class OPS_drop(Operator):
    bl_idname = "worldlib.drop"
    bl_label = "Drop World"
    bl_options = {'UNDO'}
  
    #READONLY
    filepath = StringProperty(name="Filepath")
    objectname = StringProperty(name="Object Name")
    
    def invoke(self, context, event):
        path, ext = os.path.splitext(self.filepath)
        if ext == '.blend':
            bpy.ops.fd_general.open_blend_file('INVOKE_DEFAULT',filepath=self.filepath)
            return {'FINISHED'}
        world = world_utils.get_world_from_file(context,self.filepath)
        context.scene.world = world
        return {'FINISHED'}

class OPS_create_new_world_from_image(Operator):
    bl_idname = "worldlib.create_new_world_from_image"
    bl_label = "Create New World From Image"
    bl_description = 'Create a new world from the image path. (You must have the "Path to World Image" set)'
    bl_options = {'UNDO'}
  
    @classmethod
    def poll(cls, context):
        wm = context.window_manager.worldlib
        if os.path.exists(wm.path_to_world_image):
            return True
        else:
            return False
  
    def invoke(self, context, event):
        wm = context.window_manager.worldlib
        path = wm.path_to_world_image
        if os.path.exists(path):
            new_world = world_utils.append_template_world()
            context.scene.world = new_world
            for node in new_world.node_tree.nodes:
                if node.type == 'TEX_ENVIRONMENT':
                    image = bpy.data.images.load(path)
                    node.image = image
        return {'FINISHED'}

class OPS_save_active_world_to_active_category(Operator):
    bl_idname = "worldlib.save_active_world_to_active_category"
    bl_label = "Save Active World To Active Category"
    bl_description = "Save this world to the active category. (The file must be saved)"
    bl_options = {'UNDO'}
  
    @classmethod
    def poll(cls, context):
        if bpy.data.filepath != "" and context.scene.world:
            return True
        else:
            return False
  
    def invoke(self, context, event):
        world = context.scene.world
        import subprocess
        path = fd.get_file_browser_path(context)
        blend_path = os.path.join(path,world.name + ".blend")
        thumbnail_path = os.path.join(path,world.name + ".png")
        
        script = world_utils.save_world_script(bpy.data.filepath, world.name, blend_path)
        subprocess.call([bpy.app.binary_path, '-b', '--python', script])
        
        script = world_utils.create_thumbnail_script(blend_path, world.name, thumbnail_path)
        subprocess.call([bpy.app.binary_path, world_utils.get_thumbnail_path(), '-b', '--python', script])

        return {'FINISHED'}

class OPS_Create_Thumbnails(Operator):
    bl_idname = "worldlib.create_thumbnails"
    bl_label = "Create Thumbnails"
    bl_description = "This will render thumbnails of all of the items in the world list."
    
    @classmethod
    def poll(cls, context):
        if fd.get_file_browser_path(context):
            wm = context.window_manager.worldlib
            for wld in wm.worlds_in_category:
                if wld.selected:
                    return True
        else:
            return False
        return False
    
    def execute(self,context):
        import subprocess
        wm = context.window_manager.worldlib
        category_path = fd.get_file_browser_path(context)
        for wld in wm.worlds_in_category:
            if wld.selected:
                script = world_utils.create_thumbnail_script(wld.filepath, wld.name, os.path.join(category_path,wld.name))
                subprocess.call([bpy.app.binary_path, world_utils.get_thumbnail_path(), '-b', '--python', script])
        return{'FINISHED'}

class OPS_Select_All_Worlds_In_List(Operator):   
    bl_idname = "worldlib.select_all_worlds_in_list"
    bl_label = "Select All Worlds In List"
    bl_description = "This will select all of the items in the world list"
    
    select_all = BoolProperty(name="Select All",default=True)
    
    @classmethod
    def poll(cls, context):
        wm = context.window_manager.worldlib
        if len(wm.worlds_in_category) > 0:
            return True
        else:
            return False

    def execute(self,context):
        wm = context.window_manager.worldlib
        for world in wm.worlds_in_category:
            world.selected = self.select_all
        return{'FINISHED'}

class OPS_Load_Worlds_From_Category(Operator):   
    bl_idname = "worldlib.load_worlds_from_category"
    bl_label = "Load Worlds From Category"
    bl_description = "This will load all of the worlds in the active category into a list"
    
    @classmethod
    def poll(cls, context):
        if fd.get_file_browser_path(context):
            return True
        else:
            return False
    
    def found_thumbnail(self,files,filename):
        if filename + ".png" in files:
            return True
        if filename + ".jpg" in files:
            return True
        if filename + ".PNG" in files:
            return True
        if filename + ".JPG" in files:
            return True
        return False
    
    def execute(self,context):
        wm = context.window_manager.worldlib
        path = fd.get_file_browser_path(context)
        files = os.listdir(path)
        for obj in wm.worlds_in_category:
            wm.worlds_in_category.remove(0)
            
        for file in files:
            filename, ext = os.path.splitext(file)
            if ext == '.blend':
                filepath = os.path.join(path,file)
                if os.path.isfile(filepath):
                    with bpy.data.libraries.load(filepath, False, False) as (data_from, data_to):
                        
                        for index, world in enumerate(data_from.worlds):
                            wld = wm.worlds_in_category.add()
                            wld.name = world
                            wld.filename = filename
                            wld.filepath = filepath
                            wld.has_thumbnail = self.found_thumbnail(files, wld.name)

        return{'FINISHED'}

class OPS_Append_Worlds_From_Category(Operator):   
    bl_idname = "worldlib.append_worlds_from_category"
    bl_label = "Append Worlds From Category"
    bl_options = {'UNDO'}
    bl_description = "This will append all of the selected worlds in the object list into the scene"
    
    @classmethod
    def poll(cls, context):
        wm = context.window_manager.worldlib
        if len(wm.worlds_in_category) > 0:
            return True
        else:
            return False

    def execute(self,context):
        wm = context.window_manager.worldlib
        
        for wld in wm.worlds_in_category:
            if wld.selected:
                with bpy.data.libraries.load(wld.filepath, False, False) as (data_from, data_to):
                    data_to.materials = [wld.name]

        return{'FINISHED'}

#------REGISTER
classes = [
           OPS_change_directory,
           OPS_open,
           OPS_drop,
           OPS_create_new_world_from_image,
           OPS_save_active_world_to_active_category,
           OPS_Create_Thumbnails,
           OPS_Select_All_Worlds_In_List,
           OPS_Load_Worlds_From_Category,
           OPS_Append_Worlds_From_Category
           ]

def register():
    for c in classes:
        bpy.utils.register_class(c)

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)

if __name__ == "__main__":
    register()
