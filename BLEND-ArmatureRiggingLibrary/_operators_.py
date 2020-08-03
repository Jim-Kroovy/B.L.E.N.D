import bpy

from bpy.props import (PointerProperty, IntProperty, EnumProperty)

from . import _properties_, _functions_

class JK_OT_Add_Twist_Bone(bpy.types.Operator):
    """Adds a twist bone rigging to the active bone"""
    bl_idname = "jk.add_twist_bone"
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

#class JK_OT_Add_FK_Chain(bpy.types.Operator):
    #"""Adds an FK chain from the active bone"""
    #bl_idname = "jk.add_fk_chain"
    #bl_label = "Add FK Chain"

    #Chain: PointerProperty(type=)

    #def execute(self, context):
        #return {'FINISHED'}

class JK_OT_Add_IK_Chain(bpy.types.Operator):
    """Adds an IK chain from the active bone"""
    bl_idname = "jk.add_ik_chain"
    bl_label = "Add IK Chain"

    Type: EnumProperty(name="Type", description="The type of limb IK chain",
        items=[('SCALAR', 'Scalar', "An IK chain of any length controlled by scaling, rotating a parent of the target. (Generally used for fingers)"),
        ('OPPOSABLE', 'Opposable', "A simple IK chain of 2 bones with a pole target. (Generally used by arms)"),
        ('PLANTIGRADE', 'Plantigrade', "An IK chain of 2 bones with a pole target and standard foot rolling controls. (Generally used by human legs)"),
        ('DIGITIGRADE', 'Digitigrade', "An IK chain of 2 bones with a pole target and special foot controls. (Generally used by animal legs)"),
        ('SPLINE', 'Spline', "A spline IK chain of any length controlled by a curve that's manipulated with target bones. (Generally used by tails/spines)")],
        default='OPPOSABLE')

    Chain: PointerProperty(type=_properties_.JK_ARL_IK_Chain_Props)

    Length: IntProperty(name="Chain Length", description="How far through its parents should this IK chain run",
    default=2, min=0)

    def execute(self, context):
        armature = bpy.context.object
        ARL = armature.ARL
        cb_names = [cb.name for cb in self.Chain.Bones]
        # if we are adding an opposable chain...
        if self.Chain.Type == 'OPPOSABLE':
            # get the poles transform axes...
            axes = [True, False] if 'X' in self.Chain.Pole.Axis else [False, True]
            # create the IK target...
            tb_name = _functions_.Add_Opposable_IK_Target(armature, self.Chain.Targets[0].name)
            # create the pole target...
            pb_name = _functions_.Add_IK_Pole(armature, axes, self.Chain.Pole.Distance, cb_names[1], self.Chain.Limb)
            # create and constrain the chain bones...
            _functions_.Add_Opposable_IK_Chain_Bones(armature, cb_names, tb_name, pb_name)
        # else if we are adding a plantigrade chain...
        elif self.Chain.Type == 'PLANTIGRADE':
            # get the poles transform axes...
            axes = [True, False] if 'X' in self.Chain.Pole.Axis else [False, True]
            # create the IK target and foot controls...
            tb_name = _functions_.Add_Plantigrade_Foot_Controls(armature, self.Chain.Targets[0].name, self.Chain.Foot.Pivot, self.Chain.Side)
            # create the pole target...
            pb_name = _functions_.Add_IK_Pole(armature, axes, self.Chain.Pole.Distance, cb_names[1], self.Chain.Limb)
            # create and constrain the chain bones...
            _functions_.Add_Opposable_IK_Chain_Bones(armature, cb_names, tb_name, pb_name)
        # else if we are adding a spline chain...
        elif self.Chain.Type == 'SPLINE':
            # get the target names...
            tb_names = [cb.name for cb in self.Chain.Bones if cb.Has_target]
            # set the curve name...
            sc_name = self.armature.name + "_IK_SPLINE_" + str(len(ARL.Splines))
            # add the bones we need...
            _functions_.Add_Spline_IK_Bones(armature, cb_names, tb_names)
            # add and hook the curve...
            _functions_.Add_Spline_IK_Curve(armature, tb_names, sc_name)

        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        bone = bpy.context.active_bone
        if self.Chain.Type == 'OPPOSABLE':
            pg_target = self.Chain.Targets.add()
            pg_target.name = bone.children[0].name
            pg_bone = self.Chain.Bones.add()
            pg_bone.name = bone.name
            pg_bone = self.Chain.Bones.add()
            pg_bone.name = bone.parent.name
            self.Chain.Pole.name = bone.parent.name
        elif self.Chain.Type == 'PLANTIGRADE':
            pg_target = self.Chain.Targets.add()
            pg_target.name = bone.children[0]
            pg_bone = self.Chain.Bones.add()
            pg_bone.name = bone.name
            pg_bone = self.Chain.Bones.add()
            pg_bone.name = bone.parent.name
            self.Chain.Pole.name = bone.parent.name
            if bone.children[0] and bone.children[0].children[0]:
                self.Chain.Pole.Pivot = bone.children[0].children[0].name
        elif self.Chain.Type == 'SPLINE':
            parent = bone
            for i in range(0, self.Length):
                pg_bone = self.Chain.Bones.add()
                pg_bone.name = parent.name
                parent = parent.parent 
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.ui_units_x = 25
        row = layout.row()
        col = row.column()
        col.prop(self.Chain, "Type")
        col = row.column()
        col.prop(self.Chain, "Limb")
        col.enabled = False if self.Chain.Type in ['PLANTIGRADE', 'DIGITIGRADE'] else True
        col = row.column()
        col.prop(self.Chain, "Side")
        box = layout.box()
        if self.Chain.Type == 'OPPOSABLE':
            row = box.row()
            row.prop_search(self.Chain.Targets[0], "name", bpy.context.active_pose_bone, "children", text="Create Target From")
            row = box.row()
            row.prop(self.Chain.Pole, "name", text="Create Pole From")
            row = box.row()
            row.prop(self.Chain.Pole, "Axis")
            row.prop(self.Chain.Pole, "Distance")
        elif self.Chain.Type == 'PLANTIGRADE':
            row = box.row()
            row.prop_search(self.Chain.Targets[0], "name", bpy.context.active_pose_bone, "children", text="Create Target From")
            row = box.row()
            row.prop(self.Chain.Foot, "Pivot", text="Create Ball From")
            row = box.row()
            row.label(self.Chain.Pole, "name", text="Create Pole From")
            row = box.row()
            row.prop(self.Chain.Pole, "Axis")
            row.prop(self.Chain.Pole, "Distance")
        elif self.Chain.Type == 'SPLINE':
            row = box.row()
            row.prop(self, "Length")
            for pg_bone in self.Chain.Bones:
                row = box.row()
                row.label(text=pg_bone.name)
                row.prop(pg_bone, "Has_target")