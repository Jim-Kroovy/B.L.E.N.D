import bpy

from . import _functions_

from bpy.props import (BoolProperty, BoolVectorProperty, StringProperty, EnumProperty)

class JK_OT_ASR_Set_Edit_Bone_Symmetry(bpy.types.Operator):
    """Mirror the armatures edit bones across the chosen axes based on bone name similarities"""
    bl_idname = "jk.asr_set_edit_bone_symmetry"
    bl_label = "Refined Symmetry"
    bl_options = {'REGISTER', 'UNDO'}

    use_head: BoolProperty(name="Heads", description="Symmetrize the heads of bones across the given axis", default=True)

    use_tail: BoolProperty(name="Tails", description="Symmetrize the tails of bones across the given axis", default=True)

    use_roll: BoolProperty(name="Rolls", description="Symmetrize the rolls of bones across the given axis", default=True)

    use_parent: BoolProperty(name="Parents", description="Symmetrize the parenting of bones across the given axis", default=True)
    
    from_string: StringProperty(name="From Affix", description="Affix of the source bones (case sensitive, can be prefix, affix or suffix)", default="L")

    to_string: StringProperty(name="To Affix", description="Affix of the target bones (case sensitive, can be prefix, affix or suffix)", default="R")

    only_selected: BoolProperty(name="Only Selected", description="Only symmetrize selected bones", default=True)

    axes: BoolVectorProperty(name="Axes Of Symmetry", description="The axes to symmetrize the bones over", default=(True, False, False))

    create: BoolProperty(name="Create Bones", description="Create symmetrical bones if they don't already exist", default=True)

    def execute(self, context):
        armature = bpy.context.object
        _functions_.set_edit_bone_symmetry(self, armature)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.prop(self, "use_head", toggle=True)
        row.prop(self, "use_tail", toggle=True)
        row.prop(self, "use_roll", toggle=True)
        row.prop(self, "use_parent", toggle=True)
        row = layout.row()
        row.prop(self, "from_string")
        row = layout.row()
        row.prop(self, "to_string")
        row = layout.row(align=True)
        row.label(text="Axes:")
        row.prop(self, "axes", text="X", toggle=True, index=0)
        row.prop(self, "axes", text="Y", toggle=True, index=1)
        row.prop(self, "axes", text="Z", toggle=True, index=2)
        row.enabled = True if self.use_head or self.use_tail else False
        row = layout.row()
        row.prop(self, "only_selected")
        row.prop(self, "create")

class JK_OT_ASR_Set_Pose_Bone_Symmetry(bpy.types.Operator):
    """Mirror the armatures pose bones across the chosen axes based on bone name similarities"""
    bl_idname = "jk.asr_set_pose_bone_symmetry"
    bl_label = "Refined Symmetry"
    bl_options = {'REGISTER', 'UNDO'}

    use_location: BoolProperty(name="Locations", description="Symmetrize the locations of bones across the given axis", default=True)

    use_rotation: BoolProperty(name="Rotations", description="Symmetrize the rotations of bones across the given axis", default=True)

    use_scale: BoolProperty(name="Scales", description="Symmetrize the scales of bones across the given axis", default=True)

    use_constraints: BoolProperty(name="Constraints", description="Symmetrize the constraints of bones across the given axis (if any)", default=False)

    from_string: StringProperty(name="From Affix", description="Affix of the source bones (case sensitive, can be prefix, affix or suffix)", default="L")

    to_string: StringProperty(name="To Affix", description="Affix of the target bones (case sensitive, can be prefix, affix or suffix)", default="R")

    only_selected: BoolProperty(name="Only Selected", description="Only symmetrize selected bones", default=True)

    axes: BoolVectorProperty(name="Axes Of Symmetry", description="The axes to symmetrize the bones over", default=(True, False, False))

    use_mode: BoolProperty(name="Rotation Mode", description="Symmetrize the rotation mode of bones across the given axis", default=False)

    use_mirror: BoolProperty(name="Two Way Mirror", description="Mirror symmetrical bones back on to the bones their transforms came from (like the default pose mirror operator)", default=False)

    def execute(self, context):
        armature = bpy.context.object
        _functions_.set_pose_bone_symmetry(self, armature)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.prop(self, "use_location", toggle=True)
        row.prop(self, "use_rotation", toggle=True)
        row.prop(self, "use_scale", toggle=True)
        row.prop(self, "use_constraints", toggle=True)
        row = layout.row()
        row.prop(self, "from_string")
        row = layout.row()
        row.prop(self, "to_string")
        row = layout.row(align=True)
        row.label(text="Axes:")
        row.prop(self, "axes", text="X", toggle=True, index=0)
        row.prop(self, "axes", text="Y", toggle=True, index=1)
        row.prop(self, "axes", text="Z", toggle=True, index=2)
        row = layout.row()
        row.prop(self, "only_selected")
        row.prop(self, "use_mode")
        row.prop(self, "use_mirror")

class JK_OT_ASR_Set_Action_Symmetry(bpy.types.Operator):
    """Mirror the current action of the armature across the chosen axes based on bone name similarities"""
    bl_idname = "jk.asr_set_action_symmetry"
    bl_label = "Refined Symmetry"
    bl_options = {'REGISTER', 'UNDO'}

    use_location: BoolProperty(name="Locations", description="Symmetrize the locations of bones across the given axis", default=True)

    use_rotation: BoolProperty(name="Rotations", description="Symmetrize the rotations of bones across the given axis", default=True)

    use_scale: BoolProperty(name="Scales", description="Symmetrize the scales of bones across the given axis", default=True)

    # use_constraints: BoolProperty(name="Constraints", description="Symmetrize the constraints of bones across the given axis (if any)", default=False)

    from_string: StringProperty(name="From Affix", description="Affix of the source bones (case sensitive, can be prefix, affix or suffix)", default="L")

    to_string: StringProperty(name="To Affix", description="Affix of the target bones (case sensitive, can be prefix, affix or suffix)", default="R")

    only_selected: BoolProperty(name="Only Selected", description="Only symmetrize selected bones", default=True)

    axes: BoolVectorProperty(name="Axes Of Symmetry", description="The axes to symmetrize the bones over", default=(True, False, False))

    # use_mode: BoolProperty(name="Rotation Mode", description="Symmetrize the rotation mode of bones across the given axis", default=False)

    use_mirror: BoolProperty(name="Two Way Mirror", description="Mirror symmetrical bones back on to the bones their transforms came from (like the default pose mirror operator)", default=False)

    def execute(self, context):
        armature = bpy.context.object
        _functions_.set_pose_bone_symmetry(self, armature)
        pbs, bbs = armature.pose.bones, armature.data.bones
        action = armature.animation_data.action
        curves = _functions_.get_curve_properties(action, pbs)
        _functions_.set_symmetrical_curves(self, armature, action, curves)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.prop(self, "use_location", toggle=True)
        row.prop(self, "use_rotation", toggle=True)
        row.prop(self, "use_scale", toggle=True)
        row.prop(self, "use_constraints", toggle=True)
        row = layout.row()
        row.prop(self, "from_string")
        row = layout.row()
        row.prop(self, "to_string")
        row = layout.row(align=True)
        row.label(text="Axes:")
        row.prop(self, "axes", text="X", toggle=True, index=0)
        row.prop(self, "axes", text="Y", toggle=True, index=1)
        row.prop(self, "axes", text="Z", toggle=True, index=2)
        row = layout.row()
        row.prop(self, "only_selected")
        row.prop(self, "use_mode")
        row.prop(self, "use_mirror")