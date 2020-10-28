import bpy
import json
from bpy.props import (BoolProperty, StringProperty, EnumProperty, FloatProperty, FloatVectorProperty, IntProperty, IntVectorProperty, CollectionProperty, PointerProperty) 
from . import _functions_

# this is most settings in the armature that we require to set things back and forth... (i have removed many settings that rarely if ever get used)
Grouping = {
    # all the object settings we might want...
    'Object' : {
        'Transform' : ['location', 'rotation_euler', 'rotation_quaternion', 'rotation_axis_angle', 'rotation_mode', 'scale', 
            'delta_location', 'delta_rotation_quaternion', 'delta_rotation_euler', 'delta_scale'],
        'Relations' : ['parent', 'parent_type', 'parent_bone', 'track_axis', 'up_axis', 'pass_index'], 
        'Instancing': ['instance_type', 'show_instancer_for_viewport', 'show_instancer_for_render', 
            'use_instance_vertices_rotation', 'use_instance_faces_scale', 'instance_faces_scale'], 
        'Display' : ['show_name', 'show_axis', 'show_in_front', 'show_axis', 'display_type', 'show_bounds', 'display_bounds_type']},
    # all the object data settings we might want... (pose and animation settings added here for convienience)
    'Data' : {
        'Skeleton' : ['pose_position', 'layers', 'layers_protected'],
        'Pose' : ['bone_groups', 'pose_library', 'ik_solver', 'ik_param'],
        'Animation' : ['action', 'use_nla', 'nla_tracks'],
        'Display' : ['display_type', 'show_names', 'show_bone_custom_shapes', 'show_axes', 'show_group_colors']},
    # all the edit bone settings we might want... (used per bone)
    'Edit Bone' : {
        'Transform' : ['head', 'tail', 'roll', 'lock'],
        'Bendy Bones' : ['bbone_segments', 'bbone_x', 'bbone_z', 'bbone_handle_type_start', 'bbone_custom_handle_start', 
            'bbone_handle_type_end', 'bbone_custom_handle_end', 'bbone_rollin', 'bbone_rollout', 'use_endroll_as_inroll',
            'bbone_curveinx', 'bbone_curveiny', 'bbone_curveoutx', 'bbone_curveouty', 'bbone_easein', 
            'bbone_easeout', 'bbone_scaleinx', 'bbone_scaleiny', 'bbone_scaleoutx', 'bbone_scaleouty'],
        'Relations' : ['parent', 'layers', 'use_connect', 'use_inherit_rotation', 'inherit_scale'],
        'Deform' : ['use_deform', 'envelope_distance', 'envelope_weight', 'use_envelope_multiply', 'head_radius', 'tail_radius']},
    # all the pose bone settings we might want... (used per bone)
    'Pose Bone' : {
        'Posing' : ['location', 'lock_location', 'rotation_mode', 'rotation_quaternion', 'rotation_euler', 
            'rotation_axis_angle', 'lock_rotation_w', 'lock_rotation', 'scale', 'lock_scale'],
        'Rigging' : ['constraints', 'drivers', 'bone_group'],
        'IK Settings' : ['lock_ik_x', 'lock_ik_y', 'lock_ik_z', 'use_ik_limit_x', 'use_ik_limit_y', 'use_ik_limit_z', 
            'use_ik_rotation_control', 'use_ik_linear_control','ik_min_x', 'ik_max_x', 'ik_min_y', 'ik_max_y', 'ik_min_z', 'ik_max_z', 
            'ik_stiffness_x', 'ik_stiffness_y', 'ik_stiffness_z', 'ik_stretch', 'ik_rotation_weight', 'ik_linear_weight'],
        'Display' : ['custom_shape', 'custom_shape_scale', 'use_custom_shape_bone_size', 'custom_shape_transform']},
    }

Pathing = {'Object' : "bpy.data.objects", 'Armature' : "bpy.data.armatures", 'Action' : "bpy.data.actions", 
    'Curve' : "bpy.data.curves", 'Edit Bone' : "bpy.context.object.data.edit_bones", 'Bone Group' : "bpy.context.object.pose.bone_groups"}

class JK_AES_Inherit(bpy.types.PropertyGroup):

    Type: EnumProperty(name="Type", description="Type of property this boolean references",
        items=[('BOOLEAN', "Boolean", ""), ('BOOLEAN_VECTOR', "Boolean Vector", ""), 
            ('INTEGER', "Integer", ""), ('INTEGER_VECTOR', "Integer Vector", ""), 
            ('FLOAT', "Float", ""), ('FLOAT_VECTOR', "Float Vector", ""),
            ('POINTER', "Pointer", ""), ('COLLECTION', "Collection", "")],
        default='BOOLEAN')

    Path: StringProperty(name="Path", description="Path to this property. (if it's a pointer)", default="")
    
    Inherit: BoolProperty(name="Inherit", description="Inherit this property value from parent stage",
        default=True, options=set())

class JK_AES_Inherit_Group(bpy.types.PropertyGroup):
    
    Inherit: BoolProperty(name="Inherit", description="Enable inheritance of this grouping",
        default=False, options=set())

    Inheritance: CollectionProperty(type=JK_AES_Inherit)

class JK_AES_Inherit_Group_Bone(bpy.types.PropertyGroup):

    # collected edit bone inheritance...
    def Update_Edit_Bone_Inherit(self, context):
        if self.Edit_inherit:
            for group, props in Grouping['Edit Bone'].items():
                eb_grp = self.Edit_groups.add()
                eb_grp.name = group
                for prop in props:
                    prop_iht = eb_grp.Inheritance.add()
                    prop_iht.name = prop
        else:
            self.Edit_groups.clear()

    Edit_inherit: BoolProperty(name="Pull Edit Bone", description="Inherit per bone edit mode settings from parent stage. (Head, Tail, Roll, etc)",
        default=False, options=set(), update=Update_Edit_Bone_Inherit)
    
    Edit_groups: CollectionProperty(type=JK_AES_Inherit_Group)

    Edit_json: StringProperty(name="Edit Bone Dictionary")

    # collected pose bone inheritance settings...
    def Update_Pose_Bone_Inherit(self, context):
        if self.Pose_inherit:
            for group, props in Grouping['Pose Bone'].items():
                pb_grp = self.Pose_groups.add()
                pb_grp.name = group
                for prop in props:
                    prop_iht = pb_grp.Inheritance.add()
                    prop_iht.name = prop
        else:
            self.Pose_groups.clear()

    Pose_inherit: BoolProperty(name="Pull Pose Bones", description="Inherit per bone pose mode settings from parent stage. (Constraints, Drivers, etc)",
        default=False, options=set(), update=Update_Pose_Bone_Inherit)
    
    Pose_groups: CollectionProperty(type=JK_AES_Inherit_Group)

    Pose_json: StringProperty(name="Pose Bone Dictionary")

class JK_AES_Stage_Props(bpy.types.PropertyGroup):

    Armature: StringProperty(name="Armature", description="Armature that defines this stage", 
        default="", maxlen=1024)

    Is_source: BoolProperty(name="Is Source", description="This is the source armature, there can only be one",
        default=False, options=set())

    Show_details: BoolProperty(name="Show details", description="Show pull settings for this stage",
        default=False, options=set())
    
    Parent: StringProperty(name="Parent Stage", description="The stage before this one", 
        default="", maxlen=1024)

    # object inheritance...
    def Update_Object_Inherit(self, context):
        if self.Object_inherit:
            for group, props in Grouping['Object'].items():
                obj_grp = self.Object_groups.add()
                obj_grp.name = group
                for prop in props:
                    prop_iht = obj_grp.Inheritance.add()
                    prop_iht.name = prop
        else:
            self.Object_groups.clear()

    Object_inherit: BoolProperty(name="Pull Object", description="Inherit object settings from parent stage. (NLA Strips, Pose Mode, Transforms, etc)",
        default=False, options=set(), update=Update_Object_Inherit)

    Object_groups: CollectionProperty(type=JK_AES_Inherit_Group)

    Object_json: StringProperty(name="Object Dictionary")
    
    # data inheritance...
    def Update_Data_Inherit(self, context):
        if self.Data_inherit:
            for group, props in Grouping['Data'].items():
                dat_grp = self.Data_groups.add()
                dat_grp.name = group
                for prop in props:
                    prop_iht = dat_grp.Inheritance.add()
                    prop_iht.name = prop
        else:
            self.Data_groups.clear()

    Data_inherit: BoolProperty(name="Pull Data", description="Inherit data settings from parent stage. (Layers, Bone Groups, etc)",
        default=False, options=set(), update=Update_Data_Inherit)

    Data_groups: CollectionProperty(type=JK_AES_Inherit_Group)

    Data_json: StringProperty(name="Data Dictionary")
    
    # bone inheritance...
    Bones_inherit: BoolProperty(name="Pull Bones", description="Inherit per bone edit mode settings from parent stage. (Head, Tail, Roll, etc)",
        default=False, options=set())

    Bones: CollectionProperty(type=JK_AES_Inherit_Group_Bone)

    # addon data that might need saving per stage...
    Addon_json: StringProperty(name="Addon Dictionary")

class JK_AES_Armature_Props(bpy.types.PropertyGroup):

    def Update_Stage(self, context):
        armature = bpy.context.object
        # lets not do anything silly like run a heap of code when we don't need to...
        if self.Stage != self.Last:
            last_mode = armature.mode
            if last_mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            # save the properties of the current stage
            _functions_.Get_Stage_Properties(armature, self.Stages[self.Last])
            # the pull the inheritance hierarchy to the stage we are going to...
            _functions_.Pull_Hierarchy_Inheritance(armature, self.Stages[self.Stage])
            # then set the armature to the stage we are going to...
            _functions_.Set_Stage_Properties(armature, self.Stages[self.Stage])
            # set the last stage to the new stage...
            self.Last = self.Stage
            # and return the mode if we need to...
            if armature.mode != last_mode:
                bpy.ops.object.mode_set(mode=last_mode)
                
    Last: StringProperty(name="Last", description="The stage we are coming from", 
        default="", maxlen=1024)
    
    Stage: StringProperty(name="Stage", description="The stage we are on", 
        default="", maxlen=1024, update=Update_Stage, options={'ANIMATABLE'})
    
    Stages: CollectionProperty(type=JK_AES_Stage_Props, options=set())