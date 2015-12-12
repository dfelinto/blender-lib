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

bl_info = {
    "name": "Material Library",
    "author": "Microvellum, Inc.",
    "version": (1, 0, 0),
    "blender": (2, 71, 0),
    "location": "View 3D>Tools Panel>Library",
    "warning": "",
    "description": "This is the base library that stores objects, materials, worlds, and groups",
    "wiki_url": "http://www.microvellum.com",
    "category": "Microvellum",
    "fd_open_id":"materiallib.open",
    "fd_drop_id":"materiallib.drop",
    "icon":"MATERIAL",
}

import bpy
import fd

from bpy.types import Header, Menu, Panel, UIList

from . import material_utils

class HEADER_Material_library_Filebrowser(Header):
    bl_space_type = 'FILE_BROWSER'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        if scene.mv.active_addon_name == 'Material Library':
            if scene.materiallib.active_category_name in scene.materiallib.categories:
                category = scene.materiallib.categories[scene.materiallib.active_category_name]
                layout.menu('MENU_Material_Categories',text="    " + category.name + "    ",icon='MATERIAL')
            else:
                layout.label('No Categories',icon='ERROR')
            layout.menu('MENU_Material_library_File_Browser_Options',text="",icon='QUESTION')
            
class MENU_Material_Categories(Menu):
    bl_label = "Libraries"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        categories = scene.materiallib.categories
        for category in categories:
            layout.operator('materiallib.change_directory',text=category.name,icon='MATERIAL').path = category.path

class MENU_Material_library_File_Browser_Options(Menu):
    bl_label = "Material File Browser View Options"

    def draw(self, context):
        layout = self.layout
        st = context.space_data
        params = st.params
        layout.operator("fd_general.open_browser_window",text="Open in Browser",icon='FILE_FOLDER').path = fd.get_file_browser_path(context)
        layout.prop(params, "use_filter_blender", text="Show Blender Files")
        
class MENU_Material_Category_Options(Menu):
    bl_label = "Material Category Options"

    def draw(self, context):
        layout = self.layout
        layout.operator("materiallib.select_all_materials_in_list",text="Select All",icon='CHECKBOX_HLT').select_all = True
        layout.operator("materiallib.select_all_materials_in_list",text="Deselect All",icon='CHECKBOX_DEHLT').select_all = False
        layout.separator()
        layout.operator("materiallib.create_thumbnails",text="Create Thumbnails for Selected Materials",icon='RENDER_RESULT')
        layout.operator("materiallib.append_materials_from_category",text="Append Selected Materials To Scene",icon='APPEND_BLEND')
        layout.separator()
        layout.operator("materiallib.save_selected_material_to_category",text="Save Selected Material to Library",icon='FILE_TICK')

class MENU_Material_Scene_Options(Menu):
    bl_label = "Material Scene Options"

    def draw(self, context):
        layout = self.layout
        layout.operator("fd_material.clear_unused_materials_from_file",text="Clear Unused Materials",icon='ZOOMOUT')
        layout.operator("fd_material.clear_all_materials_from_file",text="Clear All Materials From Scene",icon='PANEL_CLOSE')

class PANEL_Material_3dview(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_context = "objectmode"
    bl_label = " "
    bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        scene = context.scene
        if scene.mv.active_addon_name == 'Material Library':
            return True
        else:
            return False
        
    def draw(self, context):
        layout = self.layout
        mainbox = layout.box()
        row = mainbox.row()
        row.label('Name: Material Library')
        row.label(text='',icon='MATERIAL')
        mainbox.label('Author: Microvellum, Inc.')
        mainbox.label('Version: 1.0')

class PANEL_Materials_In_Scene(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_context = "objectmode"
    bl_label = "Materials in Scene"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        scene = context.scene
        if scene.mv.active_addon_name == 'Material Library':
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
        row.menu('MENU_Material_Scene_Options',text="Options",icon='DOWNARROW_HLT')
        col.template_list("LIST_Materials",
                          " ", 
                          bpy.data, 
                          "materials", 
                          scene.materiallib, 
                          "active_material_index")
        if len(bpy.data.materials) > 0:
            mat = bpy.data.materials[scene.materiallib.active_material_index]
            material = bpy.data.materials[mat.name]
            box = col.box()
            box.label(text="Category Name: " + material.materiallib.category_name,icon='FILE_FOLDER')

class PANEL_Materials_In_Category(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_context = "objectmode"
    bl_label = "Materials In Category"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        scene = context.scene
        if scene.mv.active_addon_name == 'Material Library':
            return True
        else:
            return False

    def draw_header(self, context):
        layout = self.layout
        layout.label('',icon='FILE_FOLDER')

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager.materiallib
        col = layout.column(align=True)
        box = col.box()
        row = box.row(align=True)
        row.scale_y = 1.3
        row.operator('materiallib.load_materials_from_category',icon='FORWARD')
        row.menu('MENU_Material_Category_Options',text="",icon='DOWNARROW_HLT')
        col.template_list("LIST_Library_Materials",
                          " ", 
                          wm, 
                          "materials_in_category", 
                          wm, 
                          "materials_in_category_index")

class LIST_Materials(UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.label(text=str(item.name) + " (" + str(item.users) + ")",icon='MATERIAL')
        layout.operator('fd_material.material_properties',text="",icon='INFO', emboss=False).material_name = item.name
        layout.operator("materiallib.delete", text="",icon='X', emboss=False).material_name = item.name

class LIST_Library_Materials(UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.label(text=item.filename + ".blend/",icon='FILE_BLEND')
        if item.has_thumbnail:
            layout.label(text=item.name,icon='MATERIAL')
        else:
            layout.label(text=item.name,icon='ERROR')
        layout.prop(item, "selected", text="")

#------REGISTER
classes = [
           HEADER_Material_library_Filebrowser,
           MENU_Material_Categories,
           MENU_Material_library_File_Browser_Options,
           MENU_Material_Category_Options,
           MENU_Material_Scene_Options,
           PANEL_Material_3dview,
           PANEL_Materials_In_Scene,
           PANEL_Materials_In_Category,
           LIST_Materials,
           LIST_Library_Materials
           ]

def register():
    for c in classes:
        bpy.utils.register_class(c)

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)

if __name__ == "__main__":
    register()
