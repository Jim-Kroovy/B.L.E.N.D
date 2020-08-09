import bpy

from bpy.props import (PointerProperty, CollectionProperty, IntProperty, EnumProperty, StringProperty, BoolProperty, FloatProperty)

from . import _properties_, _functions_

class JK_OT_Add_Twist(bpy.types.Operator):
    """Adds a twist bone rigging to the active bone"""
    bl_idname = "jk.twist_action"
    bl_label = "Add Twist Bone"

    def Update_Twist_Operator(self, context):
        armature = bpy.context.object
        if armature.mode == 'POSE':
            bpy.ops.pose.select_all(action='DESELECT')
            bone = armature.data.bones[self.Source]
            armature.data.bones.active = bone
            bone.select = True
        elif armature.mode == 'EDIT':
            bpy.ops.armature.select_all(action='DESELECT')
            bone = armature.data.edit_bones[self.Source]
            armature.data.edit_bones.active = bone
            bone.select = True
        if self.Type == 'HEAD_HOLD':
            if bone.parent:
                self.Target = bone.parent.name
            self.Float = 1.0
        if self.Type == 'TAIL_FOLLOW':
            if bone.parent:
                for child in bone.parent.children:
                    if child.name != bone.name:
                        self.Target = child.name
                        break
            self.Float = 0.5

    Source: StringProperty(name="Source", description="The targets bones name", default="", maxlen=1024, update=Update_Twist_Operator)

    Type: EnumProperty(name="Type", description="The type of twist bone to add",
        items=[('HEAD_HOLD', 'Head Hold', "Holds deformation at the head of the bone back by tracking to the target. (eg: Upper Arm Twist)"),
        ('TAIL_FOLLOW', 'Tail Follow', "Follows deformation at the tail of the bone by copying the Y rotation of the target. (eg: Lower Arm Twist)")],
        default='HEAD_HOLD', update=Update_Twist_Operator)

    Float: FloatProperty(name="Float", description="Either the head vs tail or influence depending on the twist type", 
        default=1.0, min=0.0, max=1.0, subtype='FACTOR')
    
    Target: StringProperty(name="Target", description="The targets bones name", default="", maxlen=1024)
    
    Has_pivot: BoolProperty(name="Use Pivot", description="Does this twist bone have a pivot bone to define its limits?", default=False)
    
    Use_a: BoolProperty(name="Use", description="Use this limit", default=False)
    Min_a: FloatProperty(name="Min", description="Minimum limit", default=0.0, subtype='ANGLE', unit='ROTATION')
    Max_a: FloatProperty(name="Max", description="Maximum limit", default=0.0, subtype='ANGLE', unit='ROTATION')

    Use_b: BoolProperty(name="Use", description="Use this limit", default=False)
    Min_b: FloatProperty(name="Min", description="Minimum limit", default=0.0, subtype='ANGLE', unit='ROTATION')
    Max_b: FloatProperty(name="Max", description="Maximum limit", default=0.0, subtype='ANGLE', unit='ROTATION')

    Action: EnumProperty(name="Action", description="",
        items=[('ADD', 'Add', ""), ('REMOVE', 'Remove', "")],
        default='ADD')

    def execute(self, context):
        armature = bpy.context.object
        _functions_.Set_Twist(self, armature)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        bone = bpy.context.active_bone
        self.Source = bone.name
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        armature = bpy.context.object
        layout = self.layout
        row = layout.row()
        row.prop(self, "Type")
        row.prop_search(self, "Source", armature.pose, "bones")
        box = layout.box()
        row = box.row()
        row.prop_search(self, "Target", armature.pose, "bones")
        row.prop(self, "Has_pivot")
        if self.Type == 'HEAD_HOLD':
            row = box.row()
            row.prop(self, "Use_a")
            row.prop(self, "Min_a")
            row.prop(self, "Max_a")
            row = box.row()
            row.prop(self, "Use_b")
            row.prop(self, "Min_b")
            row.prop(self, "Max_b")
            row = box.row()
            row.prop(self, "Float", text="Head Vs Tail")
        elif self.Type == 'TAIL_FOLLOW':
            row = box.row()
            row.prop(self, "Use_a")
            row.prop(self, "Min_a")
            row.prop(self, "Max_a")
            row = box.row()
            row.prop(self, "Float", text="Influence")

class JK_OT_Add_Chain(bpy.types.Operator):
    """Adds a chain from the active bone that is articulated with constraints"""
    bl_idname = "jk.chain_action"
    bl_label = "Add Chain Rigging"
    bl_options = {'REGISTER', 'UNDO'}
    
    def Update_Chain_Operator(self, context):
        armature = bpy.context.object
        if armature.mode == 'POSE':
            bpy.ops.pose.select_all(action='DESELECT')
            bone = armature.data.bones[self.Owner]
            armature.data.bones.active = bone
            bone.select = True
        elif armature.mode == 'EDIT':
            bpy.ops.armature.select_all(action='DESELECT')
            bone = armature.data.edit_bones[self.Owner]
            armature.data.edit_bones.active = bone
            bone.select = True
        #bone = bpy.context.active_bone
        self.Targets.clear()
        self.Bones.clear()
        self.Limb = _functions_.Get_Bone_Limb(bone.name)
        self.Side = _functions_.Get_Bone_Side(bone.name)
        if self.Type in ['OPPOSABLE', 'PLANTIGRADE', 'DIGITIGRADE']:
            if self.Type in ['PLANTIGRADE', 'DIGITIGRADE']:
                self.Limb = 'LEG'
            cb = self.Bones.add()
            cb.name = bone.name
            cb = self.Bones.add()
            if bone.parent != None:
                cb.name = bone.parent.name
            if self.Type == 'DIGITIGRADE':
                cb = self.Bones.add()
                if bone.parent != None and bone.parent.parent != None:
                    cb.name = bone.parent.parent.name
            else:
                if bone.parent != None:
                    self.Pole.Source = bone.parent.name
                    self.Pole.Angle = _functions_.Get_Pole_Angle(self.Pole.Axis)
            if len(bone.children) > 0:
                tb = self.Targets.add()
                tb.Source = bone.children[0].name
                if self.Type == 'DIGITIGRADE':
                    tb.Pivot = bone.name
                child = bone.children[0]
            else:
                tb = self.Targets.add()
                child = None
            if self.Type == 'PLANTIGRADE':
                if child != None:
                    if len(child.children) > 0:
                        tb.Pivot = child.children.children[0].name
        elif self.Type in ['SPLINE', 'FORWARD', 'SCALAR']:
            parent = bone
            bpy.ops.pose.select_all(action='DESELECT')
            for i in range(0, self.Length):
                if parent:
                    parent.select = True
                    cb = self.Bones.add()
                    cb.name = parent.name
                    if self.Type == 'SPLINE':
                        cb.Has_target = True
                    elif self.Type == 'FORWARD':
                        fb = self.Forward.add()
                        fb.name = cb.name
                        cb.Has_target = True if i == self.Length - 1 else False
                    parent = parent.parent

    Action: EnumProperty(name="Action", description="",
        items=[('ADD', 'Add', ""), ('REMOVE', 'Remove', "")],
        default='ADD')
    
    Owner: StringProperty(name="Owner", description="The owning bone of the chains name", default="", maxlen=1024, update=Update_Chain_Operator)
    
    Type: EnumProperty(name="Type", description="The type of limb IK chain",
        items=[('OPPOSABLE', 'Opposable', "A simple IK chain of 2 bones with a pole target. (Generally used by arms)"),
        ('SCALAR', 'Scalar', "An IK chain of any length controlled by scaling, rotating a parent of the target. (Generally used for fingers)"),
        ('PLANTIGRADE', 'Plantigrade', "An IK chain of 2 bones with a pole target and standard foot rolling controls. (Generally used by human legs)"),
        ('DIGITIGRADE', 'Digitigrade', "An IK chain of 2 bones with a pole target and special foot controls. (Generally used by animal legs)"),
        ('SPLINE', 'Spline', "A spline IK chain of any length controlled by a curve that's manipulated with target bones. (Generally used by tails/spines)"),
        ('FORWARD', 'Forward', "An FK chain of any length where the chain copies loc/rot/scale of a parent/target. (Generally an alternative used for fingers/tails)")],
        default='OPPOSABLE', update=Update_Chain_Operator)

    Length: IntProperty(name="Chain Length", description="How far through its parents should this IK chain run",
        default=2, min=1, update=Update_Chain_Operator)
    
    Side: EnumProperty(name="Side", description="Which side of the armature is this chain on",
        items=[('NONE', 'None', "Not on any side, probably central"),
            ('LEFT', 'Left', "Chain is on the left side"),
            ('RIGHT', 'Right', "Chain is on the right side")],
        default='NONE')

    Limb: EnumProperty(name="Limb", description="What appendage this chain is for. (mostly used for naming and organisation)",
        items=[('ARM', 'Arm', "This is meant to be an arm chain"),
            ('DIGIT', 'Digit', "This is meant to be a digit chain. (Toes, Fingers and Thumbs)"),
            ('LEG', 'Leg', "This is meant to be a leg chain"),
            ('SPINE', 'Spine', "This is meant to be a spine chain"),
            ('TAIL', 'Tail', "This is meant to be a tail chain"),
            ('WING', 'Wing', "This is meant to be a wing chain")],
        default='ARM')

    Bones: CollectionProperty(type=_properties_.JK_ARL_Chain_Bone_Props)
    
    Pole: PointerProperty(type=_properties_.JK_ARL_Chain_Pole_Bone_Props)

    Targets: CollectionProperty(type=_properties_.JK_ARL_Chain_Target_Bone_Props)

    Spline: PointerProperty(type=_properties_.JK_ARL_Chain_Spline_Props)

    Forward: CollectionProperty(type=_properties_.JK_ARL_Chain_Forward_Props)

    def execute(self, context):
        armature = bpy.context.object
        _functions_.Set_Chain(self, armature)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        bone = bpy.context.active_bone
        self.Owner = bone.name
        #self.Type = self.Type # trigger the Type update on invoke...
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        armature = bpy.context.object
        if self.Action == 'ADD':
            bone = bpy.context.active_bone
            layout.ui_units_x = 25
            row = layout.row()
            col = row.column()
            col.prop(self, "Type")
            col = row.column()
            col.prop(self, "Limb")
            col.enabled = False if self.Type in ['PLANTIGRADE', 'DIGITIGRADE'] else True
            col = row.column()
            col.prop(self, "Side")
            col = row.column()
            col.prop_search(self, "Owner", armature.data, "bones", text="Owner")
            #col.prop(self, "Owner")
            box = layout.box()
            if self.Type == 'OPPOSABLE':
                if bone.parent != None:
                    row = box.row()
                    if len(bone.children) > 0:
                        row.prop_search(self.Targets[0], "Source", bone, "children", text="Create Target From")
                    else:
                        row.prop_search(self.Targets[0], "Source", armature.data, "bones", text="Create Target From")
                    row = box.row()
                    row.prop(self.Pole, "Source", text="Create Pole From")
                    row.enabled = False
                    row = box.row()
                    row.prop(self.Pole, "Axis")
                    row.prop(self.Pole, "Distance")
                    row.prop(self.Pole, "Angle")
                else:
                    box.label(text="WARNING - Choose a different Owner!")
                    box.label(text="The currently active bone has no parent so there can be no chain.")
            elif self.Type == 'PLANTIGRADE':
                if bone.parent != None:
                    row = box.row()
                    if len(bone.children) > 0:
                        child = bone.children[self.Targets[0].Source]
                        row.prop_search(self.Targets[0], "Source", bone, "children", text="Create Target From")
                    else:
                        child = None
                        row.prop_search(self.Targets[0], "Source", armature.data, "bones", text="Create Target From")
                    row = box.row()
                    if child != None and len(child.children) > 0:
                        row.prop_search(self.Targets[0], "Pivot", child, "children", text="Create Controls From")
                    else:
                        row.prop_search(self.Targets[0], "Pivot", armature.data, "bones", text="Create Controls From")
                    row = box.row()
                    row.prop(self.Pole, "Source", text="Create Pole From")
                    row.enabled = False
                    row = box.row()
                    row.prop(self.Pole, "Axis")
                    row.prop(self.Pole, "Distance")
                    row.prop(self.Pole, "Angle")
                else:
                    box.label(text="WARNING - Choose a different Owner!")
                    box.label(text="The currently active bone has no parent so there can be no chain.")
            elif self.Type == 'DIGITIGRADE':
                if bone.parent != None and bone.parent.parent != None:
                    row = box.row()
                    if len(bone.children) > 0:
                        row.prop_search(self.Targets[0], "Source", bone, "children", text="Create Target From")
                    else:
                        row.prop_search(self.Targets[0], "Source", armature.data, "bones", text="Create Target From")
                    row = box.row()
                    row.prop_search(self.Targets[0], "Pivot", bone.parent, "children", text="Create Control From")
                else:
                    box.label(text="WARNING - Choose a different Owner!")
                    box.label(text="The currently active bone doesn't have enough parents so there can be no chain.")
            elif self.Type == 'SPLINE':
                row = box.row()
                row.prop(self, "Length")
                for b in self.Bones:
                    row = box.row()
                    row.label(text=b.name)
                    if b == self.Bones[0]:
                        row.prop(self.Spline, "Use_start")
                    elif b == self.Bones[-1]:    
                        row.prop(self.Spline, "Use_end")
                    else:
                        row.prop(b, "Has_target")
            elif self.Type == 'FORWARD':
                row = box.row()
                row.prop(self, "Length")
                for i, b in enumerate(self.Bones):
                    b_box = box.box()
                    row = b_box.row()
                    row.label(text=b.name)
                    col = row.column()
                    col.prop(self.Forward[b.name], "Loc")
                    col = row.column()
                    col.prop(self.Forward[b.name], "Rot")
                    col = row.column()
                    col.prop(self.Forward[b.name], "Sca")
                    col = row.column()
                    col.label(text="Space:")
                    col.prop(self.Forward[b.name], "Target", text="")
                    col.label(text="To")
                    col.prop(self.Forward[b.name], "Owner", text="")
            elif self.Type == 'SCALAR':
                row = box.row()
                row.prop(self, "Length")
        else:
            armature = bpy.context.object
            chain = armature.ARL.Chains[armature.ARL.Chain]
            layout.label(text="Are you sure you want to remove this chain rigging?")
            box = layout.b_box()
            row = box.row()
            row.label(text="Limb: " + chain.Limb)
            row.label(text="| Type: " + chain.Type)
            row.label(text="| Bone: " + chain.Bones[0].name)
        