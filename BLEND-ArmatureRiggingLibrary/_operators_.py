import bpy

from bpy.props import (PointerProperty, CollectionProperty, IntProperty, EnumProperty)

from . import _properties_, _functions_

class JK_OT_Add_Twist_Bone(bpy.types.Operator):
    """Adds a twist bone rigging to the active bone"""
    bl_idname = "jk.add_twist"
    bl_label = "Add Twist Bone"

    Twist: PointerProperty(type=_properties_.JK_ARL_Twist_Bone_Props)

    def execute(self, context):
        armature = bpy.context.object
        if self.Twist.Type == 'HEAD_HOLD':
            limits_x = [self.Twist.Limits_x.Use, self.Twist.Limits_x.Min, self.Twist.Limits_x.Max]
            limits_z = [self.Twist.Limits_z.Use, self.Twist.Limits_z.Min, self.Twist.Limits_z.Max]
            head_tail, has_pivot = self.Twist.Float, self.Twist.Has_pivot
            _functions_.Add_Head_Hold_Twist(armature, self.Twist.name, self.Twist.Target, head_tail, limits_x, limits_z, has_pivot)
        elif self.Twist.Type == 'TAIL_FOLLOW':
            limits_y = [self.Twist.Limits_y.Use, self.Twist.Limits_y.Min, self.Twist.Limits_y.Max]
            influence, has_pivot = self.Twist.Float, self.Twist.Has_pivot
            _functions_.Add_Tail_Follow_Twist(armature, self.Twist.name, self.Twist.Target, influence, limits_y, has_pivot)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        bone = bpy.context.active_bone
        self.Twist.name = bone.name
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        armature = bpy.context.object
        layout = self.layout
        layout.prop(self.Twist, "Type")
        box = layout.box()
        row = box.row()
        row.prop_search(self.Twist, "Target", armature.pose, "bones")
        row.prop(self.Twist, "Has_pivot")
        if self.Twist.Type == 'HEAD_HOLD':
            row = box.row()
            row.prop(self.Twist.Limits_x, "Use")
            row.prop(self.Twist.Limits_x, "Min")
            row.prop(self.Twist.Limits_x, "Max")
            row = box.row()
            row.prop(self.Twist.Limits_z, "Use")
            row.prop(self.Twist.Limits_z, "Min")
            row.prop(self.Twist.Limits_z, "Max")
            row = box.row()
            row.prop(self.Twist, "Float", text="Head Vs Tail")
        elif self.Twist.Type == 'TAIL_FOLLOW':
            row = box.row()
            row.prop(self.Twist.Limits_y, "Use")
            row.prop(self.Twist.Limits_y, "Min")
            row.prop(self.Twist.Limits_y, "Max")
            row = box.row()
            row.prop(self.Twist, "Float", text="Influence")

class JK_OT_Add_Chain(bpy.types.Operator):
    """Adds a chain from the active bone that is articulated with constraints"""
    bl_idname = "jk.add_chain"
    bl_label = "Add Chain Rigging"

    def Update_Operator(self, context):
        bone = bpy.context.active_bone
        self.Targets.clear()
        self.Bones.clear()
        self.Limb = _functions_.Get_Bone_Limb(bone.name)
        self.Side = _functions_.Get_Bone_Side(bone.name)
        if self.Type in ['OPPOSABLE', 'PLANTIGRADE']:
            cb = self.Bones.add()
            cb.name = bone.name
            cb = self.Bones.add()
            cb.name = bone.parent.name
            self.Pole.Source = bone.parent.name
            self.Pole.Angle = _functions_.Get_Pole_Angle(self.Pole.Axis)
            if len(bone.children) > 0:
                tb = self.Targets.add()
                tb.Source = bone.children[0].name
                child = bone.children[0]
            else:
                child = None
            if self.Type == 'PLANTIGRADE':
                self.Limb = 'LEG' 
                if child != None and len(child.children) > 0:
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

    Type: EnumProperty(name="Type", description="The type of limb IK chain",
        items=[('OPPOSABLE', 'Opposable', "A simple IK chain of 2 bones with a pole target. (Generally used by arms)"),
        ('SCALAR', 'Scalar', "An IK chain of any length controlled by scaling, rotating a parent of the target. (Generally used for fingers)"),
        ('PLANTIGRADE', 'Plantigrade', "An IK chain of 2 bones with a pole target and standard foot rolling controls. (Generally used by human legs)"),
        ('DIGITIGRADE', 'Digitigrade', "An IK chain of 2 bones with a pole target and special foot controls. (Generally used by animal legs)"),
        ('SPLINE', 'Spline', "A spline IK chain of any length controlled by a curve that's manipulated with target bones. (Generally used by tails/spines)"),
        ('FORWARD', 'Forward', "An FK chain of any length where the chain copies loc/rot/scale of a parent/target. (Generally an alternative used for fingers/tails)")],
        default='OPPOSABLE', update=Update_Operator)

    Length: IntProperty(name="Chain Length", description="How far through its parents should this IK chain run",
        default=2, min=1, update=Update_Operator)
    
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
        ARL = armature.ARL
        chain = ARL.Chains.add()
        chain.Type, chain.Side, chain.Limb = self.Type, self.Side, self.Limb
        if armature.data.bones[self.Bones[-1].name].parent != None:
            chain.Parent = armature.data.bones[self.Bones[-1].name].parent.name
        # in rare cases snapping being on can cause problems?...
        bpy.context.scene.tool_settings.use_snap = False
        # and we don't want to be keying anything in pose mode...
        bpy.context.scene.tool_settings.use_keyframe_insert_auto = False
        # some of the functions need pivot point to be individual origins...
        bpy.context.scene.tool_settings.transform_pivot_point = 'INDIVIDUAL_ORIGINS'
        # get all the chain bone data...
        for b in self.Bones:
            cb = _functions_.Get_Chain_Bone_Data(self, b, ARL.Affixes, chain)
            # get the target if it has one... (only used by spline and forward chains)
            if b.Has_target: 
                cb.Has_target = True
                _functions_.Get_Chain_Target_Data(self, ARL.Affixes, chain, cb)
        # only opposable and plantigrade chains have pole targets...
        pb = _functions_.Get_Chain_Pole_Data(self, ARL.Affixes, chain) if self.Type in ['OPPOSABLE', 'PLANTIGRADE'] else None
        # the forward and spline chains get their targets when getting bones...
        tb = _functions_.Get_Chain_Target_Data(self, ARL.Affixes, chain, None) if self.Type not in ['FORWARD', 'SPLINE'] else None
        if self.Type == 'OPPOSABLE':
            _functions_.Set_Opposable_Chain(armature, tb, pb, chain.Bones, 'ADD')
        elif self.Type == 'PLANTIGRADE':
            _functions_.Set_Plantigrade_Chain(armature, tb, pb, chain.Bones, chain.Side, 'ADD')
        elif self.Type == 'DIGITIGRADE':
            _functions_.Set_Digitigrade_Chain(armature, tb, chain.Bones, chain.Side, 'ADD')
        elif self.Type == 'FORWARD':
            _functions_.Set_Forward_Chain(armature, chain.Targets, chain.Bones, self.Forward, 'ADD')
        elif self.Type == 'SCALAR':
            _functions_.Set_Scalar_Chain(armature, tb, chain.Bones, 'ADD')
        elif self.Type == 'SPLINE':
            _functions_.Set_Spline_Chain(armature, self.Spline, chain.Targets, chain.Bones, chain.Spline, 'ADD')
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        self.Type = self.Type # trigger the Type update on invoke...
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        bone = bpy.context.active_bone
        layout = self.layout
        layout.ui_units_x = 25
        row = layout.row()
        col = row.column()
        col.prop(self, "Type")
        col = row.column()
        col.prop(self, "Limb")
        col.enabled = False if self.Type in ['PLANTIGRADE', 'DIGITIGRADE'] else True
        col = row.column()
        col.prop(self, "Side")
        box = layout.box()
        if self.Type == 'OPPOSABLE':
            if len(bone.children) > 0:
                row = box.row()
                row.prop_search(self.Targets[0], "Source", bone, "children", text="Create Target From")
            row = box.row()
            row.prop(self.Pole, "Source", text="Create Pole From")
            row.enabled = False
            row = box.row()
            row.prop(self.Pole, "Axis")
            row.prop(self.Pole, "Distance")
            row.prop(self.Pole, "Angle")
        elif self.Type == 'PLANTIGRADE':
            child = bone.children[self.Targets[0].Source]
            row = box.row()
            row.prop_search(self.Targets[0], "Source", bone, "children", text="Create Target From")
            row = box.row()
            row.prop_search(self.Targets[0], "Pivot", child, "children", text="Create Target From")
            row = box.row()
            row.prop(self.Pole, "Source", text="Create Pole From")
            row.enabled = False
            row = box.row()
            row.prop(self.Pole, "Axis")
            row.prop(self.Pole, "Distance")
            row.prop(self.Pole, "Angle")
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
        