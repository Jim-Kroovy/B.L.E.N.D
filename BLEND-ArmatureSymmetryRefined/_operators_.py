import bpy

from . import _functions_

from bpy.props import (BoolProperty, BoolVectorProperty, StringProperty, EnumProperty)

class JK_OT_ASR_Set_Armature_Symmetry(bpy.types.Operator):
    """Mirror the armatures bones across the chosen axes based on bone name similarities"""
    bl_idname = "jk.set_armature_symmetry"
    bl_label = "Better Symmetrize"
    bl_options = {'REGISTER', 'UNDO'}
    
    head: BoolProperty(name="Heads", description="Symmetrize the heads of bones across the given axis", default=True)

    tail: BoolProperty(name="Tails", description="Symmetrize the tails of bones across the given axis", default=True)

    roll: BoolProperty(name="Rolls", description="Symmetrize the rolls of bones across the given axis", default=True)

    parent: BoolProperty(name="Parents", description="Symmetrize the parenting of bones across the given axis", default=True)
    
    mode: EnumProperty(name="Method", description="Do you want to mirror bone properties based on prefix, affix or suffix?",
        items=[('PREFIX', "Prefix", "Look for similar bone names that start with the same string"),
        ('AFFIX', "Affix", "Look for similar bone names that contain the same string"),
        ('SUFFIX', "Suffix", "Look for similar bone names that end with the same string")],
        default='SUFFIX')
    
    from_suffix: StringProperty(name="From Suffix", description="Suffix of the source bones (case sensitive)", default="L")

    to_suffix: StringProperty(name="To Suffix", description="Suffix of the target bones (case sensitive)", default="R")

    
    from_affix: StringProperty(name="From Affix", description="Affix of the source bones (case sensitive)", default="Left")

    to_affix: StringProperty(name="To Affix", description="Affix of the target bones (case sensitive)", default="Right")

    
    from_prefix: StringProperty(name="From Prefix", description="Prefix of the source bones (case sensitive)", default="Left")

    to_prefix: StringProperty(name="To Prefix", description="Prefix of the target bones (case sensitive)", default="Right")

    axes: BoolVectorProperty(name="Axes Of Symmetry", description="The axes to symmetrize the bones over", default=(True, False, False))

    create: BoolProperty(name="Create Bones", description="Create symmetrical bones if they don't already exist", default=True)

    selected: BoolProperty(name="Only Selected", description="Only symmetrize selected bones", default=True)

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
        row.prop(self, "head", toggle=True)
        row.prop(self, "tail", toggle=True)
        row.prop(self, "roll", toggle=True)
        row.prop(self, "parent", toggle=True)
        row = layout.row()
        row.prop(self, "from_suffix")
        row = layout.row()
        row.prop(self, "to_suffix")
        row = layout.row(align=True)
        row.label(text="Axes:")
        row.prop(self, "axes", text="X", toggle=True, index=0)
        row.prop(self, "axes", text="Y", toggle=True, index=1)
        row.prop(self, "axes", text="Z", toggle=True, index=2)
        row.enabled = True if self.head or self.tail else False
        row = layout.row()
        row.prop(self, "selected")
        row.prop(self, "create")

        