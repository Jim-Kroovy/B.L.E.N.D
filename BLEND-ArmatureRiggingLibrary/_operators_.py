import bpy

from bpy.props import (PointerProperty, IntProperty, EnumProperty)

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
        self.Chain.Targets.clear()
        self.Chain.Bones.clear()
        if self.Type in ['OPPOSABLE', 'PLANTIGRADE']:
            pg_bone = self.Chain.Bones.add()
            pg_bone.name = bone.name
            pg_bone = self.Chain.Bones.add()
            pg_bone.name = bone.parent.name
            self.Chain.Pole.name = bone.parent.name
            if len(bone.children) > 0:
                pg_target = self.Chain.Targets.add()
                pg_target.name = bone.children[0].name 
                if len(bone.children[0].children[0]) > 0 and self.Type == 'PLANTIGRADE':
                    self.Chain.Foot.Pivot = bone.children[0].children[0].name
                    self.Chain.Limb = 'LEG'
        elif self.Chain.Type in ['SPLINE', 'FORWARD']:
            parent = bone
            bpy.ops.armature.select_all(action='DESELECT')
            for i in range(0, self.Length):
                if parent:
                    parent.select = True
                    pg_bone = self.Chain.Bones.add()
                    pg_bone.name = parent.name
                    parent = parent.parent

    Type: EnumProperty(name="Type", description="The type of limb IK chain",
        items=[('SCALAR', 'Scalar', "An IK chain of any length controlled by scaling, rotating a parent of the target. (Generally used for fingers)"),
        ('OPPOSABLE', 'Opposable', "A simple IK chain of 2 bones with a pole target. (Generally used by arms)"),
        ('PLANTIGRADE', 'Plantigrade', "An IK chain of 2 bones with a pole target and standard foot rolling controls. (Generally used by human legs)"),
        ('DIGITIGRADE', 'Digitigrade', "An IK chain of 2 bones with a pole target and special foot controls. (Generally used by animal legs)"),
        ('SPLINE', 'Spline', "A spline IK chain of any length controlled by a curve that's manipulated with target bones. (Generally used by tails/spines)"),
        ('FORWARD', 'Forward', "An FK chain of any length where the chain copies loc/rot/scale of a parent/target. (Generally an alternative used for fingers/tails)")],
        default='OPPOSABLE', update=Update_Operator)

    Chain: PointerProperty(type=_properties_.JK_ARL_Chain_Props)

    Length: IntProperty(name="Chain Length", description="How far through its parents should this IK chain run",
    default=2, min=1, update=Update_Operator)

    def execute(self, context):
        armature = bpy.context.object
        ARL = armature.ARL
        cb_names = [cb.name for cb in self.Chain.Bones]
        # if we are adding an opposable chain...
        if self.Type == 'OPPOSABLE':
            # get the poles transform axes and distance...
            axes = [True, False] if 'X' in self.Chain.Pole.Axis else [False, True]
            distance = (self.Chain.Pole.Distance * -1) if 'NEGATIVE' in self.Chain.Pole.Axis else (self.Chain.Pole.Distance)
            # create the IK target...
            tb_name = _functions_.Add_Opposable_Chain_Target(armature, self.Chain.Targets[0].name, self.Chain.Limb)
            # create the pole target...
            pb_name = _functions_.Add_Chain_Pole(armature, axes, distance, self.Chain.Pole.name, self.Chain.Limb)
            # create and constrain the chain bones...
            _functions_.Add_Opposable_Chain_Bones(armature, cb_names, tb_name, pb_name, self.Chain.Pole.Angle)
        # else if we are adding a plantigrade chain...
        elif self.Type == 'PLANTIGRADE':
            # get the poles transform axes and distance...
            axes = [True, False] if 'X' in self.Chain.Pole.Axis else [False, True]
            distance = (self.Chain.Pole.Distance * -1) if 'NEGATIVE' in self.Chain.Pole.Axis else (self.Chain.Pole.Distance)
            # create the IK target and foot controls...
            tb_name = _functions_.Add_Plantigrade_Foot_Controls(armature, self.Chain.Targets[0].name, self.Chain.Foot.Pivot, self.Chain.Side)
            # create the pole target...
            pb_name = _functions_.Add_Chain_Pole(armature, axes, distance, self.Chain.Pole.name, self.Chain.Limb)
            # create and constrain the chain bones...
            _functions_.Add_Opposable_Chain_Bones(armature, cb_names, tb_name, pb_name, self.Chain.Pole.Angle)
        # else if we are adding a spline chain...
        elif self.Type == 'SPLINE':
            # get the target names...
            tb_names = [cb.name for cb in self.Chain.Bones if cb.Has_target]
            # set the curve name...
            sc_name = self.armature.name + "_IK_SPLINE_" + str(len(ARL.Splines))
            # add the bones we need...
            _functions_.Add_Spline_Chain_Bones(armature, cb_names, tb_names)
            # add and hook the curve...
            _functions_.Add_Spline_Chain_Curve(armature, tb_names, sc_name)
        elif self.Type == 'FORWARD':
            # create the target bone...
            tb_name = _functions_.Add_Forward_Chain_Target(armature, cb_names[-1], cb_names[0], self.Chain.Limb)
            # get the default constraint values out of the chains forward chain properties...
            loc, rot, sca = self.Chain.Forward.Loc, self.Chain.Forward.Rot, self.Chain.Forward.Sca
            target, owner = self.Chain.Forward.Target, self.Chain.Forward.Owner
            # constrain the chain bones...
            _functions_.Add_Forward_Chain_Bones(armature, cb_names, tb_name, loc, rot, sca, target, owner)
        elif self.Type == 'SCALAR':
            # create the scale control bone... (it's the same as the forward control)
            cb_name = _functions_.Add_Forward_Chain_Target(armature, cb_names[-1], cb_names[0], self.Chain.Limb)
            # create the target...
            tb_name = _functions_.Add_Scalar_Chain_Target(armature, self.Chain.Targets[0].name, cb_name, self.Chain.Limb)
            # create and constrain the chain bones...
            _functions_.Add_Opposable_Chain_Bones(armature, cb_names, tb_name, pb_name, self.Chain.Pole.Angle)
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
        col.prop(self.Chain, "Limb")
        col.enabled = False if self.Chain.Type in ['PLANTIGRADE', 'DIGITIGRADE'] else True
        col = row.column()
        col.prop(self.Chain, "Side")
        box = layout.box()
        if self.Type == 'OPPOSABLE':
            row = box.row()
            row.prop_search(self.Chain.Targets[0], "name", bone, "children", text="Create Target From")
            row = box.row()
            row.prop(self.Chain.Pole, "name", text="Create Pole From")
            row.enabled = False
            row = box.row()
            row.prop(self.Chain.Pole, "Axis")
            row.prop(self.Chain.Pole, "Distance")
            row.prop(self.Chain.Pole, "Angle")
        elif self.Type == 'PLANTIGRADE':
            child = bone.children[self.Chain.Targets[0].name]
            row = box.row()
            row.prop_search(self.Chain.Targets[0], "name", bone, "children", text="Create Target From")
            row = box.row()
            row.prop_search(self.Chain.Foot, "Pivot", child, "children", text="Create Target From")
            #row.prop(self.Chain.Foot.Pivot, "Pivot", text="Create Ball From")
            row = box.row()
            row.prop(self.Chain.Pole, "name", text="Create Pole From")
            row.enabled = False
            row = box.row()
            row.prop(self.Chain.Pole, "Axis")
            row.prop(self.Chain.Pole, "Distance")
            row.prop(self.Chain.Pole, "Angle")
        elif self.Type == 'SPLINE':
            row = box.row()
            row.prop(self, "Length")
            for pg_bone in self.Chain.Bones:
                row = box.row()
                row.label(text=pg_bone.name)
                row.prop(pg_bone, "Has_target")
        elif self.Type == 'FORWARD':
            row = box.row()
            row.prop(self, "Length")
        elif self.Type == 'SCALAR':
            row = box.row()
            row.prop(self, "Length")
        