import bpy
from . import _functions_
from bpy.props import (EnumProperty, BoolProperty, StringProperty, PointerProperty, IntProperty)

class JK_OT_ARD_Bake_Retarget_Actions(bpy.types.Operator):
    """Bakes actions from offsets. (if the offset and/or action are not hidden)"""
    bl_idname = "jk.bake_retarget_actions"
    bl_label = "Bake Action"
    bl_options = {'REGISTER', 'UNDO'}

    bake_mode: EnumProperty(name="Bake Mode", description="The method used to bake retargeted actions",
        items=[('SINGLE', "Single", "Quick bake single action"),
            ('ALL', "All", "Bake all offsets to all of their actions"),
            ('OFFSET', "Offset", "Bake all actions of the offset"),
            ('ACTION', "Action", "Bake the active offset to the active action of the offset")],
        default='ALL')

    def execute(self, context):
        source = bpy.context.object
        jk_ard = source.data.jk_ard
        if source.animation_data and source.animation_data.action:
            last_action = source.animation_data.action
        else:
            last_action = None
        # if we are doing a quick single bake...
        if self.bake_mode == 'SINGLE':
            # get the target action...
            t_action = jk_ard.target.animation_data.action
            # if needed, create animation data...
            if not source.animation_data:
                source.animation_data_create()
            # if the source has an action...
            if source.animation_data.action:
                # copy it so it can be overwritten...
                s_action = source.animation_data.action.copy()
            else:
                # otherwise create one...
                s_action = bpy.data.actions.new(t_action.name)
            # and set the action to be active and use a fake user then bake...
            s_action.use_fake_user = True    
            source.animation_data.action = s_action
            bpy.ops.nla.bake(frame_start=t_action.frame_range[0], frame_end=t_action.frame_range[1], 
                step=jk_ard.bake_step, only_selected=jk_ard.only_selected, 
                visual_keying=True, clear_constraints=False, clear_parents=False, use_current_action=True, bake_types={'POSE'})
        # if we are multi baking everything...
        elif self.bake_mode == 'ALL':
            # for every offset...
            for offset in jk_ard.offsets:
                # if we are baking it...
                if offset.Use:
                    # for its offset actions... (enumerated)
                    for i, offset_action in enumerate(offset.actions):
                        # if we are baking it...
                        if offset_action.Use:
                            # copy the offset action and set it to be active...
                            copy = offset.action.copy()
                            copy.use_fake_user = True
                            source.animation_data.action = copy
                            # set the offset action to be active and bake...
                            offset.active = i
                            bpy.ops.nla.bake(frame_start=offset_action.action.frame_range[0], frame_end=offset_action.action.frame_range[1], 
                                step=offset_action.bake_step, only_selected=jk_ard.only_selected, 
                                visual_keying=True, clear_constraints=False, clear_parents=False, use_current_action=True, bake_types={'POSE'})
        # else if we are multi baking an offset...
        elif self.bake_mode == 'OFFSET':
            # get the active offset...
            offset = jk_ard.offsets[jk_ard.offset]
            # for its offset actions... (enumerated)
            for i, offset_action in enumerate(offset.actions):
                if offset_action.Use:
                    # copy the offset action and set it to be active...
                    copy = offset.action.copy()
                    copy.use_fake_user = True
                    source.animation_data.action = copy
                    # set the offset action to be active and bake... (will trigger update and make it active on the target)
                    offset.active = i
                    bpy.ops.nla.bake(frame_start=offset_action.action.frame_range[0], frame_end=offset_action.action.frame_range[1], 
                        step=offset_action.bake_step, only_selected=jk_ard.only_selected, 
                        visual_keying=True, clear_constraints=False, clear_parents=False, use_current_action=True, bake_types={'POSE'})
        # else if we are single baking from multi bake setup...
        elif self.bake_mode == 'ACTION':
            # get the active offset and its active action and bake...
            offset = jk_ard.offsets[jk_ard.offset]
            offset_action = offset.actions[offset.active]
            # copy the offset action and set it to be active...
            copy = offset.action.copy()
            copy.use_fake_user = True
            source.animation_data.action = copy
            bpy.ops.nla.bake(frame_start=offset_action.action.frame_range[0], frame_end=offset_action.action.frame_range[1], 
                step=offset_action.bake_step, only_selected=jk_ard.only_selected, 
                visual_keying=True, clear_constraints=False, clear_parents=False, use_current_action=True, bake_types={'POSE'})
        # if we want to stay bound to target after baking...
        if jk_ard.stay_bound:
            if last_action != None:
                source.animation_data.action = last_action
            #else: what should happen here...
        else:
            # otherwise set the target to None to remove all the bindings...
            jk_ard.binding, jk_ard.target = "", None
        return {'FINISHED'}

class JK_OT_ARD_Add_Action_Slot(bpy.types.Operator):
    """Adds an action slot"""
    bl_idname = "jk.add_action_slot"
    bl_label = "Add Action"
    bl_options = {'REGISTER', 'UNDO'}
    
    is_offset: BoolProperty(name="is offset", description="is this an offset action slot",
        default=False, options=set())
    
    use_all: BoolProperty(name="All Actions", description="Add all the targets possible actions to this offsets target action slots",
        default=False, options=set())
    
    def execute(self, context):
        source = bpy.context.object
        jk_ard = source.data.jk_ard
        target = jk_ard.target
        if self.is_offset:
            new_offset = jk_ard.offsets.add()
            new_offset.armature = source
        elif self.use_all:
            offset = jk_ard.offsets[jk_ard.offset]
            actions = [a for a in bpy.data.actions if any(b.name in fc.data_path for b in target.data.bones for fc in a.fcurves)]
            for action in actions:
                new_action = offset.actions.add()
                new_action.armature = target
                new_action.action = action
        else:
            offset = jk_ard.offsets[jk_ard.offset]
            new_action = offset.actions.add()
            new_action.armature = target
        return {'FINISHED'}

class JK_OT_ARD_Remove_Action_Slot(bpy.types.Operator):
    """Removes this action from the list"""
    bl_idname = "jk.remove_action_slot"
    bl_label = "Remove Action"
    bl_options = {'REGISTER', 'UNDO'}
    
    is_offset: BoolProperty(name="is offset", description="is this an offset action slot",
        default=False, options=set())
    
    def execute(self, context):
        source = bpy.context.object
        jk_ard = source.data.jk_ard
        if self.is_offset:
            jk_ard.offsets.remove(jk_ard.offset)
        else:
            jk_ard.offsets[jk_ard.offset].actions.remove(jk_ard.offsets[jk_ard.offset].active)
        return {'FINISHED'}

class JK_OT_ARD_Edit_Binding(bpy.types.Operator):
    """Add/remove this collection of bindings"""
    bl_idname = "jk.edit_binding"
    bl_label = "Edit Binding"
    bl_options = {'REGISTER', 'UNDO'}

    edit: EnumProperty(name="Edit", description="",
        items=[('ADD', 'Add', ""), ('REMOVE', 'Remove', ""),
            ('SAVE', 'Save', ""), ('LOAD', 'Load', "")],
        default='ADD')

    name: StringProperty(name="Name", default="", description="Name of the new binding")
    
    def execute(self, context):
        armature = bpy.context.object
        jk_ard = armature.data.jk_ard
        if self.edit == 'ADD':
            if self.name not in jk_ard.bindings:
                binding = jk_ard.bindings.add()
                if armature.mode != 'POSE':
                    bpy.ops.object.mode_set(mode='POSE')
                _functions_.get_binding(armature, binding)
                binding.name = self.name
                jk_ard.binding = self.name
            else:
                print("Binding name already exists!")
        elif self.edit == 'REMOVE':
            if self.name in jk_ard.bindings:
                b_index = jk_ard.bindings.find(self.name)
                jk_ard.bindings.remove(b_index)
                jk_ard.binding = ""
        elif self.edit == 'SAVE':
            if self.name not in jk_ard.bindings:
                binding = jk_ard.bindings[self.name]
                _functions_.get_binding(armature, binding)
            else:
                print("Binding does not exist!")
        elif self.edit == 'LOAD':
            binding = jk_ard.bindings[jk_ard.binding]
            _functions_.Set_binding(armature, binding)
        return {'FINISHED'}
    
    def invoke(self, context, event):
        wm = context.window_manager
        armature = bpy.context.object
        jk_ard = armature.data.jk_ard
        if self.edit == 'REMOVE':
            self.name = jk_ard.binding
        elif len(jk_ard.bindings) == 0:
            self.name = "Default"
        else:
            self.name = ""
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        armature = bpy.context.object
        jk_ard = armature.data.jk_ard
        layout = self.layout
        if self.edit == 'ADD':
            layout.prop(self, "name")
            if self.name in jk_ard.bindings:
                layout.label(text="There is already a binding with this name!", icon='ERROR')
        elif self.edit == 'REMOVE':
            layout.prop_search(self, "name", jk_ard, "bindings", text="Binding")
            if self.name not in jk_ard.bindings:
                layout.label(text="There is no binding with this name!", icon='ERROR')

class JK_OT_ARD_Auto_Offset(bpy.types.Operator):
    """Automatically calculates transform offsets"""
    bl_idname = "jk.auto_offset"
    bl_label = "Auto Offset"
    bl_options = {'REGISTER', 'UNDO'}

    Auto: EnumProperty(name="Auto", description="",
        items=[('LOCATION', 'Location', ""), ('ROTATION', 'Rotation', ""), ('SCALE', 'Scale', ""), ('POLE', 'Pole', "")],
        default='LOCATION')

    Bone: StringProperty(name="Bone", default="", description="Name of bone we are calulating on")

    target: StringProperty(name="Target", default="", description="Name of target bone we are calulating to")

    def execute(self, context):
        armature = bpy.context.object
        jk_ard = armature.data.jk_ard
        p_bone = armature.pose.bones[self.Bone]
        # get the current loc rot and scale...
        pb_loc = p_bone.location[:]
        last_rot_mode = p_bone.rotation_mode
        # easier to calulate for only one rotation mode...
        if p_bone.rotation_mode != 'QUATERNION':
            p_bone.rotation_mode = 'QUATERNION'
        pb_rot = p_bone.rotation_quaternion[:]
        pb_sca = p_bone.scale[:]
        if self.Auto == 'LOCATION':
            # clear the location and update view layer...
            p_bone.location = [0.0, 0.0, 0.0]
            bpy.context.view_layer.update()
            # then set the matrix to itself? (no idea why this works)
            p_bone.matrix = p_bone.matrix
            # negate the location we get from that...
            p_bone.location.negate()
            # and set the rotation and scale back incase they changed...
            p_bone.rotation_quaternion = pb_rot
            p_bone.scale = pb_sca
        elif self.Auto == 'ROTATION':
            # clear the rotation and update view layer...
            p_bone.rotation_quaternion = [1, 0.0, 0.0, 0.0]
            bpy.context.view_layer.update()
            # then set the matrix to itself? (no idea why this works)
            p_bone.matrix = p_bone.matrix
            # invert the new rotation...
            p_bone.rotation_quaternion.invert()
            # and set loc and scale back in case they changed...
            p_bone.location = pb_loc
            p_bone.scale = pb_sca
        elif self.Auto == 'SCALE':
            # doing the scale is so much simpler...
            t_bone = jk_ard.target.pose.bones[self.target]
            p_bone.scale = p_bone.scale * (t_bone.length / p_bone.length)
        
        # change the rotation mode back if it got changed...
        if p_bone.rotation_mode != last_rot_mode:
            p_bone.rotation_mode = last_rot_mode
        return {'FINISHED'}