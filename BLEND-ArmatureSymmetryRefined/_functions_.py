import bpy

def add_to_edit_menu(self, context):
    self.layout.operator("jk.set_armature_symmetry")

def get_symmetrical_orientation(self, fe_bone):
    # get the symmetrical head, tail and roll from operator variables...
    head = [fe_bone.head.x * -1 if self.axes[0] and self.head else fe_bone.head.x, 
        fe_bone.head.y * -1 if self.axes[1] and self.head else fe_bone.head.y,
        fe_bone.head.z * -1 if self.axes[2] and self.head else fe_bone.head.z]
    tail = [fe_bone.tail.x * -1 if self.axes[0] and self.tail else fe_bone.tail.x, 
        fe_bone.tail.y * -1 if self.axes[1] and self.tail else fe_bone.tail.y,
        fe_bone.tail.z * -1 if self.axes[2] and self.tail else fe_bone.tail.z]
    roll = fe_bone.roll * -1 if self.roll else fe_bone.roll
    # and return them...
    return head, tail, roll

def set_bone_symmetry(self, armature):
    # get selected or all armature edit bones...
    bones = [eb for eb in armature.data.edit_bones if eb.select] if self.selected else armature.data.edit_bones
    # get the symmtrical names of all the bones..
    symmetrical_bones = {eb.name : eb.name[:-len(self.from_suffix)] + self.to_suffix for eb in bones}
    # for each bone name and symmetrical bone name...
    for fb_name, tb_name in symmetrical_bones.items():
        # get the from bone and declare the to bone variable...
        fe_bone, te_bone = armature.data.edit_bones[fb_name], None
        # if the symmetrical name is already a bone, set it...
        if tb_name in armature.data.edit_bones:
            te_bone = armature.data.edit_bones[tb_name]
        # otherwise create a new one if we should...
        elif self.create:
            te_bone = armature.data.edit_bones.new(tb_name)
        # check we have a symmetrical bone...
        if te_bone != None:
            # get the symmetrical head tail and rolls...
            head, tail, roll = get_symmetrical_orientation(self, fe_bone)
            # then set what should be set...
            if self.head:
                te_bone.head = head
            if self.tail:
                te_bone.tail = tail
            if self.roll:
                te_bone.roll = roll
    # if we want to mirror parenting...
    if self.parent:
        # iterate over each pair of names again...
        for fb_name, tb_name in symmetrical_bones.items():
            # getting the from bone...
            fe_bone = armature.data.edit_bones[fb_name]
            # if the to bone exists...
            if tb_name in armature.data.edit_bones:
                # get it and what it's parents name should be...
                te_bone = armature.data.edit_bones[tb_name]
                pe_name = fe_bone.parent.name[:-len(self.from_suffix)] + self.to_suffix if fe_bone.parent != None else ""
                # if the "should be" parent exists...
                if pe_name in armature.data.edit_bones:
                    # make it the to bones parent...
                    te_bone.parent = armature.data.edit_bones[pe_name]
                else:
                    # otherwise just give it the same parent as the from bone
                    te_bone.parent = fe_bone.parent
