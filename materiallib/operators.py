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

from . import material_utils
from . import properties

class OPS_open(Operator):
    bl_idname = "materiallib.open"
    bl_label = "Open Materials"
    bl_description = "This will open the material library"
    bl_options = {'UNDO'}
  
    def execute(self, context):
        scene = context.scene
        path = material_utils.get_material_library_path()
        
        for category in scene.materiallib.categories:
            scene.materiallib.categories.remove(0)
        
        dirs = os.listdir(path)

        for directory in dirs:
            catpath = os.path.join(path,directory)
            if os.path.isdir(catpath):
                cat = scene.materiallib.categories.add()
                cat.name = directory
                cat.path = catpath
        
        if len(scene.materiallib.categories) > 0:
            category = scene.materiallib.categories[0]
            if context.screen.show_fullscreen:
                fd.update_file_browser_space(context,material_utils.get_material_library_path())
            else:
                bpy.ops.materiallib.change_directory(path=category.path)
            
        scene.mv.active_addon_name = "Material Library"
        return {'FINISHED'}
    
class OPS_drop(Operator):
    bl_idname = "materiallib.drop"
    bl_label = "Drop Material"
    bl_options = {'UNDO'}
    
    #READONLY
    filepath = StringProperty(name="Filepath")
    objectname = StringProperty(name="Object Name")
    
    obj = None
    material = None
    
    def get_material(self,context):
        self.material = material_utils.get_material_from_file(context,self.filepath)

    def cancel_drop(self,context,event):
        context.window.cursor_set('DEFAULT')
        bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
        return {'FINISHED'}
        
    def modal(self, context, event):
        self.header_text = "Place Material: (Left Click = Assign Material) (Hold Shift = Assign Multiple) (Esc = Cancel)"
        context.window.cursor_set('PAINT_BRUSH')
        context.area.tag_redraw()
        selected_point, selected_obj = fd.get_selection_point(context,event)
        bpy.ops.object.select_all(action='DESELECT')
        if selected_obj:
            selected_obj.select = True
            
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            if selected_obj and selected_obj.type == 'MESH':
                
                if len(selected_obj.data.uv_textures) == 0:
                    bpy.ops.fd_object.unwrap_mesh(object_name=selected_obj.name)
                if len(selected_obj.material_slots) > 1:
                    bpy.ops.materiallib.assign_material('INVOKE_DEFAULT',material_name = self.material.name, object_name = selected_obj.name)
                    return self.cancel_drop(context,event)
                else:
                    if len(selected_obj.material_slots) == 0:
                        bpy.ops.fd_object.add_material_slot(object_name=selected_obj.name)
                    
                    for i, mat in enumerate(selected_obj.material_slots):
                        mat.material = self.material
                        
                    if self.material.name not in context.scene.materiallib.scene_materials:
                        material = context.scene.materiallib.scene_materials.add()
                        material.name = mat.name
                
                if event.shift:
                    self.get_material(context)
                    context.window.cursor_set('PAINT_BRUSH')
                else:
                    return self.cancel_drop(context,event)
                
        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            return {'PASS_THROUGH'}
            
        if event.type == 'ESC':
            return self.cancel_drop(context,event)
            
        return {'RUNNING_MODAL'}
        
    def set_up_opengl(self,context):
        if context.area.type == 'VIEW_3D':
            args = (self, context)
            self._handle = bpy.types.SpaceView3D.draw_handler_add(fd.draw_callback_px, args, 'WINDOW', 'POST_PIXEL')
            self.mouse_loc = []
            self.mouse_text = ""
            self.header_text = ""
        
    def execute(self,context):
        path, ext = os.path.splitext(self.filepath)
        if ext == '.blend':
            bpy.ops.fd_general.open_blend_file('INVOKE_DEFAULT',filepath=self.filepath)
            return {'FINISHED'}
        self.get_material(context)
        if self.material is None:
            path, image_file = os.path.split(self.filepath)
            img_file_name, img_ext = os.path.splitext(image_file) 
            bpy.ops.fd_general.error('INVOKE_DEFAULT',message="Could Not Find " + img_file_name)
            return {'FINISHED'}
        else:
            self.set_up_opengl(context)
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}

class OPS_change_directory(Operator):
    bl_idname = "materiallib.change_directory"
    bl_label = "Change Directory"
    bl_options = {'UNDO'}
    
    path = StringProperty(name="Path")
    
    def execute(self, context):
        scene = context.scene
        directory, category = os.path.split(self.path)
        scene.materiallib.active_category_name = category
        fd.update_file_browser_space(context,self.path)
        return {'FINISHED'}

class OPS_delete(Operator):
    bl_idname = "materiallib.delete"
    bl_label = "Delete Material"
    bl_description = "This will delete the material"

    material_name = StringProperty(name="Material Name")

    def execute(self, context):
        mat = context.scene.materiallib.scene_materials[self.material_name]
        if mat:
            if mat.name in bpy.data.materials:
                material = bpy.data.materials[mat.name]
                
                for obj in bpy.data.objects:
                    for slot in obj.material_slots:
                        if slot.material == material:
                            slot.material = None
                            
                images = material_utils.get_images_from_material(material)
                for image in images:
                    image.user_clear()
                    bpy.data.images.remove(image)
                    
                material.user_clear()
                bpy.data.materials.remove(material)
            
            for index, mat2 in enumerate(context.scene.materiallib.scene_materials):
                if mat2.name == mat.name:
                    context.scene.materiallib.scene_materials.remove(index)
                    break
            
        return {'FINISHED'}
    
    def invoke(self,context,event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=500)

    def draw(self, context):
        layout = self.layout
        mat = context.scene.materiallib.scene_materials[self.material_name]
        if mat:
            layout.label("Are you sure you want to delete " + mat.name)

class OPS_assign_material(Operator):
    bl_idname = "materiallib.assign_material"
    bl_label = "Assign Material"
    bl_options = {'UNDO'}
    
    #READONLY
    material_name = StringProperty(name="Material Name")
    object_name = StringProperty(name="Object Name")
    
    obj = None
    material = None
    
    def check(self, context):
        return True
    
    def invoke(self, context, event):
        self.material = bpy.data.materials[self.material_name]
        self.obj = bpy.data.objects[self.object_name]
        if self.material.name not in context.scene.materiallib.scene_materials:
            material = context.scene.materiallib.scene_materials.add()
            material.name = self.material.name
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=400)
        
    def draw(self,context):
        layout = self.layout
        layout.label(self.obj.name,icon='OBJECT_DATA')
        for index, mat_slot in enumerate(self.obj.material_slots):
            row = layout.split(percentage=.8)
            if mat_slot.name == "":
                row.label('No Material')
            else:
                row.prop(mat_slot,"name",text="")
            props = row.operator('materiallib.assign_material_to_slot',text="Assign",icon='BACK')
            props.object_name = self.obj.name
            props.material_name = self.material.name
            props.index = index
        
    def execute(self,context):
        return {'FINISHED'}
        
class OPS_assign_material_to_slot(Operator):
    bl_idname = "materiallib.assign_material_to_slot"
    bl_label = "Assign Material to Slot"
    bl_options = {'UNDO'}
    
    #READONLY
    material_name = StringProperty(name="Material Name")
    object_name = StringProperty(name="Object Name")
    
    index = IntProperty(name="Index")
    
    obj = None
    material = None
    
    def execute(self,context):
        obj = bpy.data.objects[self.object_name]
        mat = bpy.data.materials[self.material_name]
        obj.material_slots[self.index].material = mat
        return {'FINISHED'}
        
class OPS_Select_All_Materials_In_List(Operator):   
    bl_idname = "materiallib.select_all_materials_in_list"
    bl_label = "Select All Materials In List"
    bl_description = "This will select all of the items in the material list"
    
    select_all = BoolProperty(name="Select All",default=True)
    
    @classmethod
    def poll(cls, context):
        wm = context.window_manager.materiallib
        if len(wm.materials_in_category) > 0:
            return True
        else:
            return False

    def execute(self,context):
        wm = context.window_manager.materiallib
        for obj in wm.materials_in_category:
            obj.selected = self.select_all
        return{'FINISHED'}
        
class OPS_Add_Material_To_List(Operator):
    bl_idname = "materiallib.add_material_to_list"
    bl_label = "Add Material To List"
    bl_description = "This will add the selected material to the material list"

    materials = CollectionProperty(name="Materials",type=properties.Category_Material)

    @classmethod
    def poll(cls, context):
        if context.object:
            return True
        else:
            return False

    def execute(self, context):
        mats = context.scene.materiallib.scene_materials
        for mat in self.materials:
            if mat.selected and mat.name not in mats:
                material = mats.add()
                material.name = mat.name
        return {'FINISHED'}
        
    def invoke(self,context,event):
        for mat in self.materials:
            self.materials.remove(0)
        obj = context.object
        for slot in obj.material_slots:
            if slot.material:
                mat = self.materials.add()
                mat.name = slot.material.name
                mat.selected = True
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=380)
        
    def draw(self, context):
        layout = self.layout
        if len(self.materials) == 0:
            layout.label("This object has no materials?",icon='ERROR')
        else:
            layout.label("Select the materials to add to the list?",icon='QUESTION')
            for mat in self.materials:
                row = layout.row()
                row.label("Material: " + mat.name,icon='MATERIAL')
                row.prop(mat,"selected",text="")
        
class OPS_Save_Selected_Material_to_Category(Operator):
    bl_idname = "materiallib.save_selected_material_to_category"
    bl_label = "Save Selected Material to Category"
    bl_description = "This will save the material that is assigned to the active object to this category (You must have the file saved)"

    create_thumbnail = BoolProperty(name="Create Thumbnail")

    materials = CollectionProperty(name="Materials",type=properties.Category_Material)

    @classmethod
    def poll(cls, context):
        if bpy.data.filepath != "" and context.object:
            return True
        else:
            return False

    def execute(self, context):
        filepath = bpy.data.filepath
        path = fd.get_file_browser_path(context)
        for mat in self.materials:
            if mat.selected:
                
                blend_path = os.path.join(path,mat.name + ".blend")
                thumbnail_path = os.path.join(path,mat.name + ".png")
                import subprocess
                
                script = material_utils.save_material_script(filepath, mat.name, blend_path)
                subprocess.call(bpy.app.binary_path + ' -b --python "' + script + '"')
                
                if self.create_thumbnail:
                    script = material_utils.create_thumbnail_script(blend_path, mat.name, thumbnail_path)
                    subprocess.call(bpy.app.binary_path + ' "' + material_utils.get_thumbnail_path() + '" -b --python "' + script + '"')
        return {'FINISHED'}
        
    def invoke(self,context,event):
        obj = context.object
        for slot in obj.material_slots:
            if slot.material:
                mat = self.materials.add()
                mat.name = slot.material.name
                mat.selected = True
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=380)
        
    def draw(self, context):
        layout = self.layout
        path = fd.get_file_browser_path(context)
        foldername = os.path.basename(os.path.normpath(path))
        if len(self.materials) == 0:
            layout.label("This object has no materials?",icon='ERROR')
        else:
            if len(self.materials) == 1:
                layout.label("Are you sure you want to save this material to this category?",icon='QUESTION')
                layout.label("Material: " + self.materials[0].name,icon='MATERIAL')
                layout.label("Category: " + foldername,icon='FILE_FOLDER')
                layout.prop(self,'create_thumbnail')
            else:
                layout.label("Select the materials you want to save this material to this category?",icon='QUESTION')
                for mat in self.materials:
                    row = layout.row()
                    row.label("Material: " + mat.name,icon='MATERIAL')
                    row.prop(mat,"selected",text="")
                layout.label("Category: " + foldername,icon='FILE_FOLDER')
                layout.prop(self,'create_thumbnail')
            
class OPS_Create_Thumbnails(Operator):
    bl_idname = "materiallib.create_thumbnails"
    bl_label = "Render Material"
    bl_description = "This will render thumbnails of all of the items in the material list."
    
    @classmethod
    def poll(cls, context):
        if fd.get_file_browser_path(context):
            wm = context.window_manager.materiallib
            for mat in wm.materials_in_category:
                if mat.selected:
                    return True
        else:
            return False
        return False
    
    def execute(self,context):
        import subprocess
        wm = context.window_manager.materiallib
        category_path = fd.get_file_browser_path(context)
        for mat in wm.materials_in_category:
            if mat.selected:
                script = material_utils.create_thumbnail_script(mat.filepath, mat.name, os.path.join(category_path,mat.name))
                subprocess.call(bpy.app.binary_path + ' "' + material_utils.get_thumbnail_path() + '" -b --python "' + script + '"')
        return{'FINISHED'}
        
class OPS_Load_Materials_From_Category(Operator):   
    bl_idname = "materiallib.load_materials_from_category"
    bl_label = "Load Materials From Category"
    bl_description = "This will load all of the materials in the active category into a list"
    
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
        wm = context.window_manager.materiallib
        path = fd.get_file_browser_path(context)
        files = os.listdir(path)
        for obj in wm.materials_in_category:
            wm.materials_in_category.remove(0)
            
        for file in files:
            filename, ext = os.path.splitext(file)
            if ext == '.blend':
                filepath = os.path.join(path,file)
                if os.path.isfile(filepath):
                    with bpy.data.libraries.load(filepath, False, False) as (data_from, data_to):
                        
                        for index, material in enumerate(data_from.materials):
                            obj = wm.materials_in_category.add()
                            obj.name = material
                            obj.filename = filename
                            obj.filepath = filepath
                            obj.has_thumbnail = self.found_thumbnail(files, obj.name)

        return{'FINISHED'}
        
class OPS_Append_Materials_From_Category(Operator):   
    bl_idname = "materiallib.append_materials_from_category"
    bl_label = "Append Materials From Category"
    bl_options = {'UNDO'}
    bl_description = "This will append all of the selected materials in the object list into the scene"
    
    @classmethod
    def poll(cls, context):
        wm = context.window_manager.materiallib
        if len(wm.materials_in_category) > 0:
            return True
        else:
            return False

    def execute(self,context):
        wm = context.window_manager.materiallib
        scene = context.scene
        mats = []
        
        for mat in wm.materials_in_category:
            if mat.selected:
                with bpy.data.libraries.load(mat.filepath, False, False) as (data_from, data_to):
                    data_to.materials = [mat.name]

                for mat2 in data_to.materials:
                    mats.append(mat2)

        for index, mat in enumerate(mats):
            item = context.scene.materiallib.scene_materials.add()
            item.name = mat.name
            bpy.ops.mesh.primitive_cube_add()
            obj = context.scene.objects.active
            bpy.ops.fd_object.unwrap_mesh(object_name=obj.name)
            bpy.ops.fd_object.add_material_slot(object_name=obj.name)
            for slot in obj.material_slots:
                slot.material = mat

            obj.location = scene.cursor_location
            obj.location.x = fd.inches(30) * index

        return{'FINISHED'}
        
#------REGISTER
classes = [
           OPS_open,
           OPS_drop,
           OPS_change_directory,
           OPS_delete,
           OPS_assign_material,
           OPS_assign_material_to_slot,
           OPS_Select_All_Materials_In_List,
           OPS_Add_Material_To_List,
           OPS_Save_Selected_Material_to_Category,
           OPS_Create_Thumbnails,
           OPS_Load_Materials_From_Category,
           OPS_Append_Materials_From_Category
           ]

def register():
    for c in classes:
        bpy.utils.register_class(c)

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)

if __name__ == "__main__":
    register()
