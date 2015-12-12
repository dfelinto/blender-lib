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

from bpy.types import Header, Menu, Panel, PropertyGroup, UIList
from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       BoolVectorProperty,
                       PointerProperty,
                       CollectionProperty,
                       EnumProperty)

class HEADER_Group_library_Filebrowser(Header):
    bl_space_type = 'FILE_BROWSER'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        if scene.mv.active_addon_name == 'Group Library':
            if scene.grouplib.active_category_name in scene.grouplib.categories:
                category = scene.grouplib.categories[scene.grouplib.active_category_name]
                layout.menu('MENU_Group_Libraries',text="    " + category.name + "    ",icon='GROUP')
            else:
                layout.label('No Categories',icon='ERROR')
            layout.menu('MENU_Group_library_File_Browser_Options',text="",icon='QUESTION')
            
class MENU_Group_Libraries(Menu):
    bl_label = "Libraries"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        categories = scene.grouplib.categories
        for category in categories:
            layout.operator('grouplib.change_directory',text=category.name,icon='GROUP').path = category.path

class MENU_Group_library_File_Browser_Options(Menu):
    bl_label = "Group File Browser View Options"

    def draw(self, context):
        layout = self.layout
        st = context.space_data
        params = st.params
        layout.operator("fd_general.open_browser_window",text="Open in Browser",icon='FILE_FOLDER').path = fd.get_file_browser_path(context)
        layout.prop(params, "use_filter_blender", text="Show Blender Files")

class MENU_Group_Category_Options(Menu):
    bl_label = "Group Category Options"

    def draw(self, context):
        layout = self.layout
        layout.operator("grouplib.select_all_groups_in_list",text="Select All",icon='CHECKBOX_HLT').select_all = True
        layout.operator("grouplib.select_all_groups_in_list",text="Deselect All",icon='CHECKBOX_DEHLT').select_all = False
        layout.separator()
        layout.operator("grouplib.create_thumbnails",text="Create Thumbnails for Selected Groups",icon='RENDER_RESULT')
        layout.operator("grouplib.append_groups_from_category",text="Append Selected Groups To Scene",icon='APPEND_BLEND')
        layout.separator()
        layout.operator("grouplib.save_selected_group_to_category",text="Save Selected Group to Library",icon='FILE_TICK')

class MENU_Group_Scene_Options(Menu):
    bl_label = "Group Scene Options"

    def draw(self, context):
        layout = self.layout
        layout.operator("fd_group.clear_all_groups_from_file",icon='PANEL_CLOSE')
        

class PANEL_Group_3dview(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_context = "objectmode"
    bl_label = " "
    bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        scene = context.scene
        if scene.mv.active_addon_name == 'Group Library':
            return True
        else:
            return False

    def draw(self, context):
        layout = self.layout
        mainbox = layout.box()
        row = mainbox.row()
        row.label('Name: Group Library')
        row.label(text='',icon='GROUP')
        mainbox.label('Author: Microvellum, Inc.')
        mainbox.label('Version: 1.0')

class PANEL_Groups_In_Scene(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_context = "objectmode"
    bl_label = "Groups in Scene"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        scene = context.scene
        if scene.mv.active_addon_name == 'Group Library':
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
        row.menu('MENU_Group_Scene_Options',text="Options",icon='DOWNARROW_HLT')
        col.template_list("LIST_Groups",
                          " ",
                          bpy.data,
                          "groups",
                          scene.grouplib,
                          "active_group_index")
        if len(bpy.data.groups) > 0:
            group = bpy.data.groups[scene.grouplib.active_group_index]
            box = col.box()
            box.label(text="Category Name: " + group.grouplib.category_name,icon='FILE_FOLDER')

class PANEL_Groups_In_Category(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_context = "objectmode"
    bl_label = "Groups In Category"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        scene = context.scene
        if scene.mv.active_addon_name == 'Group Library':
            return True
        else:
            return False

    def draw_header(self, context):
        layout = self.layout
        layout.label('',icon='FILE_FOLDER')

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager.grouplib
        col = layout.column(align=True)
        box = col.box()
        row = box.row(align=True)
        row.scale_y = 1.3
        row.operator('grouplib.load_groups_from_category',text='Load Groups From Category',icon='FORWARD')
        row.menu('MENU_Group_Category_Options',text="",icon='DOWNARROW_HLT')
        col.template_list("LIST_Library_Groups",
                          " ",
                          wm,
                          "groups_in_category",
                          wm,
                          "groups_in_category_index")

class LIST_Groups(UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.label(text=str(item.name),icon='GROUP')
        layout.operator("grouplib.view_group", text="",icon='VIEWZOOM', emboss=False).group_name = item.name
        prop = layout.operator("grouplib.hide_group", text="",icon='RESTRICT_VIEW_OFF', emboss=False)
        prop.group_name = item.name
        prop.hide_objects = False
        prop = layout.operator("grouplib.hide_group", text="",icon='RESTRICT_VIEW_ON', emboss=False)
        prop.group_name = item.name
        prop.hide_objects = True
        layout.operator('fd_group.show_group_options',text="",icon='INFO',emboss=False).group_name = item.name
        layout.operator("grouplib.delete", text="",icon='X', emboss=False).group_name = item.name

class LIST_Library_Groups(UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.label(text=item.filename + ".blend/",icon='FILE_BLEND')
        if item.has_thumbnail:
            layout.label(text=item.name,icon='GROUP')
        else:
            layout.label(text=item.name,icon='ERROR')
        layout.prop(item, "selected", text="")
        
#------REGISTER
classes = [
           HEADER_Group_library_Filebrowser,
           MENU_Group_Libraries,
           MENU_Group_library_File_Browser_Options,
           MENU_Group_Category_Options,
           MENU_Group_Scene_Options,
           PANEL_Group_3dview,
           PANEL_Groups_In_Scene,
           PANEL_Groups_In_Category,
           LIST_Groups,
           LIST_Library_Groups
           ]

def register():
    for c in classes:
        bpy.utils.register_class(c)

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)

if __name__ == "__main__":
    register()
