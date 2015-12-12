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
import fd
from bpy.types import Header, Menu, Panel, UIList
from . import object_utils

class HEADER_Object_library_Filebrowser(Header):
    bl_space_type = 'FILE_BROWSER'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        if scene.mv.active_addon_name == 'Object Library':
            if scene.objectlib.active_library_name in scene.objectlib.libraries:
                library = scene.objectlib.libraries[scene.objectlib.active_library_name]
                layout.menu('MENU_Object_Libraries',text="    " + library.name + "    ",icon='OBJECT_DATA')
                if library.active_category_name in library.categories:
                    category = library.categories[library.active_category_name]
                    layout.menu('MENU_Object_Categories',text="    " + category.name + "    ",icon='FILE_FOLDER')
            else:
                layout.label('No Categories',icon='ERROR')
            layout.menu('MENU_Object_library_File_Browser_Options',text="",icon='QUESTION')
            
class MENU_Object_Libraries(Menu):
    bl_label = "Libraries"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        libraries = scene.objectlib.libraries
        for library in libraries:
            layout.operator('objectlib.change_library',
                            text=library.name,
                            icon='OBJECT_DATA').library_name = library.name

class MENU_Object_Categories(Menu):
    bl_label = "Categories"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        library = scene.objectlib.libraries[scene.objectlib.active_library_name]
        categories = library.categories
        for category in categories:
            layout.operator('objectlib.change_category',
                            text=category.name,
                            icon='OBJECT_DATA').category_name = category.name

class MENU_Object_library_File_Browser_Options(Menu):
    bl_label = "Object File Browser View Options"

    def draw(self, context):
        layout = self.layout
        st = context.space_data
        params = st.params
        layout.operator("fd_general.open_browser_window",text="Open in Browser",icon='FILE_FOLDER').path = fd.get_file_browser_path(context)
        layout.prop(params, "use_filter_blender", text="Show Blender Files")

class MENU_Object_Category_Options(Menu):
    bl_label = "Object Category Options"

    def draw(self, context):
        layout = self.layout
        layout.operator("objectlib.select_all_objects_in_list",text="Select All",icon='CHECKBOX_HLT').select_all = True
        layout.operator("objectlib.select_all_objects_in_list",text="Deselect All",icon='CHECKBOX_DEHLT').select_all = False
        layout.separator()
        layout.operator("objectlib.create_thumbnails",text="Create Thumbnails for Selected Objects",icon='RENDER_RESULT')
        layout.operator("objectlib.append_objects_from_category",text="Append Selected Objects To Scene",icon='APPEND_BLEND')
        layout.separator()
        layout.operator("objectlib.save_selected_object_to_category",text="Save Selected Object to Library",icon='FILE_TICK')

class MENU_Object_Scene_Options(Menu):
    bl_label = "Object Scene Options"

    def draw(self, context):
        layout = self.layout
        

class PANEL_Object_3dview(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_context = "objectmode"
    bl_label = " "
    bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        scene = context.scene
        if scene.mv.active_addon_name == 'Object Library':
            return True
        else:
            return False

    def draw(self, context):
        layout = self.layout
        mainbox = layout.box()
        row = mainbox.row()
        row.label('Name: Object Library')
        row.label(text='',icon='OBJECT_DATA')
        mainbox.label('Author: Microvellum, Inc.')
        mainbox.label('Version: 1.0')

class PANEL_Objects_In_Scene(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_context = "objectmode"
    bl_label = "Objects in Scene"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        scene = context.scene
        if scene.mv.active_addon_name == 'Object Library':
            return True
        else:
            return False

    def draw_header(self, context):
        layout = self.layout
        layout.label('',icon='SCENE_DATA')

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        col = layout.column(align=True)
        box = col.box()
        row = box.row(align=True)
        row.scale_y = 1.3
        row.operator('objectlib.add_object_to_list',text='Add Selected Object to List',icon='TRIA_DOWN')
#         row.menu('MENU_Object_Scene_Options',text="",icon='DOWNARROW_HLT')
        col.template_list("LIST_Objects",
                          " ", 
                          scene.objectlib, 
                          "scene_objects", 
                          scene.objectlib, 
                          "active_object_index")
        if len(scene.objectlib.scene_objects) > 0:
            ob = scene.objectlib.scene_objects[scene.objectlib.active_object_index]
            if ob.name in bpy.data.objects:
                obj = bpy.data.objects[ob.name]
                box = col.box()
                box.label(text="Library Name: " + obj.objectlib.library_name,icon='OBJECT_DATA')
                box.label(text="Category Name: " + obj.objectlib.category_name,icon='FILE_FOLDER')

class PANEL_Objects_In_Category(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_context = "objectmode"
    bl_label = "Objects In Category"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        scene = context.scene
        if scene.mv.active_addon_name == 'Object Library':
            return True
        else:
            return False

    def draw_header(self, context):
        layout = self.layout
        layout.label('',icon='FILE_FOLDER')

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager.objectlib
        col = layout.column(align=True)
        box = col.box()
        row = box.row(align=True)
        row.scale_y = 1.3
        row.operator('objectlib.load_objects_from_category',text='Load Objects From Category',icon='FORWARD')
        row.menu('MENU_Object_Category_Options',text="",icon='DOWNARROW_HLT')
        col.template_list("LIST_Library_Objects",
                             " ", 
                             wm, 
                             "objects_in_category", 
                             wm, 
                             "objects_in_category_index")
        
class LIST_Objects(UIList):
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if not item.name in context.scene.objects:
            layout.label(text=item.name + " (missing)",icon='ERROR')
        obj = bpy.data.objects[item.name]
        layout.label(text=str(item.name),icon='OBJECT_DATA')
        layout.prop(obj, "hide", text="", emboss=False)
        layout.operator("objectlib.view_selected", text="", icon='VIEWZOOM', emboss=False).object_name = obj.name 
        layout.operator("objectlib.delete", text="",icon='X', emboss=False).object_name = obj.name

class LIST_Library_Objects(UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.label(text=item.filename + ".blend/",icon='FILE_BLEND')
        if item.has_thumbnail:
            layout.label(text=item.name,icon='OBJECT_DATA')
        else:
            layout.label(text=item.name,icon='ERROR')
        layout.prop(item, "selected", text="")

#------REGISTER
classes = [
           HEADER_Object_library_Filebrowser,
           MENU_Object_Libraries,
           MENU_Object_Categories,
           MENU_Object_library_File_Browser_Options,
           MENU_Object_Category_Options,
           MENU_Object_Scene_Options,
           PANEL_Object_3dview,
           PANEL_Objects_In_Scene,
           PANEL_Objects_In_Category,
           LIST_Objects,
           LIST_Library_Objects
           ]

def register():
    for c in classes:
        bpy.utils.register_class(c)

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)

if __name__ == "__main__":
    register()
