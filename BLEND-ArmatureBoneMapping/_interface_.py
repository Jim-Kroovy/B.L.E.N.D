import bpy

from . import _properties_

# add-on preferences... stores all the stash file paths, mapping and retargets between .blends...    
class JK_ABM_Addon_Prefs(bpy.types.AddonPreferences):
    bl_idname = "BLEND-ArmatureBoneMapping"
    
    Show_mapping: bpy.props.BoolProperty(name="Show Mapping", description="Show the mapping", default=False)

    # the bone mapping being used across .blend files...
    Mapping: bpy.props.CollectionProperty(type=_properties_.JK_ABM_Part_Mapping)

def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.alignment = 'LEFT'
        # mapping column...
        m_col = row.column()
        m_box = m_col.box()
        m_box.alignment = 'LEFT'
        m_row = m_box.row()
        m_row.alignment = 'LEFT'
        m_row.label(text="Bone Mapping")
        m_row.prop(self, "Show_mapping", text="", icon='DOWNARROW_HLT')
        m_row.operator("jk.clear_mapping", text="", icon='TRASH')
        m_row.operator("jk.add_mapping", text="", icon='COLLECTION_NEW').Indices = (-1, -1, -1)
        m_row.operator("jk.reset_mapping", text="", icon='FILE_REFRESH')
        m_row.operator("jk.write_mapping", text="", icon='TEXT')
        # retarget column...
        r_col = row.column()
        r_box = r_col.box()
        r_box.alignment = 'LEFT'
        r_row = r_box.row()
        r_row.alignment = 'LEFT'
        r_row.label(text="Saved Retargets")
        r_row.prop(self, "Show_retargets", text="", icon='DOWNARROW_HLT')
        r_row.operator("jk.clear_retargets", text="", icon='TRASH')
        r_row.operator("jk.add_retarget", text="", icon='COLLECTION_NEW').Retarget = ""
        r_row.operator("jk.reset_retargets", text="", icon='FILE_REFRESH')
        r_row.operator("jk.write_retargets", text="", icon='TEXT')
        # other settings column...
        d_col = row.column()
        d_box = d_col.box()
        d_box.alignment = 'LEFT'
        d_row = d_box.row()
        d_row.alignment = 'LEFT'
        d_row.label(text="Settings")
        # mapping display...
        if self.Show_mapping:
            for i1, part in enumerate(self.Mapping):
                box1 = m_box.box()
                box1.alignment = 'LEFT'
                b_row1 = box1.row()
                b_row1.alignment = 'LEFT'
                b_row1.prop(part, "Part", text="[" + str(i1) + "]")
                b_row1.prop(part, "First", text="")
                b_row1.prop(part, "Second", text="")
                b_row1.prop(part, "Show_joints", text="", icon='DOWNARROW_HLT')
                b_row1.operator("jk.remove_mapping", text="", icon='TRASH').Indices = (i1, -1, -1)
                b_row1.operator("jk.add_mapping", text="", icon='COLLECTION_NEW').Indices = (i1, -1, -1)
                if part.Show_joints:                                
                    for i2, joint in enumerate(part.Joints):
                        row2 = box1.row()
                        row2.alignment = 'LEFT'
                        row2.separator(factor=3)
                        box2 = row2.box()
                        box2.alignment = 'LEFT'
                        b_row2 = box2.row()
                        b_row2.alignment = 'LEFT'
                        b_row2.prop(joint, "Joint", text="[" + str(i1) + "][" + str(i2) + "]")
                        b_row2.prop(joint, "First", text="")
                        b_row2.prop(joint, "Second", text="")
                        b_row2.prop(joint, "Show_sections", text="", icon='DOWNARROW_HLT')
                        b_row2.operator("jk.remove_mapping", text="", icon='TRASH').Indices = (i1, i2, -1)
                        b_row2.operator("jk.add_mapping", text="", icon='COLLECTION_NEW').Indices = (i1, i2, -1)
                        if joint.Show_sections:
                            for i3, section in enumerate(joint.Sections):
                                row3 = box2.row()
                                row3.alignment = 'LEFT'
                                row3.separator(factor=3)
                                box3 = row3.box()
                                box3.alignment = 'LEFT'
                                b_row3 = box3.row()
                                b_row3.alignment = 'LEFT'
                                b_row3.label(text="[" + str(i1) + "][" + str(i2) + "][" + str(i3) + "]")
                                #b_row3.label(text=Get_Mapping_Name((i1, i2, i3), self.Mapping)) add in labels at some point?
                                b_row3.prop(section, "Section", text="")
                                b_row3.prop(section, "First", text="")
                                b_row3.prop(section, "Second", text="")    
                                b_row3.operator("jk.remove_mapping", text="", icon='TRASH').Indices = (i1, i2, i3) 