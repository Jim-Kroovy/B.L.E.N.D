import bpy
from bpy.props import (BoolProperty, BoolVectorProperty, StringProperty, EnumProperty, FloatProperty, FloatVectorProperty, IntProperty, IntVectorProperty, CollectionProperty, PointerProperty) 
from . import _functions_

class JK_ARL_Pivot_Bone_Props(bpy.types.PropertyGroup):

    def Update_Pivot(self, context):
        if not (self.id_data == None or self.Is_adding):
            if not self.Is_forced:
                armature = bpy.context.object
                _functions_.Set_Pivot(armature, self, 'UPDATE')

    Is_adding: BoolProperty(name="Is Adding", description="Stops update function on adding", default=True)

    Type: EnumProperty(name="Type", description="The type of pivot bone",
        items=[('SKIP', 'Skip Parent', "Pivot bone is parented to the source bones parents parent"),
        ('SHARE', 'Share Parent', "Pivot bone is parented to the source bones parent")],
        default='SKIP', update=Update_Pivot)

    Source: StringProperty(name="Bone",description="The bone this pivot bone was created from",
        default="", maxlen=1024, update=Update_Pivot)
    
    Is_parent: BoolProperty(name="Is Parent", description="Source bone is parented to the pivot", default=False, update=Update_Pivot)
    
    Is_forced: BoolProperty(name="Is Forced", description="This pivot bone is required by other rigging", default=False)

    Parent: StringProperty(name="Bone",description="The parent of the bone this pivot bone was created from",
        default="", maxlen=1024)

class JK_ARL_Floor_Bone_Props(bpy.types.PropertyGroup):

    def Update_Floor(self, context):
        if not (self.id_data == None or self.Is_adding):
            armature = bpy.context.object
            _functions_.Set_Floor(armature, self, 'UPDATE')

    Is_adding: BoolProperty(name="Is Adding", description="Stops update function on adding", default=True)

    Source: StringProperty(name="Bone",description="The bone this floor target was created for",
        default="", maxlen=1024, update=Update_Floor)

    Parent: StringProperty(name="Parent", description="The parent of the floor target. (if any)", 
        default="", maxlen=1024, update=Update_Floor)

class JK_ARL_Twist_Bone_Props(bpy.types.PropertyGroup):
    
    def Update_Twist(self, context):
        if not (self.id_data == None or self.Is_adding):
            armature = bpy.context.object
            _functions_.Set_Twist(armature, self, 'UPDATE')
        #elif self.id_data == None:
            #_functions_.Update_Twist_Operator(self, context)

    Is_adding: BoolProperty(name="Is Adding", description="Stops update function on adding", default=True)

    Type: EnumProperty(name="Type", description="The type of twist bone to add",
        items=[('HEAD_HOLD', 'Head Hold', "Holds deformation at the head of the bone back by tracking to the target. (eg: Upper Arm Twist)"),
        ('TAIL_FOLLOW', 'Tail Follow', "Follows deformation at the tail of the bone by copying the Y rotation of the target. (eg: Lower Arm Twist)")],
        default='HEAD_HOLD', update=Update_Twist)

    Target: StringProperty(name="Target", description="The targets bones name", default="", maxlen=1024, update=Update_Twist)
    
    Parent: StringProperty(name="Parent", description="The original parent of the twist bone. (if any)", default="", maxlen=1024)

    Has_pivot: BoolProperty(name="Use Pivot", description="Does this twist bone have a pivot bone to define its limits?", default=False, update=Update_Twist)

    def Update_Twist_Constraints(self, context):
        if not (self.id_data == None or self.Is_adding):
            armature = bpy.context.object
            tp_bone = armature.pose.bones[self.name]
            if self.Type == 'HEAD_HOLD':
                damp_track = tp_bone.constraints["TWIST - Damped Track"]
                damp_track.subtarget, damp_track.head_tail = self.Target, self.Float
                limit_rot = tp_bone.constraints["TWIST - Limit Rotation"]
                limit_rot.use_limit_x, limit_rot.min_x, limit_rot.max_x = self.Use_x, self.Min_x, self.Max_x
                limit_rot.use_limit_z, limit_rot.min_z, limit_rot.max_z = self.Use_z, self.Min_z, self.Max_z
            elif self.Type == 'TAIL_FOLLOW':
                ik = tp_bone.constraints["TWIST - IK"]
                ik.subtarget, ik.influence = self.Target, self.Float
                tp_bone.use_ik_limit_y, tp_bone.ik_min_y, tp_bone.ik_max_y = self.Use_y, self.Min_y, self.Max_y
    
    Float: FloatProperty(name="Float", description="Either the head vs tail or influence depending on the twist type", 
        default=1.0, min=0.0, max=1.0, subtype='FACTOR', update=Update_Twist_Constraints)

    Use_x: BoolProperty(name="Use X", description="Use X limit", default=False, update=Update_Twist_Constraints)
    Min_x: FloatProperty(name="Min X", description="Minimum X limit", default=0.0, subtype='ANGLE', unit='ROTATION', update=Update_Twist_Constraints)
    Max_x: FloatProperty(name="Max X", description="Maximum X limit", default=0.0, subtype='ANGLE', unit='ROTATION', update=Update_Twist_Constraints)

    Use_y: BoolProperty(name="Use Y", description="Use Y limit", default=False, update=Update_Twist_Constraints)
    Min_y: FloatProperty(name="Min Y", description="Minimum Y limit", default=0.0, subtype='ANGLE', unit='ROTATION', update=Update_Twist_Constraints)
    Max_y: FloatProperty(name="Max Y", description="Maximum Y limit", default=0.0, subtype='ANGLE', unit='ROTATION', update=Update_Twist_Constraints)

    Use_z: BoolProperty(name="Use Z", description="Use Z limit", default=False, update=Update_Twist_Constraints)
    Min_z: FloatProperty(name="Min Z", description="Minimum Z limit", default=0.0, subtype='ANGLE', unit='ROTATION', update=Update_Twist_Constraints)
    Max_z: FloatProperty(name="Max Z", description="Maximum Z limit", default=0.0, subtype='ANGLE', unit='ROTATION', update=Update_Twist_Constraints)

class JK_ARL_Chain_Target_Bone_Props(bpy.types.PropertyGroup):

    def Update_Target_Source(self, context):
        armature = bpy.context.object
        if armature.ARL.Chain < len(armature.ARL.Chains):
            chain = armature.ARL.Chains[armature.ARL.Chain]
            if not (self.id_data == None or chain.Is_adding):
                _functions_.Set_Chain(armature, chain, 'UPDATE')
        #elif self.id_data == None:
            #_functions_.Update_Chain_Operator(chain, context)

    Source: StringProperty(name="Source",description="The bone that we created the target from",
        default="", maxlen=1024, update=Update_Target_Source)

    Target: StringProperty(name="Target", description="The actual target bone. (if parented)",
        default="", maxlen=1024)

    Local: StringProperty(name="Local",description="The local bone that controls the IK chain",
        default="", maxlen=1024)

    Control: StringProperty(name="Control", description="Name of the bone that controls the roll mechanism. (if any)", default="", maxlen=1024)

    Pivot: StringProperty(name="Pivot", description="Name of the bone used to pivot the target. (eg: bone at the ball of the foot)", 
        default="", maxlen=1024, update=Update_Target_Source)

    Root: StringProperty(name="IK Root",description="The IK root bone. (if any)", default="", maxlen=1024)

class JK_ARL_Chain_Pole_Bone_Props(bpy.types.PropertyGroup):

    def Update_Pole(self, context):
        armature = bpy.context.object
        self.Angle = _functions_.Get_Pole_Angle(self.Axis)
        if armature.ARL.Chain < len(armature.ARL.Chains):
            chain = armature.ARL.Chains[armature.ARL.Chain]
            if not (self.id_data == None or chain.Is_adding):
                _functions_.Set_Chain(armature, chain, 'UPDATE')

    Source: StringProperty(name="Source",description="The bone that we created the pole from",
        default="", maxlen=1024)
    
    Local: StringProperty(name="Local Pole",description="The local pole bones name",default="",maxlen=1024)
    
    Axis: EnumProperty(name="Axis", description="The local axis of the second bone that the pole target is created along. (pole angle might need to be adjusted)",
        items=[('X', 'X Axis', "", "CON_LOCLIKE", 0),
        ('X_NEGATIVE', '-X Axis', "", "CON_LOCLIKE", 1),
        ('Z', 'Z Axis', "", "CON_LOCLIKE", 2),
        ('Z_NEGATIVE', '-Z Axis', "", "CON_LOCLIKE", 3)],
        default='X', update=Update_Pole)

    Angle: FloatProperty(name="Angle", description="The angle of the IK pole target. (degrees)", 
        default=0.0,subtype='ANGLE')

    Distance: FloatProperty(name="Distance", description="The distance the pole target is from the IK parent. (meters)", default=0.25, update=Update_Pole)

    Root: StringProperty(name="IK Root", description="The IK root bone. (if any)",default="",maxlen=1024)

class JK_ARL_Chain_Bone_Props(bpy.types.PropertyGroup):

    def Update_Bone(self, context):
        armature = bpy.context.object
        if armature.ARL.Chain < len(armature.ARL.Chains):
            chain = armature.ARL.Chains[armature.ARL.Chain]
            if not (self.id_data == None or chain.Is_adding):
                _functions_.Set_Chain(armature, chain, 'UPDATE')

    Gizmo: StringProperty(name="Gizmo", description="The gizmo bone that the chain bone follows", default="", maxlen=1024)

    Stretch: StringProperty(name="Stretch", description="The stretch bone that the gizmo bone follows", default="", maxlen=1024)

    Is_owner: BoolProperty(name="Is Owner",description="Is this bone the owner of the IK constraint",
        default=False)
    
    Has_target: BoolProperty(name="Has Target",description="Should this chain bone have a target. (Only used by Spline chains)",
        default=False, update=Update_Bone)

    Show_expanded: BoolProperty(name="Show Expanded", description="Show the IK limits and stiffness settings for this chain bone",
        default=False)

class JK_ARL_Chain_Spline_Props(bpy.types.PropertyGroup):

    def Update_Spline(self, context):
        armature = bpy.context.object
        if armature.ARL.Chain < len(armature.ARL.Chains):
            chain = armature.ARL.Chains[armature.ARL.Chain]
            if not (self.id_data == None or chain.Is_adding):
                _functions_.Set_Chain(armature, chain, 'UPDATE')
    
    Use_divisions: BoolProperty(name="Use Divisions", description="Use a subdivsion of targets instead of creating targets from existing bones",
        default=False)
    
    Divisions: IntProperty(name="Divisions", description="The number of divisions in the curve and how many controls to create. (Not including start and end)", 
        default=1, min=1)
    
    Use_start: BoolProperty(name="Use Start",description="Include the start bone in the spline chain",
        default=True, update=Update_Spline)

    Use_end: BoolProperty(name="Use End",description="Include the end bone in the spline chain",
        default=True, update=Update_Spline)

class JK_ARL_Chain_Forward_Props(bpy.types.PropertyGroup):

    def Update_Forward_Constraints(self, context):
        if not (self.id_data == None or self.Is_adding):
            armature = bpy.context.object
            cp_bone = armature.pose.bones[self.name]
            copy_rot = cp_bone.constraints.new('COPY_ROTATION')
            copy_rot.name, copy_rot.show_expanded = "FORWARD - Copy Rotation", False
            # copy_rot.target, copy_rot.subtarget = armature, target.name
            copy_rot.use_x, copy_rot.use_y, copy_rot.use_z = self.Rot[0], self.Rot[1], self.Rot[2]
            copy_rot.target_space, copy_rot.owner_space = 'LOCAL', 'LOCAL'
            copy_rot.mute = True if not any(s == True for s in self.Rot) else False
            copy_loc = cp_bone.constraints.new('COPY_LOCATION')
            copy_loc.name, copy_loc.show_expanded = "FORWARD - Copy Location", False
            # copy_loc.target, copy_loc.subtarget = armature, target.name
            copy_loc.use_x, copy_loc.use_y, copy_loc.use_z = self.Loc[0], self.Loc[1], self.Loc[2]
            copy_loc.target_space, copy_loc.owner_space = 'LOCAL', 'LOCAL'
            copy_loc.mute = True if not any(s == True for s in self.Loc) else False
            copy_sca = cp_bone.constraints.new('COPY_SCALE')
            copy_sca.name, copy_sca.show_expanded = "FORWARD - Copy Scale", False
            #copy_sca.target, copy_sca.subtarget = armature, target.name
            copy_sca.use_x, copy_sca.use_y, copy_sca.use_z = self.Sca[0], self.Sca[1], self.Sca[2]
            copy_sca.target_space, copy_sca.owner_space = 'LOCAL', 'LOCAL'
            copy_sca.mute = True if not any(s == True for s in self.Sca) else False

    Loc: BoolVectorProperty(name="Loc", description="Which axes are copied",
        default=(False, False, False), size=3, subtype='EULER')

    Rot: BoolVectorProperty(name="Rot", description="Which axes are copied",
        default=(False, False, False), size=3, subtype='EULER')

    Sca: BoolVectorProperty(name="Sca", description="Which axes are copied",
        default=(False, False, False), size=3, subtype='EULER')

    #Mute_all: BoolProperty(name="Mute Constraints",description="Switch between IK vs FK for this IK chain",
        #default=False, update=Update_Mute_All)
    
    Target: EnumProperty(name="Target Space", description="Space that target is evaluated in",
        items=[('WORLD', "World Space", ""), ('POSE', "Pose Space", ""), 
            ('LOCAL', "Local Space", ""), ('LOCAL_WITH_PARENT', "Local With Parent Space", "")],
        default='LOCAL')

    Owner: EnumProperty(name="Owner Space", description="Space that owner is evaluated in",
        items=[('WORLD', "World Space", ""), ('POSE', "Pose Space", ""), 
            ('LOCAL', "Local Space", ""), ('LOCAL_WITH_PARENT', "Local With Parent", "")],
        default='LOCAL')

class JK_ARL_Chain_Props(bpy.types.PropertyGroup):

    def Update_Chain(self, context):
        armature = bpy.context.object
        if not (self.id_data == None or self.Is_adding):
            _functions_.Set_Chain(armature, self, 'UPDATE')
        elif self.id_data == None:
            _functions_.Update_Chain_Operator(self, context)

    Is_adding: BoolProperty(name="Is Adding", description="Stops update functions", default=True)
    
    Parent: StringProperty(name="Parent", description="The bone at the beginning but not included in the chain. (if any)", 
        default="", maxlen=1024)

    Owner: StringProperty(name="Owner", description="The owning bone of the chains name", default="", maxlen=1024, update=Update_Chain)

    Length: IntProperty(name="Chain Length", description="How far through its parents should this IK chain run",
        default=2, min=1, update=Update_Chain)

    Type: EnumProperty(name="Type", description="The type of limb IK chain",
        items=[('OPPOSABLE', 'Opposable', "A simple IK chain of 2 bones with a pole target. (Generally used by arms)"),
        ('SCALAR', 'Scalar', "An IK chain of any length controlled by scaling, rotating a parent of the target. (Generally used for fingers)"),
        ('PLANTIGRADE', 'Plantigrade', "An opposable IK chain of 2 bones with a pole target and standard foot rolling controls. (Generally used by human legs)"),
        ('DIGITIGRADE', 'Digitigrade', "A scalar IK chain of 3 bones with a pole target and special foot controls. (Generally used by animal legs)"),
        ('SPLINE', 'Spline', "A spline IK chain of any length controlled by a curve that's manipulated with target bones. (Generally used by tails/spines)"),
        ('FORWARD', 'Forward', "An FK chain of any length where the chain copies loc/rot/scale of a parent/target. (Generally an alternative used for fingers/tails)")],
        default='OPPOSABLE', update=Update_Chain)

    Mode: EnumProperty(name="Mode", description="Which mode of IK is currently active",
        items=[('NONE', 'Only IK', "Only use IK"),
            ('SWITCH', 'Switchable', "IK and FK can be switched between while keyframing"),
            ('AUTO', 'Automatic', "IK and FK are switched automatically depending on bone selection")],
        default='NONE')

    def Update_Detected(self, context):
        armature = bpy.context.object
        if not (self.id_data == None or self.Is_adding):
            _functions_.Set_Chain(armature, self, 'UPDATE')
    
    Side: EnumProperty(name="Side", description="Which side of the armature is this chain on",
        items=[('NONE', 'None', "Not on any side, probably central"),
            ('LEFT', 'Left', "Chain is on the left side"),
            ('RIGHT', 'Right', "Chain is on the right side")],
        default='NONE', update=Update_Detected)

    Limb: EnumProperty(name="Limb", description="What appendage this chain is for. (mostly used for naming and organisation)",
        items=[('ARM', 'Arm', "This is meant to be an arm chain"),
            ('DIGIT', 'Digit', "This is meant to be a digit chain. (Toes, Fingers and Thumbs)"),
            ('LEG', 'Leg', "This is meant to be a leg chain"),
            ('SPINE', 'Spine', "This is meant to be a spine chain"),
            ('TAIL', 'Tail', "This is meant to be a tail chain"),
            ('WING', 'Wing', "This is meant to be a wing chain")],
        default='ARM', update=Update_Detected)

    Last_fk: BoolProperty(name="Last FK",description="The last 'Use FK' boolean",
        default=False)
    
    def Update_Use_FK(self, context):
        if self.Use_fk != self.Last_fk:
            if self.Use_fk:
                _functions_.Set_IK_to_FK(self, self.id_data)
            else:
                _functions_.Set_FK_to_IK(self, self.id_data)       
            self.Last_fk = self.Use_fk
            if self.id_data.ARL.Last_frame == bpy.context.scene.frame_float:
                _functions_.Set_Chain_Keyframe(self, self.id_data.id_data)

    Use_fk: BoolProperty(name="Use FK",description="Switch between IK vs FK for this IK chain",
        default=False, update=Update_Use_FK)

    Auto_fk: BoolProperty(name="Auto Switch", description="Automatically switch between IK and FK depending on bone selection. (Defaults to IK)",
        default=False)
    
    Auto_key: BoolProperty(name="Auto Key Switch",description="Automatically keyframe switching between IK and FK",
        default=False)
    
    Bones: CollectionProperty(type=JK_ARL_Chain_Bone_Props)
    
    Pole: PointerProperty(type=JK_ARL_Chain_Pole_Bone_Props)

    Targets: CollectionProperty(type=JK_ARL_Chain_Target_Bone_Props)

    Spline: PointerProperty(type=JK_ARL_Chain_Spline_Props)

    Forward: CollectionProperty(type=JK_ARL_Chain_Forward_Props)

class JK_ARL_Affix_Props(bpy.types.PropertyGroup):

    Control: StringProperty(name="Control", description="The prefix of control bones. (Uses 'Armature Control Bones' control prefix if it's installed)", 
        default="CB_", maxlen=1024)
    
    Gizmo: StringProperty(name="Gizmo", description="The prefix of hidden bones that are used to indirectly create movement", 
        default="GB_", maxlen=1024)

    Pivot: StringProperty(name="Pivot", description="The prefix of control bones that are used to offset constraints, inherit transforms and rotate around", 
        default="PB_", maxlen=1024)

    Stretch: StringProperty(name="Stretch", description="The affix given to bones that stretch", 
        default="STRETCH_", maxlen=1024)

    Roll: StringProperty(name="Roll", description="The affix given to bones that roll", 
        default="ROLL_", maxlen=1024)
    
    Local: StringProperty(name="Local", description="The affix given to bones that hold local transforms", 
        default="LOCAL_", maxlen=1024)
    
    Target_arm: StringProperty(name="Arm Target", description="The prefix of arm chain targets", 
        default="AT_", maxlen=1024)

    Target_digit: StringProperty(name="Digit Target", description="The prefix of digit chain targets", 
        default="DT_", maxlen=1024)

    Target_leg: StringProperty(name="Arm Target", description="The prefix of leg chain targets", 
        default="LT_", maxlen=1024)

    Target_spine: StringProperty(name="Spine Target", description="The prefix of spline chain targets", 
        default="ST_", maxlen=1024)

    Target_tail: StringProperty(name="Tail Target", description="The prefix of tail chain targets", 
        default="TT_", maxlen=1024)

    Target_wing: StringProperty(name="Wing Target", description="The prefix of wing chain targets", 
        default="WT_", maxlen=1024)

    Target_floor: StringProperty(name="Floor Target", description="The prefix of floor targets", 
        default="FT_", maxlen=1024)

class JK_ARL_Bone_Props(bpy.types.PropertyGroup):

    Type: EnumProperty(name="Type", description="What type of bone is this",
        items=[('NONE', 'None', "Not a rigging bone"),
            ('GIZMO', 'Gizmo', "A gizmo bone"),
            ('PIVOT', 'Pivot', "A pivot bone"),
            ('CHAIN', 'Chain', "A chain bone"),
            ('TARGET', 'Target', "A target bone"),
            ('TWIST', 'Twist', "A twist bone")],
        default='NONE')

    Subtype: EnumProperty(name="Subtype", description="What Subtype of bone is this. (if any)",
        items=[('NONE', 'None', "Has no subtype"),
            ('OFFSET', 'Offset', "An offset bone"),
            ('STRETCH', 'Stretch', "A stretch bone"),
            ('LOCAL', 'Local', "A local bone"),
            ('ROLL', 'Roll', "A roll bone")],
        default='NONE')

    # will need this at some point for smart auto-keying ?
    #Pose_Matrix: FloatVectorProperty(name="Last Matrix", description="Used to tell if we should auto-keyframe things",
        #size=16, subtype='MATRIX')

    def Get_Has_Changes(self):
        if self.name in self.id_data.bones:
            bone = self.id_data.bones[self.name]
            if self.Edit_matrix != bone.matrix_local:
                mat = bone.matrix_local.copy()
                self.Edit_matrix = [mat[j][i] for i in range(len(mat)) for j in range(len(mat))]
                return True
            else:
                return False
        else:
            return False
    
    Has_changes: BoolProperty(name="Has_changes", description="Show/Hide all gizmo bones",
        default=False, get=Get_Has_Changes)
    
    Edit_matrix: FloatVectorProperty(name="Last Matrix", description="Used to tell if we should update the rigging",
        size=16, subtype='MATRIX', precision=6)

class JK_ARL_Armature_Props(bpy.types.PropertyGroup):
    
    def Update_Hide(self, context):
        bools = {'GIZMO' : self.Hide_gizmo, 'PIVOT' : self.Hide_pivot, 
            'CHAIN' : self.Hide_chain, 'TARGET' : self.Hide_target,
            'TWIST' : self.Hide_twist, 'NONE' : self.Hide_none}
        control_bones = True if 'BLEND-ArmatureControlBones' in bpy.context.preferences.addons.keys() else False 
        for b in self.id_data.bones:
            if control_bones:
                if b.ACB.Type in ['CONT', 'NONE']:
                    b.hide = bools[b.ARL.Type]
            else:
                b.hide = bools[b.ARL.Type]

    Hide_gizmo: BoolProperty(name="Hide Gizmos", description="Show/Hide all gizmo bones",
        default=True, update=Update_Hide)

    Hide_pivot: BoolProperty(name="Hide Pivots", description="Show/Hide all pivot bones",
        default=False, update=Update_Hide)

    Hide_chain: BoolProperty(name="Hide Chains", description="Show/Hide all chain bones",
        default=False, update=Update_Hide)

    Hide_target: BoolProperty(name="Hide Targets", description="Show/Hide all target bones",
        default=False, update=Update_Hide)

    Hide_twist: BoolProperty(name="Hide Twists", description="Show/Hide all twist bones",
        default=False, update=Update_Hide)

    Hide_none: BoolProperty(name="Hide Unrigged", description="Show/Hide all unrigged bones",
        default=False, update=Update_Hide)

    def Update_Wire(self, context):
        for bone in self.id_data.bones:
            bone.show_wire = self.Wire_shapes
    
    Wire_shapes: BoolProperty(name="Wireframe Shapes", description="Set all bones to wireframe/solid display",
        default=False, update=Update_Wire)

class JK_ARL_Object_Props(bpy.types.PropertyGroup):
    
    Last_frame: FloatProperty(name="Last Frame", description="Used to determine when we can auto keyframe the chain",
        default=0.0)
    
    def Get_Is_Playing(self):
        return bpy.context.screen.is_animation_playing
    
    Is_playing: BoolProperty(name="Is Playing", description="A protection bool to stop auto switching on play animation",
        get=Get_Is_Playing)

    def Get_Is_Auto_Keying(self):
        return bpy.context.scene.tool_settings.use_keyframe_insert_auto
    
    Is_auto_keying: BoolProperty(name="Is Auto-keying", description="A bool to check if we should be auto-keying",
        get=Get_Is_Auto_Keying)

    Pivot: IntProperty(name='Active', default=0, min=0)

    Pivots: CollectionProperty(type=JK_ARL_Pivot_Bone_Props)

    Floor: IntProperty(name='Active', default=0, min=0)

    Floors: CollectionProperty(type=JK_ARL_Floor_Bone_Props)

    Twist: IntProperty(name='Active', default=0, min=0)

    Twists: CollectionProperty(type=JK_ARL_Twist_Bone_Props)
    
    Chain: IntProperty(name='Active', default=0, min=0)

    Chains: CollectionProperty(type=JK_ARL_Chain_Props)