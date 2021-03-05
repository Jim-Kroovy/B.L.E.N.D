import bpy
from bpy.props import (EnumProperty, BoolProperty, StringProperty, CollectionProperty, FloatProperty, IntProperty, PointerProperty)
from . import _functions_

class JK_PG_ACB_Mesh(bpy.types.PropertyGroup):

    armature: StringProperty(name="Armature", description="The first armature this mesh is weighted to")
    
class JK_PG_ACB_Armature(bpy.types.PropertyGroup):
    
    use_auto_update: BoolProperty(name="Auto Update", description="Automatically update any changes made to control/deform bones when leaving edit mode",
        default=False, options=set())

    auto_hide: BoolProperty(name="Auto Hide", description="Automatically hide/show deform bones depending on mode. (Shows only controls in pose mode and only deform bones in edit/weight mode",
        default=False, options=set())

    def update_use_deforms(self, context):
        controller, deformer = _functions_.get_armatures()
        _functions_.use_deforms(controller, deformer, self.use_deforms)

    use_deforms: BoolProperty(name="Use Deform Bones", description="Use deform/control bones to deform the mesh",
        default=False, options=set(), update=update_use_deforms)

    def update_use_combined(self, context):
        controller, deformer = _functions_.get_armatures()
        _functions_.set_combined(controller, deformer, self.use_combined)

    use_combined: BoolProperty(name="Combine Armatures", description="Deformation bones are combined into the control armature",
        default=False, options=set(), update=update_use_combined)

    def update_hide_deforms(self, context):
        controller, deformer = _functions_.get_armatures()
        _functions_.hide_deforms(controller, deformer, self.hide_deforms)

    hide_deforms: BoolProperty(name="Hide Deforms", description="Hide/Show deform bones",
        default=False, options=set(), update=update_hide_deforms)

    def update_hide_controls(self, context):
        controller, _ = _functions_.get_armatures()
        _functions_.hide_controls(controller, self.hide_controls)

    hide_controls: BoolProperty(name="Hide Controls", description="Hide/Show control bones",
        default=False, options=set(), update=update_hide_controls)

    def update_hide_others(self, context):
        controller, _ = _functions_.get_armatures()
        _functions_.hide_others(controller, self.hide_others)

    hide_others: BoolProperty(name="Hide Others", description="Hide/Show bones that are not control or deform bones",
        default=False, options=set(), update=update_hide_others)

    is_deformer:  BoolProperty(name="Is Deform Armature", description="Is this a deformation armature",
        default=False, options=set())

    is_controller:  BoolProperty(name="Is Control Armature", description="Is this an animation control armature",
        default=False, options=set())

    armature: PointerProperty(type=bpy.types.Object)

    deforms: StringProperty(name="Deform Bones", description="The .json list that stores the deform bones")

    #meshes: CollectionProperty(type=JK_PG_ACB_Mesh)