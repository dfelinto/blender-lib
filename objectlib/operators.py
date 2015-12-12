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
import re

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

from . import object_utils
from . import properties

class OPS_Open(Operator):
    bl_idname = "objectlib.open"
    bl_label = "Objects Library"
    bl_description = "This will open the object library"
    bl_options = {'UNDO'}

    def execute(self, context):
        scene = context.scene
        path = object_utils.get_object_library_path()
        
        for library in scene.objectlib.libraries:
            scene.objectlib.libraries.remove(0)
        
        dirs = os.listdir(path)

        for directory in dirs:
            libpath = os.path.join(path,directory)
            if os.path.isdir(libpath):
                lib = scene.objectlib.libraries.add()
                lib.name = directory
                lib.path = libpath

        if len(scene.objectlib.libraries) > 0:
            library = scene.objectlib.libraries[0]
            path, lib_name = os.path.split(os.path.normpath(library.path))
            if context.screen.show_fullscreen:
                fd.update_file_browser_space(context,object_utils.get_object_library_path())
            else:
                bpy.ops.objectlib.change_library(library_name=lib_name)

        scene.mv.active_addon_name = "Object Library"
        return {'FINISHED'}

class OPS_Drop(Operator):
    bl_idname = "objectlib.drop"
    bl_label = "Drop Object"
    bl_options = {'UNDO'}
    
    #READONLY
    filepath = StringProperty(name="Filepath",
                              subtype='FILE_PATH')
    
    objectname = StringProperty(name="Object Name")
    
    obj = None
    
    def get_object(self,context):
        self.obj = object_utils.get_object_from_file(context,self.filepath)
        self.obj.draw_type = 'WIRE'
        context.scene.objects.link(self.obj)
        bpy.ops.object.select_all(action='DESELECT')
        context.scene.update() # THE SCENE MUST BE UPDATED FOR RAY CAST TO WORK
    
    def set_up_opengl(self,context):
        if context.area.type == 'VIEW_3D':
            args = (self, context)
            self._handle = bpy.types.SpaceView3D.draw_handler_add(fd.draw_callback_px, args, 'WINDOW', 'POST_PIXEL')
            self.mouse_loc = []
            self.mouse_text = ""
            self.header_text = ""
    
    def execute(self, context):
        path, ext = os.path.splitext(self.filepath)
        if ext == '.blend':
            bpy.ops.fd_general.open_blend_file('INVOKE_DEFAULT',filepath=self.filepath)
            return {'FINISHED'}
        self.get_object(context)
        self.set_up_opengl(context)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
        
    def cancel_drop(self,context,event):
        bpy.context.window.cursor_set('DEFAULT')
        self.obj.select = True
        context.scene.objects.active = self.obj
        bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
        return {'FINISHED'}

    def modal(self, context, event):
        self.header_text = "Place Object: (Left Click = Place Object) (Hold Shift = Place Multiple) (Esc = Cancel)"
        context.area.tag_redraw()
        selected_point, selected_obj = fd.get_selection_point(context,event)
        self.obj.location = selected_point
        rotation = object_utils.get_z_rotation(selected_obj, 0)
        self.obj.rotation_euler.z = rotation
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            self.obj.draw_type = 'TEXTURED'
            item = context.scene.objectlib.scene_objects.add()
            item.name = self.obj.name
            if event.shift:
                self.get_object(context)
            else:
                return self.cancel_drop(context,event)
        
        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            return {'PASS_THROUGH'}
        
        if event.type == 'ESC':
            obj_list = []
            obj_list.append(self.obj)
            fd.delete_obj_list(obj_list)
            return self.cancel_drop(context,event)
        
        return {'RUNNING_MODAL'}

class OPS_Delete(Operator):
    bl_idname = "objectlib.delete"
    bl_label = "Delete Object"
    bl_description = "This will delete the object"

    object_name = StringProperty(name="Object Name")

    def execute(self, context):
        ob = context.scene.objectlib.scene_objects[self.object_name]
        if ob:
            obj = bpy.data.objects[ob.name]
            objects = []
            objects.append(obj)
            fd.delete_obj_list(objects)          
            for index, obj2 in enumerate(context.scene.objectlib.scene_objects):
                if obj2.name == ob.name:
                    context.scene.objectlib.scene_objects.remove(index)
                    break
            
        return {'FINISHED'}
    
    def invoke(self,context,event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=500)

    def draw(self, context):
        layout = self.layout
        obj = context.scene.objectlib.scene_objects[self.object_name]
        if obj:
            layout.label("Are you sure you want to delete " + obj.name)

class OPS_View_Selected(Operator):
    bl_idname = "objectlib.view_selected"
    bl_label = "View Selected"
    bl_description = "This will focus the viewport on the object"

    object_name = StringProperty(name="Object Name")

    def execute(self, context):
        ob = context.scene.objectlib.scene_objects[self.object_name]
        if ob:
            obj = bpy.data.objects[ob.name]
            bpy.ops.object.select_all(action='DESELECT')
            obj.select = True
            context.scene.objects.active = obj
            bpy.ops.view3d.view_selected()
        return {'FINISHED'}

class OPS_Add_Object_To_List(Operator):
    bl_idname = "objectlib.add_object_to_list"
    bl_label = "Add Object To List"
    bl_description = "This will add the selected object to the object list"

    @classmethod
    def poll(cls, context):
        if context.object:
            return True
        else:
            return False

    def execute(self, context):
        objs = context.scene.objectlib.scene_objects
        if context.object:
            if context.object.name not in objs:
                object = objs.add()
                object.name = context.object.name
        return {'FINISHED'}

class OPS_Change_Library(Operator):
    bl_idname = "objectlib.change_library"
    bl_label = "Change Library"
    bl_description = "This will change the active object library"
    
    library_name = StringProperty(name="Path")
    
    def execute(self, context):
        scene = context.scene
        addon_path = os.path.dirname(__file__)
        library_path = os.path.join(addon_path,'Objects')
        path = os.path.join(library_path,self.library_name)
        scene.objectlib.active_library_name = self.library_name
        library = scene.objectlib.libraries[scene.objectlib.active_library_name]
        library.path = path
        library.get_categories()
        fd.update_file_browser_space(context,path)
        if len(library.categories) > 0:
            bpy.ops.objectlib.change_category(category_name = library.categories[0].name)
        context.scene.update()
        return {'FINISHED'}

class OPS_Change_Category(Operator):
    bl_idname = "objectlib.change_category"
    bl_label = "Change Category"
    bl_description = "This will change the active object category"
    
    category_name = StringProperty(name="Category Name")
    
    def execute(self, context):
        scene = context.scene
        library = scene.objectlib.libraries[scene.objectlib.active_library_name]
        path = os.path.join(library.path,self.category_name)
        fd.update_file_browser_space(context,path)
        context.scene.update()
        library.active_category_name = self.category_name
        return {'FINISHED'}

class OPS_Select_All_Objects_In_List(Operator):   
    bl_idname = "objectlib.select_all_objects_in_list"
    bl_label = "Select All Objects In List"
    bl_description = "This will select all of the items in the object list"
    
    select_all = BoolProperty(name="Select All",default=True)
    
    @classmethod
    def poll(cls, context):
        wm = context.window_manager.objectlib
        if len(wm.objects_in_category) > 0:
            return True
        else:
            return False

    def execute(self,context):
        wm = context.window_manager.objectlib
        for obj in wm.objects_in_category:
            obj.selected = self.select_all
        return{'FINISHED'}
                
class OPS_Save_Selected_Object_to_Category(Operator):
    bl_idname = "objectlib.save_selected_object_to_category"
    bl_label = "Save Selected Object to Category"
    bl_description = "This will save the selected object to the active category"

    create_thumbnail = BoolProperty(name="Create Thumbnail")

    @classmethod
    def poll(cls, context):
        if bpy.data.filepath != "" and context.object:
            return True
        else:
            return False

    def execute(self, context):
        obj = context.object
        filepath = bpy.data.filepath
        path = fd.get_file_browser_path(context)
        blend_path = os.path.join(path,obj.name + ".blend")
        thumbnail_path = os.path.join(path,obj.name + ".png")
        import subprocess

        script = object_utils.save_object_script(filepath, obj.name, blend_path)
        subprocess.call(bpy.app.binary_path + ' -b --python "' + script + '"')

        if self.create_thumbnail:
            script = object_utils.create_thumbnail_script(blend_path, obj.name, thumbnail_path)
            subprocess.call(bpy.app.binary_path + ' "' + object_utils.get_thumbnail_path() + '" -b --python "' + script + '"')
        return {'FINISHED'}
    
    def invoke(self,context,event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=380)

    def draw(self, context):
        layout = self.layout
        obj = context.object
        if obj:
            path = fd.get_file_browser_path(context)
            foldername = os.path.basename(os.path.normpath(path))
            layout.label("Are you sure you want to save this object to this category?",icon='QUESTION')
            layout.label("Object: " + obj.name,icon='OBJECT_DATA')
            layout.label("Category: " + foldername,icon='FILE_FOLDER')
            layout.prop(self,'create_thumbnail')
        
class OPS_Create_Thumbnails(Operator):   
    bl_idname = "objectlib.create_thumbnails"
    bl_label = "Render Object"
    bl_description = "This will render thumbnails of all of the items in the object list. (You must have the file saved with an active camera)"
    
    object_name = StringProperty(name="Object Name")
    file_name = StringProperty(name="File Name")
    save_file_to_path = BoolProperty(name="Save File to Path",default=True)
    
    object_names = []
    
    @classmethod
    def poll(cls, context):
        wm = context.window_manager.objectlib
        if len(wm.objects_in_category) > 0:
            if fd.get_file_browser_path(context):
                return True
            else:
                return False
        else:
            return False
    
    def execute(self,context):
        import subprocess
        wm = context.window_manager.objectlib
        for obj in wm.objects_in_category:
            if obj.selected:
                script = object_utils.create_thumbnail_script(obj.filepath, 
                                                              obj.name, 
                                                              os.path.join(fd.get_file_browser_path(context),obj.name))
                subprocess.call(bpy.app.binary_path + ' "' + object_utils.get_thumbnail_path() + '" -b --python "' + script + '"')
        return{'FINISHED'}
        
class OPS_Load_Objects_From_Category(Operator):
    bl_idname = "objectlib.load_objects_from_category"
    bl_label = "Load Objects From Category"
    bl_description = "This will load all of the objects in the active category into a list"
    
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
        wm = context.window_manager.objectlib
        path = fd.get_file_browser_path(context)
        files = os.listdir(path)
        for obj in wm.objects_in_category:
            wm.objects_in_category.remove(0)
            
        for file in files:
            filename, ext = os.path.splitext(file)
            if ext == '.blend':
                filepath = os.path.join(path,file)
                if os.path.isfile(filepath):
                    with bpy.data.libraries.load(filepath, False, False) as (data_from, data_to):
                        
                        for index, object in enumerate(data_from.objects):
                            obj = wm.objects_in_category.add()
                            obj.name = object
                            obj.filename = filename
                            obj.filepath = filepath
                            obj.has_thumbnail = self.found_thumbnail(files, obj.name)

        return{'FINISHED'}
        
class OPS_Append_Objects_From_Category(Operator):   
    bl_idname = "objectlib.append_objects_from_category"
    bl_label = "Append Objects From Category"
    bl_options = {'UNDO'}
    bl_description = "This will append all of the selected objects in the object list into the scene"
    
    placement_spacing = FloatProperty(name="Placement Spacing",default=0,unit='LENGTH')
    
    @classmethod
    def poll(cls, context):
        wm = context.window_manager.objectlib
        if len(wm.objects_in_category) > 0:
            if fd.get_file_browser_path(context):
                return True
            else:
                return False
        else:
            return False

    def invoke(self,context,event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=280)

    def execute(self,context):
        wm = context.window_manager.objectlib
        scene = context.scene
        objs = []
        
        for obj in wm.objects_in_category:
            if obj.selected:
                with bpy.data.libraries.load(obj.filepath, False, False) as (data_from, data_to):
                    data_to.objects = [obj.name]
                            
                for obj2 in data_to.objects:
                    objs.append(obj2)

        for index, obj3 in enumerate(objs):
            item = context.scene.objectlib.scene_objects.add()
            item.name = obj3.name
            context.scene.objects.link(obj3)
            obj3.location = scene.cursor_location
            obj3.location.x = self.placement_spacing * index

        return{'FINISHED'}

    def draw(self, context):
        layout = self.layout
        layout.prop(self,'placement_spacing')
                
#------REGISTER
classes = [
           OPS_Open,
           OPS_Drop,
           OPS_View_Selected,
           OPS_Delete,
           OPS_Change_Library,
           OPS_Change_Category,
           OPS_Add_Object_To_List,
           OPS_Save_Selected_Object_to_Category,
           OPS_Select_All_Objects_In_List,
           OPS_Create_Thumbnails,
           OPS_Load_Objects_From_Category,
           OPS_Append_Objects_From_Category
           ]

def register():
    for c in classes:
        bpy.utils.register_class(c)

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)

if __name__ == "__main__":
    register()
