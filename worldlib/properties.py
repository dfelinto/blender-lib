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

def update_active_scene_index(self,context):
    if self.active_world_index + 1 <= len(bpy.data.worlds):
        world = bpy.data.worlds[self.active_world_index]
        context.scene.world = world

class Category(PropertyGroup):
    path = StringProperty(name="Path")

bpy.utils.register_class(Category)

class Category_World(PropertyGroup):
    name = StringProperty(name='Name')
    selected = BoolProperty(name="Selected")
    has_thumbnail = BoolProperty(name="Has Thumbnail")
    filename = StringProperty(name='Filename')
    filepath = StringProperty(name="Filepath")
    
bpy.utils.register_class(Category_World)

class WORLD_PROPERTIES(PropertyGroup):
    category_name = StringProperty(name="Category Name")
    
    material_name = StringProperty(name="Material Name")
    
class SCENE_PROPERTIES(PropertyGroup):
    categories = CollectionProperty(name="Categories",
                                    type=Category)
    
    active_category_name = StringProperty(name="Active Category Name")
    
    link_or_append = EnumProperty(name="Link or Append",
                                  items=[('LINK',"Link","Link Data - You cannot edit linked data"),
                                         ('APPEND',"Append","Append Data - You can edit appended data")],
                                  default = 'APPEND')

    active_world_index = IntProperty(name="Active Object Index",
                                      default=0,
                                      update=update_active_scene_index)   

class WM_PROPERTIES(PropertyGroup):
    path_to_world_image = StringProperty(name="Path To World Image",subtype='FILE_PATH')

    worlds_in_category = CollectionProperty(name="Worlds in Category",
                                            type=Category_World)
    
    worlds_in_category_index = IntProperty(name="Worlds in Category Index",
                                           default=0)
    
bpy.utils.register_class(WORLD_PROPERTIES)
bpy.utils.register_class(SCENE_PROPERTIES)
bpy.utils.register_class(WM_PROPERTIES)

def register():
    bpy.types.World.worldlib = PointerProperty(type = WORLD_PROPERTIES)
    bpy.types.Scene.worldlib = PointerProperty(type = SCENE_PROPERTIES)
    bpy.types.WindowManager.worldlib = PointerProperty(type = WM_PROPERTIES)
    
def unregister():
    pass
