import bpy
from bpy.props import (BoolProperty, StringProperty, EnumProperty, FloatProperty, FloatVectorProperty, IntProperty, IntVectorProperty, CollectionProperty, PointerProperty) 
from . import _functions_

class JK_AES_Edit_Bone_Props(bpy.types.PropertyGroup):

    Push_transform: BoolProperty(name="Push Transform", description="Pushes edit transform settings to child stages. (Head, Tail, Roll and Lock)",
        default=True, options=set())

    Push_bendy_bones: BoolProperty(name="Push Bendy Bones", description="Pushes bendy bone settings to child stages",
        default=True, options=set())

    Push_relations: BoolProperty(name="Push Relations", description="Pushes bone relations settings to child stages",
        default=True, options=set())

    Push_deform: BoolProperty(name="Push Deform", description="Pushes deform settings to child stages",
        default=True, options=set())

class JK_AES_Pose_Bone_Props(bpy.types.PropertyGroup):

    Push_posing: BoolProperty(name="Push Posing", description="Pushes pose transform settings to child stages. (Location, Rotation Mode, Rotation, Scale and all their lock settings",
        default=True, options=set())
        
    Push_group: BoolProperty(name="Push Group", description="Pushes bone group to child stages",
        default=True, options=set())

    Push_ik: BoolProperty(name="Push IK", description="Pushes inverse kinematics settings to child stages",
        default=True, options=set())
    
    Push_display: BoolProperty(name="Push Display", description="Pushes viewport display settings to child stages",
        default=True, options=set())
    
    Push_constraints: BoolProperty(name="Push Constraints", description="Pushes constraints to child stages",
        default=True, options=set())

    Push_drivers: BoolProperty(name="Push Drivers", description="Pushes drivers to child stages",
        default=True, options=set())

class JK_AES_Bone_Props(bpy.types.PropertyGroup):

    Push_edit: BoolProperty(name="Push Edit Bone", description="Pushes edit bone settings to child stages. (will create the bone if it doesn't exist in the child stage)",
        default=False, options=set())

    Edit: PointerProperty(type=JK_AES_Edit_Bone_Props, options=set())
    
    Push_pose: BoolProperty(name="Push Pose Bone", description="Pushes pose bone settings to child stages",
        default=False, options=set())

    Pose: PointerProperty(type=JK_AES_Pose_Bone_Props, options=set())

    Push_custom_props: BoolProperty(name="Push Properties", description="Pushes custom properties on both pose and edit bones to child stages",
        default=False, options=set())

class JK_AES_Object_Props(bpy.types.PropertyGroup):

    Push_transform: BoolProperty(name="Push Transform", description="Pushes object transform settings to child stages.",
        default=True, options=set())

    Push_relations: BoolProperty(name="Push Relations", description="Pushes object relations settings to child stages",
        default=True, options=set())

    Push_instancing: BoolProperty(name="Push Instancing", description="Pushes object instancing settings to child stages.",
        default=True, options=set())

    Push_display: BoolProperty(name="Push Display", description="Pushes viewport display settings to child stages",
        default=True, options=set())

class JK_AES_Data_Props(bpy.types.PropertyGroup):

    Push_skeleton: BoolProperty(name="Push Skeleton", description="Pushes skeleton settings to child stages. (pose position, layers and protected layers)",
        default=True, options=set())

    Push_groups: BoolProperty(name="Push Groups", description="Pushes bone groups to child stages",
        default=True, options=set())

    Push_library: BoolProperty(name="Push Library", description="Pushes pose library to child stages",
        default=True, options=set())

    Push_display: BoolProperty(name="Push Display", description="Pushes viewport display settings to child stages",
        default=True, options=set())

class JK_AES_Stage_Props(bpy.types.PropertyGroup):

    Is_pushing: BoolProperty(name="Is Pushing", description="Are we currently pushing",
        default=False, options=set())
        
    Armature: StringProperty(name="Armature", description="Armature that defines this stage", 
        default="", maxlen=1024)
        
    Is_source: BoolProperty(name="Is Source", description="This is the source armature, there can only be one",
        default=False, options=set())

    Show_details: BoolProperty(name="Show details", description="This is the source armature, there can only be one",
        default=False, options=set())
    
    Parent: StringProperty(name="Parent Stage", description="The stage before this one", 
        default="", maxlen=1024)

    def Update_Push_Data(self, context):
        if self.Push_data:
            bpy.ops.jk.draw_push_settings('INVOKE_DEFAULT', Stage=self.name, Settings='DATA')
    
    Push_data: BoolProperty(name="Push Data", description="Pushes data settings to child stages. (All Bones, Bone Groups, etc)",
        default=False, options=set(), update=Update_Push_Data)

    Data: PointerProperty(type=JK_AES_Data_Props)
    
    def Update_Push_Object(self, context):
        if self.Push_object and not self.Is_pushing:
            bpy.ops.jk.draw_push_settings('INVOKE_DEFAULT', Stage=self.name, Settings='OBJECT')

    Push_object: BoolProperty(name="Push Object", description="Pushes object settings to child stages. (NLA Strips, Pose Mode, Transforms, etc)",
        default=False, options=set(), update=Update_Push_Object)

    Object: PointerProperty(type=JK_AES_Object_Props)

    def Update_Push_Bones(self, context):
        bones = bpy.data.armatures[self.Armature].bones
        _functions_.Get_Push_Bones(self, bones)
        bpy.ops.jk.draw_push_settings('INVOKE_DEFAULT', Stage=self.name, Settings='BONES')
    
    Push_bones: BoolProperty(name="Push Bones", description="Pushes per bone settings to child stages. (Edit Bones, Pose Bones)",
        default=False, options=set(), update=Update_Push_Bones)

    Bones: CollectionProperty(type=JK_AES_Bone_Props, options=set())

class JK_AES_Armature_Props(bpy.types.PropertyGroup):
    
    Is_master: BoolProperty(name="Is Master", description="Is this a master of stages. (used by load handler to clean up after deleting a master)",
        default=True, options=set())

    Master: PointerProperty(type=bpy.types.Object, options=set())
    
    def Update_Stage(self, context):
        # lets not do anything silly like run a heap of code when we don't need to...
        if self.Stage != self.Last:
            last_mode = context.object.mode
            bpy.ops.object.mode_set(mode='OBJECT')
            # first we save the last stage by pulling from the master...
            _functions_.Pull_From_Master(bpy.context.object, self.Stages[self.Last])
            # then we push the last stage into the hierarchy of stages...
            _functions_.Push_From_Stage(bpy.context.object, self.Stages[self.Last])
            # set the last stage to the new stage, important this happens before...
            self.Last = self.Stage
            # we push the stage we are heading to onto the master...
            _functions_.Push_To_Master(bpy.context.object, self.Stages[self.Stage])
            bpy.ops.object.mode_set(mode=last_mode)
                
    Last: StringProperty(name="Last", description="The stage we are coming from", 
        default="", maxlen=1024)
    
    Stage: StringProperty(name="Stage", description="The stage we are on", 
        default="", maxlen=1024, update=Update_Stage)
    
    Stages: CollectionProperty(type=JK_AES_Stage_Props, options=set())