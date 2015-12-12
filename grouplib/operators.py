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

from bpy.app.handlers import persistent

from . import group_utils
from . import properties

class OPS_change_directory(Operator):
    bl_idname = "grouplib.change_directory"
    bl_label = "Change Directory"
    bl_options = {'UNDO'}
    
    path = StringProperty(name="Path")
    
    def execute(self, context):
        scene = context.scene
        directory, category = os.path.split(self.path)
        scene.grouplib.active_category_name = category
        fd.update_file_browser_space(context,self.path)
        return {'FINISHED'}

class OPS_open(Operator):
    bl_idname = "grouplib.open"
    bl_label = "Groups Library"
    bl_description = "This will open the group library"
    bl_options = {'UNDO'}

    def execute(self, context):
        scene = context.scene
        path = group_utils.get_group_library_path()
        
        for category in scene.grouplib.categories:
            scene.grouplib.categories.remove(0)
        
        dirs = os.listdir(path)

        for directory in dirs:
            catpath = os.path.join(path,directory)
            if os.path.isdir(catpath):
                cat = scene.grouplib.categories.add()
                cat.name = directory
                cat.path = catpath
        
        if len(scene.grouplib.categories) > 0:
            category = scene.grouplib.categories[0]
            if context.screen.show_fullscreen:
                fd.update_file_browser_space(context,group_utils.get_group_library_path())
            else:
                bpy.ops.grouplib.change_directory(path=category.path)
        
        scene.mv.active_addon_name = "Group Library"
        return {'FINISHED'}

class OPS_drop(Operator):
    bl_idname = "grouplib.drop"
    bl_label = "Drop Group"
    bl_options = {'UNDO'}
    
    #READONLY
    filepath = StringProperty(name="Filepath",
                              subtype='FILE_PATH')
    
    objectname = StringProperty(name="Object Name")
    
    grp = None
    grp_z_loc = 0
    
    obj_bps = []
    obj_bools = []
    cages = []
    
    def get_group(self,context):
        self.cages = []
        self.obj_bps = []
        self.obj_bools = []
        self.grp = group_utils.get_group_from_file(context,self.filepath)
        for obj in self.grp.objects:
            obj.draw_type = 'WIRE'
            if obj.mv.type == 'CAGE':
                self.cages.append(obj)
            if obj.mv.use_as_bool_obj:
                self.obj_bools.append(obj)
            if not obj.parent:
                self.grp_z_loc = obj.location.z
                fd.link_objects_to_scene(obj, context.scene)
                self.obj_bps.append(obj)
                self.set_xray(obj)
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
        bpy.ops.object.select_all(action='DESELECT')
        self.get_group(context)
        self.set_up_opengl(context)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
        
    def cancel_drop(self,context,event):
        bpy.context.window.cursor_set('DEFAULT')
        bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
        return {'FINISHED'}

    def set_xray(self,obj_bp,turn_on=True):
        if turn_on:
            draw_type = 'WIRE'
        else:
            draw_type = 'TEXTURED'
        obj_bp.draw_type = draw_type
        for child in obj_bp.children:
            child.draw_type = draw_type
            child.show_x_ray = turn_on
            self.set_xray(child, turn_on)

    def assign_boolean(self,obj):
        if obj:
            for obj_bool in self.obj_bools:
                mod = obj.modifiers.new(obj_bool.name,'BOOLEAN')
                mod.object = obj_bool
                mod.operation = 'DIFFERENCE'

    def set_wall_as_parent(self,obj_wall_bp,obj_bp):
        x_loc = fd.calc_distance((obj_bp.location.x,obj_bp.location.y,0),
                                (obj_wall_bp.matrix_local[0][3],obj_wall_bp.matrix_local[1][3],0))
        obj_bp.location.x = 0
        obj_bp.location.y = 0
        obj_bp.parent = obj_wall_bp
        obj_bp.rotation_euler = (0,0,0)
        obj_bp.location.x = x_loc

    def place_group(self,context,selected_obj):
        obj_wall_bp = fd.get_wall_bp(selected_obj)
        for obj_bp in self.obj_bps:
            self.set_xray(obj_bp, False)
            if obj_wall_bp:
                self.set_wall_as_parent(obj_wall_bp, obj_bp)
        self.assign_boolean(selected_obj)
        fd.delete_obj_list(self.cages)
        group = context.scene.grouplib.scene_groups.add()
        group.name = self.grp.name
        for obj_bp in self.obj_bps:
            obj_bp.select = True
            context.scene.objects.active = obj_bp

    def modal(self, context, event):
        self.header_text = "Place Group: (Left Click = Place Group) (Hold Shift = Place Multiple) (Esc = Cancel)"
        context.area.tag_redraw()
        selected_point, selected_obj = fd.get_selection_point(context,event)
        obj_wall_bp = fd.get_wall_bp(selected_obj)
        for obj_bp in self.obj_bps:
            if obj_wall_bp:
                obj_bp.location.x = selected_point[0]
                obj_bp.location.y = selected_point[1]
                obj_bp.location.z = self.grp_z_loc
                obj_bp.rotation_euler = obj_wall_bp.rotation_euler
            else:
                obj_bp.location = selected_point

        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            self.place_group(context,selected_obj)
            if event.shift:
                self.get_group(context)
            else:
                return self.cancel_drop(context,event)

        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            return {'PASS_THROUGH'}
         
        if event.type == 'ESC':
            obj_list = []
            for obj in self.grp.objects:
                obj_list.append(obj)
            fd.delete_obj_list(obj_list)
            return self.cancel_drop(context,event)
         
        return {'RUNNING_MODAL'}
        
class OPS_Add_Group_To_List(Operator):
    bl_idname = "grouplib.add_group_to_list"
    bl_label = "Add Group To List"
    bl_description = "This will add the selected group to the group list"

    groups = CollectionProperty(name="Groups",type=properties.Category_Group)

    @classmethod
    def poll(cls, context):
        if context.object:
            if len(context.object.users_group) > 0:
                return True
            else:
                return False
        else:
            return False

    def execute(self, context):
        grps = context.scene.grouplib.scene_groups
        for grp in self.groups:
            if grp.selected and grp.name not in grps:
                group = grps.add()
                group.name = grp.name
        return {'FINISHED'}
        
    def invoke(self,context,event):
        for grp in self.groups:
            self.groups.remove(0)
            
        obj = context.object
        
        for grp in obj.users_group:
            group = self.groups.add()
            group.name = grp.name
            group.selected = True
            
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=380)
        
    def draw(self, context):
        layout = self.layout
        if len(self.groups) == 0:
            layout.label("This object has no groups?",icon='ERROR')
        else:
            layout.label("Select the groups to add to the list?",icon='QUESTION')
            for grp in self.groups:
                row = layout.row()
                row.label("Group: " + grp.name,icon='GROUP')
                row.prop(grp,"selected",text="")
        
class OPS_Select_All_Groups_In_List(Operator):   
    bl_idname = "grouplib.select_all_groups_in_list"
    bl_label = "Select All Groups in List"
    bl_description = "This will select all of the items in the group list"
    
    select_all = BoolProperty(name="Select All",default=True)
    
    @classmethod
    def poll(cls, context):
        wm = context.window_manager.grouplib
        if len(wm.groups_in_category) > 0:
            return True
        else:
            return False

    def execute(self,context):
        wm = context.window_manager.grouplib
        for obj in wm.groups_in_category:
            obj.selected = self.select_all
        return{'FINISHED'}
        
class OPS_Delete(Operator):
    bl_idname = "grouplib.delete"
    bl_label = "Delete Group"
    bl_description = "This will delete the group list"
    
    group_name = StringProperty(name="Group Name")

    def execute(self,context):
        if self.group_name in bpy.data.groups:
            grp = bpy.data.groups[self.group_name]
            obj_list = []
            for obj in grp.objects:
                obj_list.append(obj)
            fd.delete_obj_list(obj_list)
            bpy.data.groups.remove(grp)
        for index, group in enumerate(context.scene.grouplib.scene_groups):
            if group.name == self.group_name:
                context.scene.grouplib.scene_groups.remove(index)
                break
        return{'FINISHED'}
        
    def invoke(self,context,event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=400)
        
    def draw(self, context):
        layout = self.layout
        layout.label("Are you sure you want to delete " + self.group_name)
        
class OPS_Hide_Group(Operator):
    bl_idname = "grouplib.hide_group"
    bl_label = "Delete Group"
    bl_description = "This will delete the group list"
    
    group_name = StringProperty(name="Group Name")
    hide_objects = BoolProperty(name="Hide Objects")
    
    def execute(self,context):
        grp = bpy.data.groups[self.group_name]
        obj_list = []
        for obj in grp.objects:
            obj_list.append(obj)

        for obj in obj_list:
            if self.hide_objects:
                obj.hide = True
            else:
                if obj.type != 'EMPTY':
                    obj.hide = False
        return{'FINISHED'}
        
class OPS_View_Group(Operator):
    bl_idname = "grouplib.view_group"
    bl_label = "View Group"
    bl_description = "This will zoom to the group"
    
    group_name = StringProperty(name="Group Name")

    def execute(self,context):
        grp = bpy.data.groups[self.group_name]
        bpy.ops.object.select_all(action='DESELECT')
        obj_list = []
        for obj in grp.objects:
            obj_list.append(obj)

        for obj in obj_list:
            obj.select = True
            context.scene.objects.active = obj
        bpy.ops.view3d.view_selected()
        return{'FINISHED'}
        
class OPS_Save_Selected_Group_to_Category(Operator):
    bl_idname = "grouplib.save_selected_group_to_category"
    bl_label = "Save Selected Group to Category"
    bl_description = "This will save the selected group to the active category"
    
    create_thumbnail = BoolProperty(name="Create Thumbnail")
    
    groups = CollectionProperty(name="Groups",type=properties.Category_Group)
    
    @classmethod
    def poll(cls, context):
        if context.object and bpy.data.filepath != "":
            if len(context.object.users_group) > 0:
                return True
            else:
                return False
        else:
            return False
    
    def execute(self, context):
        for group in self.groups:
            if group.selected:
                grp = bpy.data.groups[group.name]
                filepath = bpy.data.filepath
                path = fd.get_file_browser_path(context)
                blend_path = os.path.join(path,grp.name + ".blend")
                thumbnail_path = os.path.join(path,grp.name + ".png")
                import subprocess
                
                script = group_utils.save_group_script(filepath, grp.name, blend_path)
                subprocess.call([bpy.app.binary_path, '-b', '--python', script])
                
                if self.create_thumbnail:
                    script = group_utils.create_thumbnail_script(blend_path, grp.name, thumbnail_path)
                    subprocess.call([bpy.app.binary_path, group_utils.get_thumbnail_path(), '-b', '--python', script])
        return {'FINISHED'}
    
    def invoke(self,context,event):
        for grp in self.groups:
            self.groups.remove(0)
        
        for grp in context.object.users_group:
            group = self.groups.add()
            group.name = grp.name
            group.selected = True
        
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=380)

    def draw(self, context):
        layout = self.layout
        obj = context.object
        if obj:
            path = fd.get_file_browser_path(context)
            foldername = os.path.basename(os.path.normpath(path))
            if len(self.groups) == 0:
                layout.label("The object you have selected is not part of a group?",icon='ERROR')
            else:
                if len(self.groups) == 1:
                    layout.label("Are you sure you want to save this group to this category?",icon='QUESTION')
                    layout.label("Group: " + self.groups[0].name,icon='GROUP')
                    layout.label("Category: " + foldername,icon='FILE_FOLDER')
                    layout.prop(self,'create_thumbnail')
                else:
                    layout.label("Select the groups you want to save to this category?",icon='QUESTION')
                    for group in self.groups:
                        row = layout.row()
                        row.label("Group: " + group.name,icon='GROUP')
                        row.prop(group,'selected',text="")
                    layout.label("Category: " + foldername,icon='FILE_FOLDER')
                    layout.prop(self,'create_thumbnail')
        
class OPS_Create_Thumbnails(Operator):   
    bl_idname = "grouplib.create_thumbnails"
    bl_label = "Render Group"
    bl_description = "This will render thumbnails of all of the items in the object list. (You must have the file saved with an active camera)"
    
    object_name = StringProperty(name="Object Name")
    file_name = StringProperty(name="File Name")
    save_file_to_path = BoolProperty(name="Save File to Path",default=True)
    
    object_names = []
    
    @classmethod
    def poll(cls, context):
        wm = context.window_manager.grouplib
        if len(wm.groups_in_category) > 0 and group_utils.get_thumbnail_path():
            return True
        else:
            return False
    
    def write_script(self,filepath,thumbnail_path,group_name):
        path = group_utils.get_addon_path()
        file = open(os.path.join(path,"thumbnail.py"),'w')
        file.write("import bpy\n")
        file.write("with bpy.data.libraries.load(r'" + filepath + "', False, True) as (data_from, data_to):\n")
        file.write("    for obj in data_from.groups:\n")
        file.write("        if obj == '" + group_name + "':\n")
        file.write("            data_to.groups = [obj]\n")
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
        return os.path.join(path,'thumbnail.py')
    
    def execute(self,context):
        import subprocess
        wm = context.window_manager.grouplib
        for obj in wm.groups_in_category:
            if obj.selected:
                script = self.write_script(obj.filepath, os.path.join(fd.get_file_browser_path(context),obj.name), obj.name)
                subprocess.call([bpy.app.binary_path, group_utils.get_thumbnail_path(), '-b', '--python', script])
        return{'FINISHED'}
        
class OPS_Load_Groups_From_Category(Operator):   
    bl_idname = "grouplib.load_groups_from_category"
    bl_label = "Load Groups From Category"
    bl_description = "This will load all of the groups in the active category into a list"
    
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
        wm = context.window_manager.grouplib
        path = fd.get_file_browser_path(context)
        files = os.listdir(path)
        for obj in wm.groups_in_category:
            wm.groups_in_category.remove(0)
            
        for file in files:
            filename, ext = os.path.splitext(file)
            if ext == '.blend':
                filepath = os.path.join(path,file)
                if os.path.isfile(filepath):
                    with bpy.data.libraries.load(filepath, False, False) as (data_from, data_to):
                        
                        for index, group in enumerate(data_from.groups):
                            grp = wm.groups_in_category.add()
                            grp.name = group
                            grp.filename = filename
                            grp.filepath = filepath
                            grp.has_thumbnail = self.found_thumbnail(files, grp.name)

        return{'FINISHED'}
        
class OPS_Append_Groups_From_Category(Operator):   
    bl_idname = "grouplib.append_groups_from_category"
    bl_label = "Append Groups From Category"
    bl_options = {'UNDO'}
    bl_description = "This will append all of the selected groups in the object list into the scene"
    
    placement_spacing = FloatProperty(name="Placement Spacing",default=0,unit='LENGTH')
    
    @classmethod
    def poll(cls, context):
        if fd.get_file_browser_path(context):
            return True
        else:
            return False

    def invoke(self,context,event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=280)

    def execute(self,context):
        wm = context.window_manager.grouplib
        scene = context.scene
        grps = []
        
        for grp in wm.groups_in_category:
            if grp.selected:
                with bpy.data.libraries.load(grp.filepath, False, False) as (data_from, data_to):
                    data_to.groups = [grp.name]

                for grp in data_to.groups:
                    grps.append(grp)

        obj_bps = []
        
        for index, grp in enumerate(grps):
            item = context.scene.grouplib.scene_groups.add()
            item.name = grp.name
            for obj in grp.objects:
                if obj.parent is None:
                    obj_bps.append(obj)
                scene.objects.link(obj)
                obj.parent = obj.parent #THIS IS NEEDED FOR SOME REASON
        
        for index, obj in enumerate(obj_bps):
            obj.location.x = self.placement_spacing * index

        return{'FINISHED'}
        
    def draw(self, context):
        layout = self.layout
        layout.prop(self,'placement_spacing')
        
#------REGISTER
classes = [
           OPS_change_directory,
           OPS_open,
           OPS_drop,
           OPS_Add_Group_To_List,
           OPS_Select_All_Groups_In_List,
           OPS_Delete,
           OPS_View_Group,
           OPS_Hide_Group,
           OPS_Save_Selected_Group_to_Category,
           OPS_Create_Thumbnails,
           OPS_Load_Groups_From_Category,
           OPS_Append_Groups_From_Category
           ]

def register():
    for c in classes:
        bpy.utils.register_class(c)

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)

if __name__ == "__main__":
    register()
