import bpy
from . import _functions_
from bpy.props import (EnumProperty, BoolProperty, StringProperty, PointerProperty, IntProperty)

class JK_OT_Bake_Retarget_Actions(bpy.types.Operator):
    """Bakes actions from offsets. (if the offset and/or action are not hidden)"""
    bl_idname = "jk.bake_retarget_actions"
    bl_label = "Bake Action"

    Bake_mode: EnumProperty(name="Bake Mode", description="The method used to bake retargeted actions",
        items=[('SINGLE', "Single", "Quick bake single action"),
            ('ALL', "All", "Bake all offsets to all of their actions"),
            ('OFFSET', "Offset", "Bake all actions of the offset"),
            ('ACTION', "Action", "Bake the active offset to the active action of the offset")],
        default='ALL')

    def execute(self, context):
        source = bpy.context.object
        AAR = source.data.AAR
        if source.animation_data and source.animation_data.action:
            last_action = source.animation_data.action
        else:
            last_action = None
        # if we are doing a quick single bake...
        if self.Bake_mode == 'SINGLE':
            # get the target action...
            t_action = AAR.Target.animation_data.action
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
                step=AAR.Bake_step, only_selected=AAR.Only_selected, 
                visual_keying=True, clear_constraints=False, clear_parents=False, use_current_action=True, bake_types={'POSE'})
        # if we are multi baking everything...
        elif self.Bake_mode == 'ALL':
            # for every offset...
            for offset in AAR.Offsets:
                # if we are baking it...
                if offset.Use:
                    # for its offset actions... (enumerated)
                    for i, offset_action in enumerate(offset.Actions):
                        # if we are baking it...
                        if offset_action.Use:
                            # copy the offset action and set it to be active...
                            copy = offset.Action.copy()
                            copy.use_fake_user = True
                            source.animation_data.action = copy
                            # set the offset action to be active and bake...
                            offset.Active = i
                            bpy.ops.nla.bake(frame_start=offset_action.Action.frame_range[0], frame_end=offset_action.Action.frame_range[1], 
                                step=offset_action.Bake_step, only_selected=AAR.Only_selected, 
                                visual_keying=True, clear_constraints=False, clear_parents=False, use_current_action=True, bake_types={'POSE'})
        # else if we are multi baking an offset...
        elif self.Bake_mode == 'OFFSET':
            # get the active offset...
            offset = AAR.Offsets[AAR.Offset]
            # for its offset actions... (enumerated)
            for i, offset_action in enumerate(offset.Actions):
                if offset_action.Use:
                    # copy the offset action and set it to be active...
                    copy = offset.Action.copy()
                    copy.use_fake_user = True
                    source.animation_data.action = copy
                    # set the offset action to be active and bake... (will trigger update and make it active on the target)
                    offset.Active = i
                    bpy.ops.nla.bake(frame_start=offset_action.Action.frame_range[0], frame_end=offset_action.Action.frame_range[1], 
                        step=offset_action.Bake_step, only_selected=AAR.Only_selected, 
                        visual_keying=True, clear_constraints=False, clear_parents=False, use_current_action=True, bake_types={'POSE'})
        # else if we are single baking from multi bake setup...
        elif self.Bake_mode == 'ACTION':
            # get the active offset and its active action and bake...
            offset = AAR.Offsets[AAR.Offset]
            offset_action = offset.Actions[offset.Active]
            # copy the offset action and set it to be active...
            copy = offset.Action.copy()
            copy.use_fake_user = True
            source.animation_data.action = copy
            bpy.ops.nla.bake(frame_start=offset_action.Action.frame_range[0], frame_end=offset_action.Action.frame_range[1], 
                step=offset_action.Bake_step, only_selected=AAR.Only_selected, 
                visual_keying=True, clear_constraints=False, clear_parents=False, use_current_action=True, bake_types={'POSE'})
        # if we want to stay bound to target after baking...
        if AAR.Stay_bound:
            if last_action != None:
                source.animation_data.action = last_action
            #else: what should happen here...
        else:
            # otherwise set the target to None to remove all the bindings...
            AAR.Binding, AAR.Target = "", None
        return {'FINISHED'}

class JK_OT_Add_Action_Slot(bpy.types.Operator):
    """Adds an action slot"""
    bl_idname = "jk.add_action_slot"
    bl_label = "Add Action"
    
    Is_offset: BoolProperty(name="Is Offset", description="Is this an offset action slot",
        default=False, options=set())
    
    All: BoolProperty(name="All Actions", description="Add all the targets possible actions to this offsets target action slots",
        default=False, options=set())
    
    def execute(self, context):
        source = bpy.context.object
        AAR = source.data.AAR
        target = AAR.Target
        if self.Is_offset:
            new_offset = AAR.Offsets.add()
            new_offset.Armature = source.data
        elif self.All:
            offset = AAR.Offsets[AAR.Offset]
            actions = [a for a in bpy.data.actions if any(b.name in fc.data_path for b in target.data.bones for fc in a.fcurves)]
            for action in actions:
                new_action = offset.Actions.add()
                new_action.Armature = target.data
                new_action.Action = action
        else:
            offset = AAR.Offsets[AAR.Offset]
            new_action = offset.Actions.add()
            new_action.Armature = target.data
        return {'FINISHED'}

class JK_OT_Remove_Action_Slot(bpy.types.Operator):
    """Removes this action from the list"""
    bl_idname = "jk.remove_action_slot"
    bl_label = "Remove Action"
    
    Is_offset: BoolProperty(name="Is Offset", description="Is this an offset action slot",
        default=False, options=set())
    
    def execute(self, context):
        source = bpy.context.object
        AAR = source.data.AAR
        if self.Is_offset:
            AAR.Offsets.remove(AAR.Offset)
        else:
            AAR.Offsets[AAR.Offset].Actions.remove(AAR.Offsets[AAR.Offset].Active)
        return {'FINISHED'}

class JK_OT_Edit_Binding(bpy.types.Operator):
    """Add/remove this collection of bindings"""
    bl_idname = "jk.edit_binding"
    bl_label = "Edit Binding"

    Edit: EnumProperty(name="Edit", description="",
        items=[('ADD', 'Add', ""), ('REMOVE', 'Remove', ""),
            ('SAVE', 'Save', ""), ('LOAD', 'Load', "")],
        default='ADD')

    Name: StringProperty(name="Name", default="", description="Name of the new binding")
    
    def execute(self, context):
        armature = bpy.context.object
        AAR = armature.data.AAR
        if self.Edit == 'ADD':
            if self.Name not in AAR.Bindings:
                binding = AAR.Bindings.add()
                if armature.mode != 'POSE':
                    bpy.ops.object.mode_set(mode='POSE')
                _functions_.Get_Binding(armature, binding)
                binding.name = self.Name
                AAR.Binding = self.Name
            else:
                print("Binding name already exists!")
        elif self.Edit == 'REMOVE':
            if self.Name in AAR.Bindings:
                b_index = AAR.Bindings.find(self.Name)
                AAR.Bindings.remove(b_index)
                AAR.Binding = ""
        elif self.Edit == 'SAVE':
            if self.Name not in AAR.Bindings:
                binding = AAR.Bindings[self.Name]
                _functions_.Get_Binding(armature, binding)
            else:
                print("Binding does not exists!")
        elif self.Edit == 'LOAD':
            binding = AAR.Bindings[AAR.Binding]
            _functions_.Set_Binding(armature, binding)
        return {'FINISHED'}
    
    def invoke(self, context, event):
        wm = context.window_manager
        armature = bpy.context.object
        AAR = armature.data.AAR
        if self.Edit == 'REMOVE':
            self.Name = AAR.Binding
        elif len(AAR.Bindings) == 0:
            self.Name = "Default"
        else:
            self.Name = ""
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        armature = bpy.context.object
        AAR = armature.data.AAR
        layout = self.layout
        if self.Edit == 'ADD':
            layout.prop(self, "Name")
            if self.Name in AAR.Bindings:
                layout.label(text="There is already a binding with this name!", icon='ERROR')
        elif self.Edit == 'REMOVE':
            layout.prop_search(self, "Name", AAR, "Bindings", text="Binding")
            if self.Name not in AAR.Bindings:
                layout.label(text="There is no binding with this name!", icon='ERROR')

class JK_OT_Auto_Offset(bpy.types.Operator):
    """Automatically calculates transform offsets"""
    bl_idname = "jk.auto_offset"
    bl_label = "Auto Offset"

    Auto: EnumProperty(name="Auto", description="",
        items=[('LOCATION', 'Location', ""), ('ROTATION', 'Rotation', ""), ('SCALE', 'Scale', ""), ('POLE', 'Pole', "")],
        default='LOCATION')

    Bone: StringProperty(name="Bone", default="", description="Name of bone we are calulating on")

    Target: StringProperty(name="Target", default="", description="Name of target bone we are calulating to")

    def execute(self, context):
        armature = bpy.context.object
        AAR = armature.data.AAR
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
            t_bone = AAR.Target.pose.bones[self.Target]
            p_bone.scale = p_bone.scale * (t_bone.length / p_bone.length)
        
        # change the rotation mode back if it got changed...
        if p_bone.rotation_mode != last_rot_mode:
            p_bone.rotation_mode = last_rot_mode
        return {'FINISHED'}