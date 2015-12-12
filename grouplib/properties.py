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

from bpy.types import Header, Menu, Panel, PropertyGroup, AddonPreferences
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

class Category(PropertyGroup):
    path = StringProperty(name="Path")

bpy.utils.register_class(Category)

class Category_Group(PropertyGroup):
    name = StringProperty(name='Name')
    selected = BoolProperty(name="Selected")
    has_thumbnail = BoolProperty(name="Has Thumbnail")
    filename = StringProperty(name='Filename')
    filepath = StringProperty(name="Filepath")
    
bpy.utils.register_class(Category_Group)

class GROUP_PROPERTIES(PropertyGroup):
    category_name = StringProperty(name="Category Name")

class SCENE_PROPERTIES(PropertyGroup):
    link_or_append = EnumProperty(name="Link or Append",
                                  items=[('LINK',"Link","Link Data - You cannot edit linked data"),
                                         ('APPEND',"Append","Append Data - You can edit appended data")],
                                  default = 'APPEND')
    
    categories = CollectionProperty(name="Categories",
                                    type=Category)
    
    scene_groups = CollectionProperty(name="Scene Groups",
                                      type=Category_Group)
    
    active_group_index = IntProperty(name="Active Group Index",
                                     default=0)
    
    active_category_name = StringProperty(name="Active Category Name")
    
class WM_PROPERTIES(PropertyGroup):
    groups_in_category = CollectionProperty(name="Groups in Category",
                                            type=Category_Group)
    
    groups_in_category_index = IntProperty(name="Groups in Category Index",
                                           default=0)
    
bpy.utils.register_class(GROUP_PROPERTIES)
bpy.utils.register_class(SCENE_PROPERTIES)
bpy.utils.register_class(WM_PROPERTIES)

def register():
    bpy.types.Group.grouplib = PointerProperty(type = GROUP_PROPERTIES)
    bpy.types.Scene.grouplib = PointerProperty(type = SCENE_PROPERTIES)
    bpy.types.WindowManager.grouplib = PointerProperty(type = WM_PROPERTIES)

def unregister():
    pass
