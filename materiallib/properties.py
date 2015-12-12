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

from bpy.types import PropertyGroup
from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       BoolVectorProperty,
                       PointerProperty,
                       CollectionProperty,
                       EnumProperty)

class Category(PropertyGroup):
    path = StringProperty(name="Path")

bpy.utils.register_class(Category)

class Category_Material(PropertyGroup):
    name = StringProperty(name='Name')
    selected = BoolProperty(name="Selected")
    has_thumbnail = BoolProperty(name="Has Thumbnail")
    filename = StringProperty(name='Filename')
    filepath = StringProperty(name="Filepath")
    
bpy.utils.register_class(Category_Material)

class Material_Slot(PropertyGroup):
    category_name = StringProperty(name="Category Name")
    material_name = StringProperty(name="Material Name")

bpy.utils.register_class(Material_Slot)

class MATERIAL_PROPERTIES(PropertyGroup):
    category_name = StringProperty(name="Category Name")
    
    material_name = StringProperty(name="Material Name")
    
class OBJECT_PROPERTIES(PropertyGroup):
    material_slots = CollectionProperty(name="Material Slots",
                                        type=Material_Slot)
    
    category_name = StringProperty(name="Category Name")
    
    object_name = StringProperty(name="Object Name")

class SCENE_PROPERTIES(PropertyGroup):
    categories = CollectionProperty(name="Categories",
                                    type=Category)
    
    active_category_name = StringProperty(name="Active Category Name")
    
    scene_materials = CollectionProperty(name="Scene Materials",
                                         type=Category_Material)
    
    active_material_index = IntProperty(name="Active Material Index",
                                        default=0)    
    
    link_or_append = EnumProperty(name="Link or Append",
                                  items=[('LINK',"Link","Link Data - You cannot edit linked data"),
                                         ('APPEND',"Append","Append Data - You can edit appended data")],
                                  default = 'APPEND')

    placement_spacing = FloatProperty(name="Placement Spacing",
                                      unit='LENGTH',
                                      default=fd.inches(10))

class WM_PROPERTIES(PropertyGroup):
    materials_in_category = CollectionProperty(name="Materials in Category",
                                               type=Category_Material)
    
    materials_in_category_index = IntProperty(name="Materials in Category Index",
                                              default=0)
    
bpy.utils.register_class(MATERIAL_PROPERTIES)
bpy.utils.register_class(OBJECT_PROPERTIES)
bpy.utils.register_class(SCENE_PROPERTIES)
bpy.utils.register_class(WM_PROPERTIES)

def register():
    bpy.types.Material.materiallib = PointerProperty(type = MATERIAL_PROPERTIES)
    bpy.types.Object.materiallib = PointerProperty(type = OBJECT_PROPERTIES)
    bpy.types.Scene.materiallib = PointerProperty(type = SCENE_PROPERTIES)
    bpy.types.WindowManager.materiallib = PointerProperty(type = WM_PROPERTIES)

def unregister():
    pass
