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
        # if we are multi baking everything...
        if self.Bake_mode == 'ALL':
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
                                step=offset_action.Bake_step, only_selected=offset_action.Selected, 
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
                        step=offset_action.Bake_step, only_selected=offset_action.Selected, 
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
                step=offset_action.Bake_step, only_selected=offset_action.Selected, 
                visual_keying=True, clear_constraints=False, clear_parents=False, use_current_action=True, bake_types={'POSE'})
        # set the target to None to remove all the bindings...
        AAR.Target = None
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
    bl_label = "Remove Action"

    Edit: EnumProperty(name="Edit", description="",
        items=[('ADD', 'Add', ""), ('REMOVE', 'Remove', ""),
            ('SAVE', 'Save', ""), ('LOAD', 'Load', "")],
        default='ADD')

    def execute(self, context):
        armature = bpy.context.object
        AAR = armature.data.AAR
        if self.Edit == 'ADD':
            if AAR.Binding not in AAR.Bindings:
                binding = AAR.Bindings.add()
                if armature.mode != 'POSE':
                    bpy.ops.object.mode_set(mode='POSE')
                _functions_.Get_Binding(armature, binding)
                binding.name = AAR.Binding
        elif self.Edit == 'REMOVE':
            b_index = AAR.Bindings.find(AAR.Binding)
            AAR.Bindings.remove(b_index)
        return {'FINISHED'}
        