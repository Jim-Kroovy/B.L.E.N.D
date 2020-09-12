import bpy

from . import _functions_

from bpy.props import (BoolProperty, BoolVectorProperty, StringProperty)

class JK_OT_Set_Armature_Symmetry(bpy.types.Operator):
    """Mirror the armatures bones across the chosen axes based on bone name suffixes"""
    bl_idname = "jk.set_armature_symmetry"
    bl_label = "Better Symmetrize"
    
    Head: BoolProperty(name="Heads", description="Symmetrize the heads of bones across the given axis", default=True)

    Tail: BoolProperty(name="Tails", description="Symmetrize the tails of bones across the given axis", default=True)

    Roll: BoolProperty(name="Rolls", description="Symmetrize the rolls of bones across the given axis", default=True)

    Parent: BoolProperty(name="Parents", description="Symmetrize the parenting of bones across the given axis", default=True)
    
    From_suffix: StringProperty(name="From Suffix", description="Suffix of the source bones (case sensitive)", default="L")

    To_suffix: StringProperty(name="To Suffix", description="Suffix of the target bones (case sensitive)", default="R")

    Axes: BoolVectorProperty(name="Axes Of Symmetry", description="The axes to symmetrize the bones over", default=(True, False, False))

    Create: BoolProperty(name="Create Bones", description="Create symmetrical bones if they don't already exist", default=True)

    Selected: BoolProperty(name="Only Selected", description="Only symmetrize selected bones", default=True)

    # Case: BoolProperty(name="Case Sensitive", description="From and to suffices are case sensitve", default=False)
    
    def execute(self, context):
        armature = bpy.context.object
        _functions_.Set_Bone_Symmetry(self, armature)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.prop(self, "Head", toggle=True)
        row.prop(self, "Tail", toggle=True)
        row.prop(self, "Roll", toggle=True)
        row.prop(self, "Parent", toggle=True)
        row = layout.row()
        row.prop(self, "From_suffix")
        row = layout.row()
        row.prop(self, "To_suffix")
        row = layout.row(align=True)
        row.label(text="Axes:")
        row.prop(self, "Axes", text="X", toggle=True, index=0)
        row.prop(self, "Axes", text="Y", toggle=True, index=1)
        row.prop(self, "Axes", text="Z", toggle=True, index=2)
        row.enabled = True if self.Head or self.Tail else False
        row = layout.row()
        row.prop(self, "Selected")
        row.prop(self, "Create")

        