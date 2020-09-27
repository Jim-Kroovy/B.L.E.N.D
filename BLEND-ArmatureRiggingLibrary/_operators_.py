import bpy

from bpy.props import (PointerProperty, CollectionProperty, IntProperty, EnumProperty, StringProperty, BoolProperty, FloatProperty)

from . import _properties_, _functions_

class JK_OT_Set_Pivot(bpy.types.Operator):
    """Adds a multi-purpose pivot bone, usually used to offset transforms or be used as a pivot point while transforming"""
    bl_idname = "jk.pivot_set"
    bl_label = "Set Pivot Rigging"
    bl_options = {'REGISTER', 'UNDO'}

    Action: EnumProperty(name="Action", description="",
        items=[('ADD', 'Add', ""), ('REMOVE', 'Remove', ""), ('UPDATE', 'Update', "")],
        default='ADD')
    
    Pivot: PointerProperty(type=_properties_.JK_ARL_Pivot_Bone_Props)

    def execute(self, context):
        armature = bpy.context.view_layer.objects.active
        pivot = self.Pivot if self.Action == 'ADD' else armature.ARL.Pivots[armature.ARL.Pivot]
        _functions_.Set_Pivot(armature, pivot, self.Action)
        return {'FINISHED'}

    def invoke(self, context, event):
        if self.Action == 'ADD':
            wm = context.window_manager
            bone = bpy.context.active_bone
            self.Pivot.Source = bone.name
            return wm.invoke_props_dialog(self)
        elif self.Action == 'UPDATE':
            return context.window_manager.invoke_popup(self)
        else:
            return self.execute(bpy.context)

    def draw(self, context):
        layout = self.layout
        armature = bpy.context.object
        pivot = self.Pivot if self.Action == 'ADD' else armature.ARL.Pivots[armature.ARL.Pivot]
        row = layout.row()
        row.prop(pivot, "Type")
        row.prop(pivot, "Is_parent")
        row = layout.row()
        row.prop_search(pivot, "Source", armature.data, "bones", text="Add Pivot To")

class JK_OT_Set_Floor(bpy.types.Operator):
    """Adds a floor bone then a floor constraint to the source bone"""
    bl_idname = "jk.floor_set"
    bl_label = "Set Floor Rigging"
    bl_options = {'REGISTER', 'UNDO'}
    
    Action: EnumProperty(name="Action", description="",
        items=[('ADD', 'Add', ""), ('REMOVE', 'Remove', ""), ('UPDATE', 'Update', "")],
        default='ADD')
    
    Floor: PointerProperty(type=_properties_.JK_ARL_Floor_Bone_Props)

    def execute(self, context):
        armature = bpy.context.view_layer.objects.active
        floor = self.Floor if self.Action == 'ADD' else armature.ARL.Floors[armature.ARL.Floor]
        _functions_.Set_Floor(armature, floor, self.Action)
        return {'FINISHED'}

    def invoke(self, context, event):
        if self.Action == 'ADD':
            wm = context.window_manager
            bone = bpy.context.active_bone
            self.Floor.Source = bone.name
            return wm.invoke_props_dialog(self)
        elif self.Action == 'UPDATE':
            return context.window_manager.invoke_popup(self)
        else:
            return self.execute(bpy.context)

    def draw(self, context):
        layout = self.layout
        armature = bpy.context.object
        floor = self.Floor if self.Action == 'ADD' else armature.ARL.Floors[armature.ARL.Floor]
        row = layout.row()
        row.prop_search(floor, "Source", armature.data, "bones", text="Add Floor To")
        row = layout.row()
        row.prop_search(floor, "Parent", armature.data, "bones", text="Floor Parent")

class JK_OT_Set_Twist(bpy.types.Operator):
    """Adds a twist bone rigging to the active bone"""
    bl_idname = "jk.twist_set"
    bl_label = "Set Twist Bone"
    bl_options = {'REGISTER', 'UNDO'}

    Action: EnumProperty(name="Action", description="",
        items=[('ADD', 'Add', ""), ('REMOVE', 'Remove', ""), ('UPDATE', 'Update', "")],
        default='ADD')

    Twist: PointerProperty(type=_properties_.JK_ARL_Twist_Bone_Props)

    def execute(self, context):
        armature = bpy.context.view_layer.objects.active
        twist = self.Twist if self.Action == 'ADD' else armature.ARL.Twists[armature.ARL.Twist]
        _functions_.Set_Floor(armature, twist, self.Action)
        return {'FINISHED'}

    def invoke(self, context, event):
        if self.Action == 'ADD':
            wm = context.window_manager
            bone = bpy.context.active_bone
            self.Source = bone.name
            return wm.invoke_props_dialog(self)
        elif self.Action == 'UPDATE':
            return context.window_manager.invoke_popup(self)
        else:
            return self.execute(bpy.context)

    def draw(self, context):
        armature = bpy.context.object
        twist = self.Twist if self.Action == 'ADD' else armature.ARL.Twists[armature.ARL.Twist]
        layout = self.layout
        row = layout.row()
        row.prop(twist, "Type")
        row.prop(twist, "Has_pivot")
        box = layout.box()
        row = box.row()
        row.prop_search(twist, "Source", armature.pose, "bones")
        row = box.row()
        row.prop_search(twist, "Target", armature.pose, "bones")
        if twist.Type == 'HEAD_HOLD':
            row = box.row()
            row.prop(twist, "Use_x", text="Use Limit X")
            row.prop(twist, "Min_x", text="Min X")
            row.prop(twist, "Max_x", text="Max X")
            row = box.row()
            row.prop(twist, "Use_z", text="Use Limit Z")
            row.prop(twist, "Min_z", text="Min Z")
            row.prop(twist, "Max_z", text="Max Z")
            row = box.row()
            row.prop(twist, "Float", text="Head Vs Tail")
        elif self.Type == 'TAIL_FOLLOW':
            row = box.row()
            row.prop(twist, "Use_y", text="Use Limit Y")
            row.prop(twist, "Min_y", text="Min Y")
            row.prop(twist, "Max_y", text="Max Y")
            row = box.row()
            row.prop(twist, "Float", text="Influence")

class JK_OT_Set_Chain(bpy.types.Operator):
    """Adds a chain from the active bone that is articulated with constraints"""
    bl_idname = "jk.chain_set"
    bl_label = "Set Chain Rigging"
    bl_options = {'REGISTER', 'UNDO'}
    
    Action: EnumProperty(name="Action", description="",
        items=[('ADD', 'Add', ""), ('REMOVE', 'Remove', ""), ('UPDATE', 'Update', "")],
        default='ADD')
    
    Chain: PointerProperty(type=_properties_.JK_ARL_Chain_Props)

    def execute(self, context):
        armature = bpy.context.view_layer.objects.active
        chain = self.Chain if self.Action == 'ADD' else armature.ARL.Chains[armature.ARL.Chain]
        # in rare cases snapping being on can cause problems?... (not a clue why, it's pretty random, probably an API bug)
        bpy.context.scene.tool_settings.use_snap = False
        # and we don't want to be keying anything in pose mode...
        bpy.context.scene.tool_settings.use_keyframe_insert_auto = False
        # some of the functions need pivot point to be individual origins...
        bpy.context.scene.tool_settings.transform_pivot_point = 'INDIVIDUAL_ORIGINS'
        # x axis mirror in edit mode can tamper with existing chains as well...
        armature.data.use_mirror_x = False
        # then we can set the set chain by the action...
        _functions_.Set_Chain(armature, chain, self.Action)
        return {'FINISHED'}

    def invoke(self, context, event):
        if self.Action == 'ADD':
            wm = context.window_manager
            bone = bpy.context.active_bone
            self.Chain.Owner = bone.name
            return wm.invoke_props_dialog(self)
        elif self.Action == 'UPDATE':
            return context.window_manager.invoke_popup(self)
        else:
            return self.execute(bpy.context)

    def draw(self, context):
        layout = self.layout
        armature = bpy.context.object
        chain = self.Chain if self.Action == 'ADD' else armature.ARL.Chains[armature.ARL.Chain]
        layout.ui_units_x = 25
        row = layout.row()
        col = row.column()
        col.prop(chain, "Type")
        col.enabled = True if self.Action == 'ADD' else False
        col = row.column()
        col.prop(chain, "Limb")
        col.enabled = False if chain.Type in ['PLANTIGRADE', 'DIGITIGRADE'] else True
        col = row.column()
        col.prop(chain, "Side")
        box = layout.box()
        row = box.row()
        row.prop_search(chain, "Owner", armature.data, "bones", text="Start Chain From")
        row.enabled = True if self.Action == 'ADD' else False
        bone = armature.data.bones[chain.Owner]
        if chain.Type == 'OPPOSABLE':
            if bone.parent != None or self.Action == 'UPDATE':
                row = box.row()
                if len(bone.children) > 0 and self.Action == 'ADD':
                    row.prop_search(chain.Targets[0], "Source", bone, "children", text="Create Target From")
                else:
                    row.prop_search(chain.Targets[0], "Source", armature.data, "bones", text="Create Target From")
                row = box.row()
                row.prop_search(chain.Pole, "Source", armature.data, "bones", text="Create Pole From")
                #row.prop(chain.Pole, "Source", text="Create Pole From")
                row.enabled = False# if self.Action == 'ADD' else True
                row = box.row()
                row.label(text="Pole Settings:")
                row.prop(chain.Pole, "Axis", text="")
                row.prop(chain.Pole, "Distance")
                row.prop(chain.Pole, "Angle")
                row = box.row()
                row.prop_search(chain.Pole, "Root", armature.data, "bones", text="IK Root Bone")
            else:
                box.label(text="WARNING - Choose a different Owner!")
                box.label(text="The currently active bone has no parent so there can be no chain.")
        elif chain.Type == 'PLANTIGRADE':
            if bone.parent != None or self.Action == 'UPDATE':
                row = box.row()
                if len(bone.children) > 0 and self.Action == 'ADD':
                    child = bone.children[chain.Targets[0].Source]
                    row.prop_search(chain.Targets[0], "Source", bone, "children", text="Create Target From")
                else:
                    child = None
                    row.prop_search(chain.Targets[0], "Source", armature.data, "bones", text="Create Target From")
                row = box.row()
                if child != None and len(child.children) > 0:
                    row.prop_search(chain.Targets[0], "Pivot", child, "children", text="Create Controls From")
                else:
                    row.prop_search(chain.Targets[0], "Pivot", armature.data, "bones", text="Create Controls From")
                row = box.row()
                row.prop_search(chain.Pole, "Source", armature.data, "bones", text="Create Pole From")
                row.enabled = False # if self.Action == 'ADD' else True
                row = box.row()
                row.label(text="Pole Settings:")
                row.prop(chain.Pole, "Axis", text="")
                row.prop(chain.Pole, "Distance")
                row.prop(chain.Pole, "Angle")
                row = box.row()
                row.prop_search(chain.Pole, "Root", armature.data, "bones", text="IK Root Bone")
            else:
                box.label(text="WARNING - Choose a different Owner!")
                box.label(text="The currently active bone has no parent so there can be no chain.")
        elif chain.Type == 'DIGITIGRADE':
            if (bone.parent != None and bone.parent.parent != None) or self.Action == 'UPDATE':
                row = box.row()
                if len(bone.children) > 0:
                    row.prop_search(chain.Targets[0], "Source", bone, "children", text="Create Target From")
                else:
                    row.prop_search(chain.Targets[0], "Source", armature.data, "bones", text="Create Target From")
                row = box.row()
                row.prop(chain.Targets[0], "Pivot", text="Create Control From")
                row.enabled = False
                row = box.row()
                row.prop_search(chain.Pole, "Root", armature.data, "bones", text="IK Root Bone")
            else:
                box.label(text="WARNING - Choose a different Owner!")
                box.label(text="The currently active bone doesn't have enough parents so there can be no chain.")
        elif chain.Type == 'SPLINE':
            row = box.row()
            row.prop(chain, "Length")
            for b in chain.Bones:
                row = box.row()
                row.label(text=b.name)
                if b == chain.Bones[0]:
                    row.prop(chain.Spline, "Use_start")
                elif b == chain.Bones[-1]:    
                    row.prop(chain.Spline, "Use_end")
                else:
                    row.prop(b, "Has_target")
        elif chain.Type == 'FORWARD':
            row = box.row()
            row.prop(chain, "Length")
            for i, b in enumerate(chain.Bones):
                b_box = box.box()
                row = b_box.row()
                name_col = row.column()
                name_col.label(text=b.name)
                limit_col = row.column()
                loc_row = limit_col.row(align=True)
                loc_row.ui_units_x = 40
                loc_row.label(icon='CON_LOCLIKE')
                loc_row.prop(chain.Forward[b.name], "Loc", text="X", toggle=True, index=0)
                loc_row.prop(chain.Forward[b.name], "Loc", text="Y", toggle=True, index=1)
                loc_row.prop(chain.Forward[b.name], "Loc", text="Z", toggle=True, index=2)
                loc_row.label(icon='CON_ROTLIKE')
                loc_row.prop(chain.Forward[b.name], "Rot", text="X", toggle=True, index=0)
                loc_row.prop(chain.Forward[b.name], "Rot", text="Y", toggle=True, index=1)
                loc_row.prop(chain.Forward[b.name], "Rot", text="Z", toggle=True, index=2)
                loc_row.label(icon='CON_SIZELIKE')
                loc_row.prop(chain.Forward[b.name], "Sca", text="X", toggle=True, index=0)
                loc_row.prop(chain.Forward[b.name], "Sca", text="Y", toggle=True, index=1)
                loc_row.prop(chain.Forward[b.name], "Sca", text="Z", toggle=True, index=2)
        elif chain.Type == 'SCALAR':
            row = box.row()
            row.prop(chain, "Length")

class JK_OT_Select_Bone(bpy.types.Operator):
    """Selects the given bone"""
    bl_idname = "jk.active_bone_set"
    bl_label = "Active"
    bl_options = {'REGISTER', 'UNDO'}

    Bone: StringProperty(name="Bone", description="The bone to make active", default="", maxlen=1024)
    
    def execute(self, context):
        armature = bpy.context.object
        bone = armature.data.bones[self.Bone]
        armature.data.bones.active = bone
        bone.select = True
        return {'FINISHED'}

class JK_OT_Key_Chain(bpy.types.Operator):
    """Keyframes the active chain of bones"""
    bl_idname = "jk.keyframe_chain"
    bl_label = "Keyframe Chain"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        armature = bpy.context.object
        chain = armature.ARL.Chains[armature.ARL.Chain]
        _functions_.Set_Chain_Keyframe(chain, armature)
        return {'FINISHED'}