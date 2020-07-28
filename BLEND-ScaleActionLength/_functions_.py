import bpy

# adds operator to menu...
def Add_To_Menu(self, context):
    self.layout.operator("jk.switch_transform_space", text="Switch Transform Space")

def Scale_By_Framerate(action, fps_from, fps_to, offset, selected):
    if selected:
        # iterate over the fcurves... (we don't have access to selected_keyframes?)
        for fcurve in action.fcurves:
            # make sure the keys are in chronological order... (this is important)
            fcurve.update()
            # get our selection...
            selected_keys = [key for key in fcurve.keyframe_points if key.select_control_point]
            # we need the start and end frames...
            #start_frame = selected_keys[0].co[0]
            end_frame = selected_keys[-1].co[0]
            # then check every key...
            for key in fcurve.keyframe_points:
                # if the keyframe comes after the end frame of the selection...
                if key.co[0] > end_frame:
                    # we need to shift it along by the amount we are scaling the selected keys by...
                    addition = (end_frame - offset) * (fps_to / fps_from)
                    key.co[0] = key.co[0] + addition
                    key.handle_left[0] = key.handle_left[0] + addition
                    key.handle_right[0] = key.handle_right[0] + addition
                elif key.co[0] < start_frame:
                    print("Pre-Frame")
                else:
                    (key.co[0] - offset) * (fps_to / fps_from)
                    key.co[0] = key.co[0] + addition
                    key.handle_left[0] = key.handle_left[0] + addition
                    key.handle_right[0] = key.handle_right[0] + addition

    # switch to the dope sheet...
    last_area = bpy.context.area.type
    bpy.context.area.type = 'DOPESHEET_EDITOR'
    # set the ui_mode...
    last_ui_mode = bpy.context.space_data.ui_mode
    bpy.context.space_data.ui_mode = 'ACTION'
    # set the auto snapping...
    last_auto_snap = bpy.context.space_data.auto_snap
    bpy.context.space_data.auto_snap = 'NONE'
    # set the current frame to the first frame of the animation...
    last_current_frame = bpy.context.scene.frame_current
    bpy.context.scene.frame_current = action.frame_range[0]
    # select all the keys...
    bpy.ops.action.select_all(action='SELECT')
    # scale the keyframes by fps_to divided by fps_from...
    bpy.ops.transform.transform(mode='TIME_SCALE', value=(fps_to / fps_from, 0, 0, 0), orient_axis='X', orient_type='VIEW', 
        orient_matrix=((-1, -0, -0), (-0, -1, -0), (-0, -0, -1)), orient_matrix_type='VIEW', mirror=True, 
        use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, 
        use_proportional_connected=False, use_proportional_projected=False)
    # return the area back to what it was...
    bpy.context.scene.frame_current = last_current_frame
    bpy.context.space_data.auto_snap = last_auto_snap
    bpy.context.space_data.ui_mode = last_ui_mode
    bpy.context.area.type = last_area
   

def Scale_By_Length(action, fps, offset, seconds, selection):
    # switch to the dope sheet...
    last_area = bpy.context.area.type
    bpy.context.area.type = 'DOPESHEET_EDITOR'
    # set the ui_mode...
    last_ui_mode = bpy.context.space_data.ui_mode
    bpy.context.space_data.ui_mode = 'ACTION'
    # set the auto snapping...
    last_auto_snap = bpy.context.space_data.auto_snap
    bpy.context.space_data.auto_snap = 'NONE'
    # set the current frame to the first frame of the animation...
    last_current_frame = bpy.context.scene.frame_current
    bpy.context.scene.frame_current = action.frame_range[0]
    # select all the keys...
    bpy.ops.action.select_all(action='SELECT')
    # divide desired length by old length to get scaling value...
    scaling = (fps * seconds) / (action.frame_range[1] - action.frame_range[0])
    # scale the keyframes by...
    bpy.ops.transform.transform(mode='TIME_SCALE', value=(scaling, 0, 0, 0), orient_axis='X', orient_type='VIEW', 
        orient_matrix=((-1, -0, -0), (-0, -1, -0), (-0, -0, -1)), orient_matrix_type='VIEW', mirror=True, 
        use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, 
        use_proportional_connected=False, use_proportional_projected=False)
    # return the area back to what it was...
    bpy.context.scene.frame_current = last_current_frame
    bpy.context.space_data.auto_snap = last_auto_snap
    bpy.context.space_data.ui_mode = last_ui_mode
    bpy.context.area.type = last_area
    # set the render fps to what it was before importing...
    #bpy.context.scene.render.fps = self.Start