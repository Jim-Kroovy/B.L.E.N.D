import bpy

def Add_To_Edit_Menu(self, context):
    self.layout.operator("jk.set_armature_symmetry")

def Get_Symmetrical_Orientation(self, fe_bone):
    # get the symmetrical head, tail and roll from operator variables...
    head = [fe_bone.head.x * -1 if self.Axes[0] and self.Head else fe_bone.head.x, 
        fe_bone.head.y * -1 if self.Axes[1] and self.Head else fe_bone.head.y,
        fe_bone.head.z * -1 if self.Axes[2] and self.Head else fe_bone.head.z]
    tail = [fe_bone.tail.x * -1 if self.Axes[0] and self.Tail else fe_bone.tail.x, 
        fe_bone.tail.y * -1 if self.Axes[1] and self.Tail else fe_bone.tail.y,
        fe_bone.tail.z * -1 if self.Axes[2] and self.Tail else fe_bone.tail.z]
    roll = fe_bone.roll * -1 if self.Roll else fe_bone.roll
    # and return them...
    return head, tail, roll

def Set_Bone_Symmetry(self, armature):
    # get selected or all armature edit bones...
    bones = [eb for eb in armature.data.edit_bones if eb.select] if self.Selected else armature.data.edit_bones
    # get the symmtrical names of all the bones..
    symmetrical_bones = {eb.name : eb.name[:-len(self.From_suffix)] + self.To_suffix for eb in bones}
    # for each bone name and symmetrical bone name...
    for fb_name, tb_name in symmetrical_bones.items():
        # get the from bone...
        fe_bone = armature.data.edit_bones[fb_name]
        # if the symmetrical name is already a bone, set it...
        if tb_name in armature.data.edit_bones:
            te_bone = armature.data.edit_bones[tb_name]
            head, tail, roll = Get_Symmetrical_Orientation(self, fe_bone)
        elif self.Create:
            # otherwise create a new one using the from bones orientation...
            te_bone = armature.data.edit_bones.new(tb_name)
            head, tail, roll = Get_Symmetrical_Orientation(self, fe_bone)
        te_bone.head, te_bone.tail, te_bone.roll = head, tail, roll
    # if we want to do mirror parenting...
    if self.Parent:
        # iterate over each pair of names again...
        for fb_name, tb_name in symmetrical_bones.items():
            # getting the from bone...
            fe_bone = armature.data.edit_bones[fb_name]
            # if the to bone exists...
            if tb_name in armature.data.edit_bones:
                # get it and what it's parents name should be...
                te_bone = armature.data.edit_bones[tb_name]
                pe_name = fe_bone.parent.name[:-len(self.From_suffix)] + self.To_suffix if fe_bone.parent != None else ""
                # if the "should be" parent exists...
                if pe_name in armature.data.edit_bones:
                    # make it the to bones parent...
                    te_bone.parent = armature.data.edit_bones[pe_name]
                else:
                    # otherwise just give it the same parent as the from bone
                    te_bone.parent = fe_bone.parent
