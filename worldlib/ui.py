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
    "name": "World Library",
    "author": "Microvellum, Inc.",
    "version": (1, 0, 0),
    "blender": (2, 71, 0),
    "location": "View 3D>Tools Panel>Library",
    "warning": "",
    "description": "This is the base library that stores objects, materials, worlds, and groups",
    "wiki_url": "http://www.microvellum.com",
    "category": "Microvellum",
    "fd_open_id":"worldlib.open",
    "fd_drop_id":"worldlib.drop",
    "icon":"WORLD",
}

import bpy
import os
import fd

from bpy.types import Header, Menu, Panel, UIList
from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       BoolVectorProperty,
                       PointerProperty,
                       CollectionProperty,
                       EnumProperty)

class HEADER_World_library_Filebrowser(Header):
    bl_space_type = 'FILE_BROWSER'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        if scene.mv.active_addon_name == 'World Library':
            if scene.worldlib.active_category_name in scene.worldlib.categories:
                category = scene.worldlib.categories[scene.worldlib.active_category_name]
                layout.menu('MENU_World_Categories',text="    " + category.name + "    ",icon='WORLD')
            else:
                layout.label('No Categories',icon='ERROR')
            layout.menu('MENU_World_library_File_Browser_Options',text="",icon='QUESTION')
            
class MENU_World_Categories(Menu):
    bl_label = "Libraries"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        categories = scene.worldlib.categories
        for category in categories:
            layout.operator('worldlib.change_directory',text=category.name,icon='WORLD').path = category.path

class MENU_World_Category_Options(Menu):
    bl_label = "World Category Options"

    def draw(self, context):
        layout = self.layout
        layout.operator("worldlib.select_all_worlds_in_list",text="Select All",icon='CHECKBOX_HLT').select_all = True
        layout.operator("worldlib.select_all_worlds_in_list",text="Deselect All",icon='CHECKBOX_DEHLT').select_all = False
        layout.separator()
        layout.operator("worldlib.create_thumbnails",text="Create Thumbnails for Selected Worlds",icon='RENDER_RESULT')
        layout.operator("worldlib.append_worlds_from_category",text="Append Selected Worlds To Scene",icon='APPEND_BLEND')
        layout.separator()
        layout.operator("worldlib.save_active_world_to_active_category",text="Save Active World to Library",icon='FILE_TICK')

class MENU_World_Scene_Options(Menu):
    bl_label = "World Scene Options"

    def draw(self, context):
        layout = self.layout
        view = context.space_data
        layout.operator("fd_world.clear_unused_worlds_from_file",text="Clear Unused Worlds",icon='ZOOMOUT')
        layout.separator()
        layout.prop(view, "show_world",text="Show World in Viewport")

class MENU_World_library_File_Browser_Options(Menu):
    bl_label = "World File Browser View Options"

    def draw(self, context):
        layout = self.layout
        st = context.space_data
        params = st.params
        layout.operator("fd_general.open_browser_window",text="Open in Browser",icon='FILE_FOLDER').path = fd.get_file_browser_path(context)
        layout.prop(params, "use_filter_blender", text="Show Blender Files")

class PANEL_World_3dview(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_context = "objectmode"
    bl_label = " "
    bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        scene = context.scene
        if scene.mv.active_addon_name == 'World Library':
            return True
        else:
            return False

    def draw(self, context):
        layout = self.layout
        view = context.space_data
        wm = context.window_manager.worldlib
        
        mainbox = layout.box()
        row = mainbox.row()
        row.label('Name: World Library')
        row.label(text='',icon='WORLD')
        mainbox.label('Author: Microvellum, Inc.')
        mainbox.label('Version: 1.0')

class PANEL_Worlds_In_Scene(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_context = "objectmode"
    bl_label = "Worlds In Scene"

    @classmethod
    def poll(cls, context):
        scene = context.scene
        if scene.mv.active_addon_name == 'World Library':
            return True
        else:
            return False

    def draw_header(self, context):
        layout = self.layout
        layout.label('',icon='WORLD')

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        view = context.space_data
        wm = context.window_manager.worldlib
        col = layout.column(align=True)
        box = col.box()
        row = box.row(align=True)
        row.scale_y = 1.3
        row.menu('MENU_World_Scene_Options',text="Options",icon='DOWNARROW_HLT')
        col.template_list("LIST_Worlds",
                          " ", 
                          bpy.data, 
                          "worlds", 
                          scene.worldlib, 
                          "active_world_index")
        
#         world = context.scene.world
#         if world and world.node_tree:
#             propbox = layout.box()
#             propbox.label("Active World Properties:")
#             propbox.prop(world,'name')
#             for node in world.node_tree.nodes:
#                 if node.type == 'BACKGROUND':
#                     propbox.prop(node.inputs[1],'default_value',text="Strength")
#                 if node.type == 'MAPPING':
#                     propbox.prop(node,'rotation')
# 
#             propbox.prop(view, "show_world",text="Show World in Viewport")
#             propbox.operator('worldlib.save_active_world_to_active_category',text="Save to Category",icon='BACK')

class PANEL_Worlds_In_Category(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_context = "objectmode"
    bl_label = "Worlds In Category"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        scene = context.scene
        if scene.mv.active_addon_name == 'World Library':
            return True
        else:
            return False

    def draw_header(self, context):
        layout = self.layout
        layout.label('',icon='FILE_FOLDER')

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager.worldlib
        col = layout.column(align=True)
        box = col.box()
        row = box.row(align=True)
        row.scale_y = 1.3
        row.operator('worldlib.load_worlds_from_category',icon='FORWARD')
        row.menu('MENU_World_Category_Options',text="",icon='DOWNARROW_HLT')
        col.template_list("LIST_Library_Worlds",
                          " ", 
                          wm, 
                          "worlds_in_category", 
                          wm, 
                          "worlds_in_category_index")

class PANEL_Create_New_World(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_context = "objectmode"
    bl_label = "Create New World"
    
    @classmethod
    def poll(cls, context):
        scene = context.scene
        if scene.mv.active_addon_name == 'World Library':
            return True
        else:
            return False

    def draw_header(self, context):
        layout = self.layout
        layout.label('',icon='ZOOMIN')

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager.worldlib

        createbox = layout.box()
        createbox.label("Create New World:")
        createbox.prop(wm,'path_to_world_image')
        createbox.operator('worldlib.create_new_world_from_image',icon='WORLD')

class LIST_Worlds(UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.label(text=str(item.name) + " (" + str(item.users) + ")",icon='WORLD')
        layout.operator('fd_world.show_world_options',text="",icon='INFO', emboss=False).world_name = item.name
        layout.operator("fd_world.remove_world", text="",icon='X', emboss=False).world_name = item.name

class LIST_Library_Worlds(UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.label(text=item.filename + ".blend/",icon='FILE_BLEND')
        if item.has_thumbnail:
            layout.label(text=item.name,icon='WORLD')
        else:
            layout.label(text=item.name,icon='ERROR')
        layout.prop(item, "selected", text="")

#------REGISTER
classes = [
           HEADER_World_library_Filebrowser,
           MENU_World_Categories,
           MENU_World_library_File_Browser_Options,
           MENU_World_Category_Options,
           MENU_World_Scene_Options,
           PANEL_World_3dview,
           PANEL_Worlds_In_Scene,
           PANEL_Create_New_World,
           LIST_Worlds,
           PANEL_Worlds_In_Category,
           LIST_Library_Worlds
           ]

def register():
    for c in classes:
        bpy.utils.register_class(c)

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)

if __name__ == "__main__":
    register()
