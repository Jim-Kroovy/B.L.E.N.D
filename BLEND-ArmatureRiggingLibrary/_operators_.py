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
        cb_names = [cb.name for cb in self.Bones]
        chain = ARL.Chains.add()
        chain.Type, chain.Side, chain.Limb = self.Type, self.Side, self.Limb
        # if we are adding an opposable chain...
        if self.Type == 'OPPOSABLE':
            # create the IK target...
            tb = chain.Targets.add()
            tb.Source = self.Targets[0].Source
            tb.name = _functions_.Get_Chain_Target_Affix(ARL.Affixes, self.Limb) + tb.Source
            tb.Local = _functions_.Get_Chain_Target_Affix(ARL.Affixes, self.Limb) + ARL.Affixes.Local + tb.Source
            tb.Target = tb.name
            _functions_.Add_Opposable_Chain_Target(armature, tb)
            # create the pole target...
            pb = chain.Pole
            pb.Source = self.Pole.Source
            pb.name = _functions_.Get_Chain_Target_Affix(ARL.Affixes, self.Limb) + pb.Source
            pb.Local = _functions_.Get_Chain_Target_Affix(ARL.Affixes, self.Limb) + ARL.Affixes.Local + pb.Source
            pb.Axis, pb.Distance, pb.Angle = self.Pole.Axis, self.Pole.Distance, self.Pole.Angle
            _functions_.Add_Chain_Pole(armature, pb)
            # create and constrain the chain bones...
            for b in self.Bones:
                cb = chain.Bones.add()
                cb.name = b.name
                cb.Gizmo = ARL.Affixes.Gizmo + b.name
                cb.Stretch = ARL.Affixes.Gizmo + ARL.Affixes.Stretch + b.name
                cb.Is_owner = True if b == self.Bones[0] else False
            _functions_.Add_Opposable_Chain_Bones(armature, chain.Bones, tb, pb)
        # else if we are adding a plantigrade chain...
        elif self.Type == 'PLANTIGRADE':
            # create the IK target and foot controls...
            tb = chain.Targets.add()
            tb.Source = self.Targets[0].Source
            tb.name = _functions_.Get_Chain_Target_Affix(ARL.Affixes, self.Limb) + tb.Source
            tb.Local = _functions_.Get_Chain_Target_Affix(ARL.Affixes, self.Limb) + ARL.Affixes.Local + tb.Source
            tb.Target, tb.Pivot, tb.Control = ARL.Affixes.Gizmo + tb.Source, self.Targets[0].Pivot, ARL.Affixes.Control + ARL.Affixes.Roll + tb.Source
            _functions_.Add_Plantigrade_Target(armature, tb, self.Side)
            # create the pole target...
            pb = chain.Pole
            pb.Source = self.Pole.Source
            pb.name = _functions_.Get_Chain_Target_Affix(ARL.Affixes, self.Limb) + pb.Source
            pb.Local = _functions_.Get_Chain_Target_Affix(ARL.Affixes, self.Limb) + ARL.Affixes.Local + pb.Source
            pb.Axis, pb.Distance, pb.Angle = self.Pole.Axis, self.Pole.Distance, self.Pole.Angle
            _functions_.Add_Chain_Pole(armature, pb)
            # create and constrain the chain bones...
            for b in self.Bones:
                cb = chain.Bones.add()
                cb.name = b.name
                cb.Gizmo = ARL.Affixes.Gizmo + b.name
                cb.Stretch = ARL.Affixes.Gizmo + ARL.Affixes.Stretch + b.name
                cb.Is_owner = True if b == self.Bones[0] else False
            _functions_.Add_Opposable_Chain_Bones(armature, chain.Bones, tb, pb)
        # else if we are adding a spline chain...
        elif self.Type == 'SPLINE':
            # set the target and chain bone data...
            for b in self.Bones:
                cb = chain.Bones.add()
                cb.name = b.name
                #cb.Gizmo = ARL.Affixes.Gizmo + cb_name
                cb.Stretch = ARL.Affixes.Gizmo + ARL.Affixes.Stretch + b.name
                if b.Has_target: 
                    cb.Has_target = True
                    tb = chain.Targets.add()
                    tb.name = _functions_.Get_Chain_Target_Affix(ARL.Affixes, self.Limb) + cb.name
                    tb.Source = cb.Stretch
            # create the bones we need and get the target names...
            _functions_.Add_Spline_Chain_Bones(armature, chain.Bones, chain.Targets)
            # set the spline data...
            chain.Spline.name = armature.name + "_IK_SPLINE_" + str(len([c for c in ARL.Chains if c.Type == 'SPLINE']))
            chain.Spline.Use_start, chain.Spline.Use_end = self.Spline.Use_start, self.Spline.Use_end
            # create and hook the curve...
            _functions_.Add_Spline_Chain_Curve(armature, chain.Bones, chain.Targets, chain.Spline)
        # else if we are adding a forward chain...
        elif self.Type == 'FORWARD':
           # set the target and chain bone data...
            for b in self.Bones:
                cb = chain.Bones.add()
                cb.name = b.name
                if b.Has_target: 
                    cb.Has_target = True
                    tb = chain.Targets.add()
                    tb.name = ARL.Affixes.Control + self.Limb + "_" + cb.name
                    tb.Source = cb.name
            # add the control target...
            _functions_.Add_Forward_Chain_Target(armature, tb, chain.Bones[0])
            # set the forward chain data and set the constraints... (forward constraint chains are not a collection in the armature props)
            _functions_.Add_Forward_Chain_Constraints(armature, chain.Bones, tb, self.Forward)
        elif self.Type == 'SCALAR':
            # set the data for the chain bones...
            for b in self.Bones:
                cb = chain.Bones.add()
                cb.name = b.name
                cb.Gizmo = ARL.Affixes.Gizmo + b.name
                cb.Stretch = ARL.Affixes.Gizmo + ARL.Affixes.Stretch + b.name
                cb.Is_owner = True if b == self.Bones[0] else False
            # add the target data...
            tb = chain.Targets.add()
            tb.Source = self.Bones[0].name
            tb.name = ARL.Affixes.Control + self.Limb + "_" + self.Bones[-1].name
            tb.Target = _functions_.Get_Chain_Target_Affix(ARL.Affixes, self.Limb) + tb.Source
            tb.Pivot, tb.Local = self.Bones[-1].name, _functions_.Get_Chain_Target_Affix(ARL.Affixes, self.Limb) + ARL.Affixes.Local + tb.Source
            # create the scalar target...
            _functions_.Add_Scalar_Chain_Target(armature, tb)
            # create and constrain the chain bones...
            _functions_.Add_Opposable_Chain_Bones(armature, chain.Bones, tb, None)
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
        