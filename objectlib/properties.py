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

from bpy.types import AddonPreferences, PropertyGroup
from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       BoolVectorProperty,
                       PointerProperty,
                       CollectionProperty,
                       EnumProperty)

def update_active_obj_index(self,context):
    obj_name = self.scene_objects[self.active_object_index].name
    obj = bpy.data.objects[obj_name]
    bpy.ops.object.select_all(action='DESELECT')
    context.scene.objects.active = obj
    obj.select = True

class Category(PropertyGroup):
    path = StringProperty(name="Path")

bpy.utils.register_class(Category)

class Category_Object(PropertyGroup):
    name = StringProperty(name='Name')
    selected = BoolProperty(name="Selected")
    has_thumbnail = BoolProperty(name="Has Thumbnail")
    filename = StringProperty(name='Filename')
    filepath = StringProperty(name="Filepath")
    
bpy.utils.register_class(Category_Object)

class Library(PropertyGroup):
    path = StringProperty(name="Path")
    
    categories = CollectionProperty(name="Categories",
                                    type=Category)
    
    active_category_name = StringProperty(name="Active Category Name")
    
    def get_categories(self):
        for _ in self.categories:
            self.categories.remove(0)
        
        categories = os.listdir(self.path)
        for category in categories:
            category_path = os.path.join(self.path,category)
            if os.path.isdir(category_path):
                lib_category = self.categories.add()
                lib_category.name = category
                lib_category.path = category_path
                
        if len(self.categories) > 0:
            self.active_category_name = self.categories[0].name
    
    def get_active_category(self):
        return self.categories[self.active_category_name]        

bpy.utils.register_class(Library)

class OBJECT_PROPERTIES(PropertyGroup):
    library_name = StringProperty(name="Library Name")
    
    category_name = StringProperty(name="Category Name")
    
    object_name = StringProperty(name="Object Name")
    
class SCENE_PROPERTIES(PropertyGroup):
    link_or_append = EnumProperty(name="Link or Append",
                                  items=[('LINK',"Link","Link Data - You cannot edit linked data"),
                                         ('APPEND',"Append","Append Data - You can edit appended data")],
                                  default = 'APPEND')

    libraries = CollectionProperty(name="Library",
                                   type=Library)
    
    active_library_name = StringProperty(name="Active Library Name")

    categories = CollectionProperty(name="Categories",
                                    type=Category)
    
    active_category_name = StringProperty(name="Active Category Name")
        
    scene_objects = CollectionProperty(name="Scene Objects",
                                       type=Category_Object)
    
    active_object_index = IntProperty(name="Active Object Index",
                                      default=0,
                                      update=update_active_obj_index)    
    
class WM_PROPERTIES(PropertyGroup):
    objects_in_category = CollectionProperty(name="Objects in Category",
                                             type=Category_Object)
    
    objects_in_category_index = IntProperty(name="Objects in Category Index",
                                            default=0)
    
bpy.utils.register_class(OBJECT_PROPERTIES)
bpy.utils.register_class(SCENE_PROPERTIES)
bpy.utils.register_class(WM_PROPERTIES)

def register():
    bpy.types.Object.objectlib = PointerProperty(type = OBJECT_PROPERTIES)
    bpy.types.Scene.objectlib = PointerProperty(type = SCENE_PROPERTIES)
    bpy.types.WindowManager.objectlib = PointerProperty(type = WM_PROPERTIES)
    
def unregister():
    pass
