import bpy
import math
from mathutils import Vector

from bpy.props import (BoolProperty, BoolVectorProperty, StringProperty, EnumProperty, FloatProperty, FloatVectorProperty, IntProperty, IntVectorProperty, CollectionProperty, PointerProperty)

# Much of this code is copy/pasted between the various flavours of rigging, while a little long winded it makes adding new things and updating and troubleshooting a whole lot easier...
# and everyone wants me to do so much i decided it's better that things are easy to edit/create and not as dynamic as they could be...

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- PROPERTY FUNCTIONS -----------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

def get_spline_refs(self):
    armature, references = self.id_data, {}
    pbs, bbs = armature.pose.bones, armature.data.bones
    references['targets'] = [{
        'source' : pbs.get(target.source), 'origin' : pbs.get(target.origin)} for target in self.targets]
    references['bones'] = [{
        'source' : pbs.get(bone.source), 'origin' : pbs.get(bone.origin), 'gizmo' : pbs.get(bone.gizmo)} for bone in self.bones]
    references['constraints'] = [{
        'constraint' : pbs.get(con.source).constraints.get(con.constraint) if pbs.get(con.source) else None,
        'source' : pbs.get(con.source)} for con in self.constraints]
    references['drivers'] = [{
        'source' : pbs.get(drv.source) if drv.is_pose_bone else bbs.get(drv.source),
        'constraint' : pbs.get(drv.source).constraints.get(drv.constraint) if drv.constraint and pbs.get(drv.source) else "",
        'setting' : drv.setting} for drv in self.drivers]
    return references

def get_spline_parents(self, bones):
    # get recursive parents from the source to the length of the chain...
    parent, parents = bones.get(self.spline.end), []
    while len(parents) < self.spline.length:# and parent != None:
        parents.append(parent)
        parent = parent.parent if parent else None
    return parents

def get_spline_props(self, armature):
    bones = armature.data.edit_bones if armature.mode == 'EDIT' else armature.data.bones
    self.is_editing = True
    if bones.active:
        self.spline.end = bones.active.name
    # clear the bones, targets and constraints...
    self.bones.clear()
    self.targets.clear()
    self.constraints.clear()
    # need a spline IK constraint on the gizmos using original scale...
    spline_ik = self.constraints.add()
    spline_ik.flavour = 'SPLINE_IK'
    # then another spline IK constraint on the stretches that scales to the curve...
    spline_ik = self.constraints.add()
    spline_ik.flavour = 'SPLINE_IK'
    # end gizmo copies end target rotation in world space...
    copy_rot = self.constraints.add()
    copy_rot.flavour = 'COPY_ROTATION'
    # start bone copies start target location in local space...
    copy_loc = self.constraints.add()
    copy_loc.flavour = 'COPY_LOCATION'
    # get recursive parents...
    parents = get_spline_parents(self, bones)
    # add in a bone and a target for every bone in the chain...
    for parent in reversed(parents):
        bone = self.bones.add()
        target = self.targets.add()
        if parent:
            bone.source = parent.name
            target.source = parent.name
        # each source bone has a copy rotation to its gizmo...
        copy_rot = self.constraints.add()
        copy_rot.flavour = 'COPY_ROTATION'
        # and a copy rot to its stretch...
        copy_rot = self.constraints.add()
        copy_rot.flavour = 'COPY_ROTATION'
        # so we can drive a float that switches between them...
        driver = self.drivers.add()
        driver.setting, driver.expression = "influence", "1 - use_fit_curve"
        variable = driver.variables.add()
        variable.name, variable.flavour = "use_fit_curve", 'SINGLE_PROP'
        # by inverting the float on one of them...
        driver = self.drivers.add()
        driver.setting, driver.expression = "influence", "use_fit_curve"
        variable = driver.variables.add()
        variable.name, variable.flavour = "use_fit_curve", 'SINGLE_PROP'
    self.is_editing = False

def set_spline_props(self, armature):
    prefs = bpy.context.preferences.addons["BLEND-ArmatureRiggingModules"].preferences
    bones = armature.data.edit_bones if armature.mode == 'EDIT' else armature.data.bones
    rigging = armature.jk_arm.rigging[armature.jk_arm.active]
    # set the name of the rigging based on the bones... (needed for drivers)
    rigging.name = "Chain (Spline) - " + self.spline.end + " - " + str(self.spline.length)
    # self.spline.curve = armature.name + "_" + self.spline.end + "_" + str(self.spline.length)
    # get recursive parents...
    parents, self.is_editing = get_spline_parents(self, bones), True
    ci, di, = 4, 0
    parents.reverse()
    for bi in range(0, self.spline.length):
        # if we don't have a bone already create one...
        bone = self.bones.add() if len(self.bones) <= bi else self.bones[bi]
        target = self.targets.add() if len(self.targets) <= bi else self.targets[bi]
        parent = parents[bi] if len(parents) > bi else None
        if parent:
            bone.source = parent.name
            bone.origin = parent.parent.name if parent.parent else ""
            bone.gizmo = prefs.affixes.gizmo + parent.name
            bone.stretch = prefs.affixes.mech + prefs.affixes.stretch + parent.name
            target.source = parent.name
            target.origin = parent.parent.name if parent.parent else ""
            target.bone = prefs.affixes.target + parent.name
            # start and end targets must always be used... (also use middle by default)
            if bi == int(self.spline.length * 0.5):
                target.use = target.use if target.use_edited else True
            elif bi == self.spline.length - 1 or bi == 0:
                target.use = True
            else:
                target.use = target.use if target.use_edited else False
        # each source bone has a copy rotation to its gizmo...
        copy_rot = self.constraints.add() if len(self.constraints) <= ci else self.constraints[ci]
        copy_rot.constraint = "GIZMO - Copy Rotation"
        copy_rot.source, copy_rot.subtarget = bone.source, bone.gizmo
        copy_rot.target_space, copy_rot.owner_space, copy_rot.mix_mode = 'LOCAL', 'LOCAL', 'BEFORE'
        ci = ci + 1
        # and a copy rot to its stretch bone...
        copy_rot = self.constraints.add() if len(self.constraints) <= ci else self.constraints[ci]
        copy_rot.constraint = "STRETCH - Copy Rotation"
        copy_rot.source, copy_rot.subtarget = bone.source, bone.stretch
        copy_rot.target_space, copy_rot.owner_space, copy_rot.mix_mode = 'LOCAL', 'LOCAL', 'BEFORE'
        ci = ci + 1
        # so we can drive a float that switches between them...
        driver = self.drivers.add() if len(self.drivers) <= di else self.drivers[di]
        variable = driver.variables[0] if driver.variables else driver.variables.add()
        driver.setting, driver.expression = "influence", "1 - fit_curve"
        variable.name, variable.flavour = "fit_curve", 'SINGLE_PROP'
        driver.source, driver.constraint = bone.source, "GIZMO - Copy Rotation"
        driver.variables[0].data_path = 'jk_arm.rigging["' + rigging.name + '"].spline.fit_curve'
        di = di + 1
        # by inverting the float on one of them...
        driver = self.drivers.add() if len(self.drivers) <= di else self.drivers[di]
        variable = driver.variables[0] if driver.variables else driver.variables.add()
        driver.setting, driver.expression = "influence", "fit_curve"
        variable.name, variable.flavour = "fit_curve", 'SINGLE_PROP'
        driver.source, driver.constraint = bone.source, "STRETCH - Copy Rotation"
        driver.variables[0].data_path = 'jk_arm.rigging["' + rigging.name + '"].spline.fit_curve'
        di = di + 1

    self.spline.parent = prefs.affixes.control + self.targets[0].source
    # might need to clean up bones when reducing chain length...
    if len(self.bones) > self.spline.length:
        while len(self.bones) != self.spline.length:
            self.bones.remove(self.spline.length)
    # might need to clean up targets when reducing chain length...
    if len(self.targets) > self.spline.length:
        while len(self.targets) != self.spline.length:
            self.targets.remove(self.spline.length)
    # might need to clean up constraints when reducing chain length...
    if len(self.constraints) > ((self.spline.length * 2) + 4):
        while len(self.constraints) != ((self.spline.length * 2) + 4):
            self.constraints.remove(((self.spline.length * 2) + 4))
    # aaand might need to clean up drivers when reducing length...
    if len(self.drivers) > (self.spline.length * 2):
        while len(self.drivers) != (self.spline.length * 2):
            self.drivers.remove((self.spline.length * 2))
    # need a spline IK constraint on the gizmos using original scale...
    spline_ik = self.constraints[0]
    spline_ik.source, spline_ik.chain_count = self.bones[-2].gizmo, self.spline.length - 1
    spline_ik.y_scale_mode, spline_ik.constraint = 'BONE_ORIGINAL', "SPLINE - Spline IK"
    # then another spline IK constraint on the stretches that scales to the curve...
    spline_ik = self.constraints[1]
    spline_ik.source, spline_ik.chain_count = self.bones[-2].stretch, self.spline.length - 1
    spline_ik.y_scale_mode, spline_ik.constraint = 'FIT_CURVE', "SPLINE - Spline IK"
    # end gizmo copies end target rotation in world space...
    copy_rot = self.constraints[2]
    copy_rot.source, copy_rot.subtarget = self.bones[-1].gizmo, self.targets[-1].bone
    copy_rot.owner_space, copy_rot.target_space, copy_rot.constraint = 'WORLD', 'WORLD', "TARGET - Copy Rotation"
    # start bone copies start target location in local space...
    copy_loc = self.constraints[3]
    copy_loc.source, copy_loc.subtarget, copy_loc.use_offset = self.bones[0].source, self.targets[0].bone, True
    copy_loc.owner_space, copy_loc.target_space, copy_loc.constraint = 'LOCAL', 'LOCAL', "TARGET - Copy Location"
    self.is_editing = False
    # then clear the riggings source bone data...
    rigging.sources.clear()
    # and refresh it for the auto update functionality...
    rigging.get_sources()

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- RIGGING FUNCTIONS ------------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

def add_spline_targets(self, armature):
    # get the user defined local axis and offset distance...
    direction = Vector((1.0, 0.0, 0.0)) if self.spline.axis.startswith('X') else Vector((0.0, 1.0, 0.0)) if self.spline.axis.startswith('Y') else Vector((0.0, 0.0, 1.0))
    distance = (self.spline.distance * -1) if 'NEGATIVE' in self.spline.axis else (self.spline.distance)
    ebs = armature.data.edit_bones
    # create a parent for the targets...
    start_eb = ebs.get(self.targets[0].source)
    parent_eb = ebs.new(self.spline.parent)
    parent_eb.head, parent_eb.tail, parent_eb.roll = start_eb.head, start_eb.tail, start_eb.roll
    # that uses the parent of the first targets source...
    parent_eb.parent, parent_eb.use_deform = start_eb.parent, False
    # then iterate through the targets, making them duplicates of their source bones...
    for target in self.targets:
        if target.use:
            source_eb = ebs.get(target.source)
            target_eb = ebs.new(target.bone)
            target_eb.head = source_eb.head + (direction * distance)
            target_eb.tail = source_eb.tail + (direction * distance)
            target_eb.roll, target_eb.length = source_eb.roll, source_eb.length * 0.5
            target_eb.parent, target_eb.use_deform = parent_eb, False
            # and saving their head position for the spline to reference...
            target.co = target_eb.head.copy()

def add_spline_curve(self, armature):
    # in object mode...
    bpy.ops.object.mode_set(mode='OBJECT')
    # let's create a new curve with some basic display settings...
    #curve = bpy.data.curves.new(self.spline.curve, 'CURVE')
    curve = bpy.data.curves.new(armature.name + "_" + self.spline.end + "_" + str(self.spline.length), 'CURVE')
    curve.dimensions, curve.bevel_depth = '3D', self.spline.bevel_depth
    spline = curve.splines.new(type='NURBS')
    # and enough points for all the target bones...
    coords = [[target.co[0], target.co[1], target.co[2]] for target in self.targets if target.use]
    spline.points.add(len(coords) - 1)
    for p, co in zip(spline.points, coords):
        p.co = (co + [1.0])
    spline.use_endpoint_u, spline.use_endpoint_v = True, True
    # assign to an object, parent to the armature and link to the same collections...
    obj = bpy.data.objects.new(armature.name + "_" + self.spline.end + "_" + str(self.spline.length), curve)
    obj.parent = armature
    self.spline.curve = obj
    for collection in armature.users_collection:
        collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    # then we need to hook its points to the targets...
    targets = [target for target in self.targets if target.use]
    for pi, target in enumerate(targets):
        bpy.ops.object.mode_set(mode='OBJECT')
        # add the modifier in object mode... (only the last hook applies if we do this all in edit mode)
        hook = obj.modifiers.new(name=target.bone + " - Hook", type='HOOK')
        hook.object, hook.subtarget = armature, target.bone
        # go back to edit mode and deselect everything...
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.curve.select_all(action='DESELECT')
        # get a nice fresh reference to the the point and select it to hook the damn thing... (switching mode breaks references)
        point = obj.data.splines[0].points[pi]
        point.select = True
        bpy.ops.object.hook_assign(modifier=target.bone + " - Hook")
    # make sure the spline isn't selectable and doesn't render...
    
    # then go back to the armature...
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.objects.active = armature

def add_spline_bones(self, armature):
    # and the defined local axis and distance...
    direction = Vector((1.0, 0.0, 0.0)) if self.spline.axis.startswith('X') else Vector((0.0, 1.0, 0.0)) if self.spline.axis.startswith('Y') else Vector((0.0, 0.0, 1.0))
    distance = (self.spline.distance * -1) if 'NEGATIVE' in self.spline.axis else (self.spline.distance)
    bpy.ops.object.mode_set(mode='EDIT')
    ebs = armature.data.edit_bones
    # get the start and parent bones and make the start a child of the parent...
    start_eb, parent_eb = ebs.get(self.bones[0].source), ebs.get(self.spline.parent)
    start_eb.use_connect, start_eb.parent = False, parent_eb
    stretch_parent = parent_eb
    # add in stretch bones for every bone in the chain...
    for bone in self.bones:
        source_eb = ebs.get(bone.source)
        stretch_eb = ebs.new(bone.stretch)
        stretch_eb.head, stretch_eb.tail = source_eb.head + (direction * distance), source_eb.tail + (direction * distance)
        stretch_eb.roll, stretch_eb.parent, stretch_eb.use_deform = source_eb.roll, stretch_parent, False
        stretch_parent = stretch_eb
        if bone.source == self.bones[-1].source:
            stretch_eb.use_inherit_rotation = False
    # then hop over to pose mode and constrain them to the spline...
    bpy.ops.object.mode_set(mode='POSE')
    pbs, obs = armature.pose.bones, bpy.data.objects
    stretch_pb = pbs.get(self.bones[-2].stretch)
    spline_ik = stretch_pb.constraints.new('SPLINE_IK')
    #spline_ik.target, spline_ik.chain_count = obs[self.spline.curve], self.spline.length - 1
    spline_ik.target, spline_ik.chain_count = self.spline.curve, self.spline.length - 1
    # applying the pose they take when fitting the curve...
    bpy.ops.pose.select_all(action='DESELECT')
    for pb in [pbs.get(bone.stretch) for bone in self.bones]:
        pb.bone.select = True
    bpy.ops.pose.armature_apply(selected=True)
    bpy.ops.pose.constraints_clear()
    # then back to edit mode and re-reference a couple of variables... (swithing mode kills bone refs)
    bpy.ops.object.mode_set(mode='EDIT')
    ebs = armature.data.edit_bones
    start = ebs.get(self.bones[0].source)
    gizmo_parent = ebs.get(self.spline.parent)
    # and iterate on the bones again setting all the gizmo bones to match stretch bones...
    for bone in self.bones:
        stretch_eb = ebs.get(bone.stretch)
        if bone.source == self.bones[-1].source:
            stretch_eb.use_inherit_rotation = True
        gizmo_eb = ebs.new(bone.gizmo)
        gizmo_eb.head, gizmo_eb.tail, gizmo_eb.roll = stretch_eb.head, stretch_eb.tail, stretch_eb.roll
        gizmo_eb.parent, gizmo_eb.use_deform, gizmo_eb.inherit_scale = gizmo_parent, False, 'ALIGNED'
        gizmo_parent = gizmo_eb

def add_spline_constraints(self, armature):
    #pbs, curve = armature.pose.bones, bpy.data.objects[self.spline.curve]
    pbs, curve = armature.pose.bones, self.spline.curve
    for constraint in self.constraints:
        pb = pbs.get(constraint.source)
        if pb and constraint.flavour != 'NONE':
            con = pb.constraints.new(type=constraint.flavour)
            con_props = {cp.identifier : getattr(constraint, cp.identifier) for cp in constraint.bl_rna.properties if not cp.is_readonly}
            # for each of the constraints settings...
            for cp in con.bl_rna.properties:
                if cp.identifier == 'target':
                    con.target = curve if constraint.flavour == 'SPLINE_IK' else armature
                # so constraints are stupid af, not all constraints with 'target_space' even HAVE a 'target' property...
                elif cp.identifier == 'target_space' and con_props['target_space'] in ['LOCAL_WITH_PARENT', 'POSE']:
                    # but can only set target space to 'local with parent' or 'pose' on those that do if the target has been set...
                    con.target, con.target_space = armature, con_props['target_space']
                # my collections are indexed, so to avoid my own confusion, name is constraint...
                elif cp.identifier == 'name':
                    setattr(con, cp.identifier, con_props['constraint'])
                # use offset overrides copy rotations mix mode...
                elif cp.identifier == 'use_offset':
                    # so only set it if this constraint is not a copy rotation...
                    if constraint.flavour != 'COPY_ROTATION' and cp.identifier in con_props:
                        setattr(con, cp.identifier, con_props[cp.identifier])
                # if they are in our settings dictionary... (and are not read only?)
                elif cp.identifier in con_props and not cp.is_readonly:
                    setattr(con, cp.identifier, con_props[cp.identifier])
    
            con.show_expanded = False

def add_spline_drivers(self, armature):
    pbs, bbs = armature.pose.bones, armature.data.bones
    for driver in self.drivers:
        # get the source bone of the driver, if it exists... (from the relevant bones)
        source_b = pbs.get(driver.source) if driver.is_pose_bone else bbs.get(driver.source)
        if source_b:
            if driver.constraint:
                drv = source_b.constraints[driver.constraint].driver_add(driver.setting)
            else:
                drv = source_b.driver_add(driver.setting)
            # and iterate on the variables...
            for variable in driver.variables:
                # adding them, setting their names and types...
                var = drv.driver.variables.new()
                var.name, var.type = variable.name, variable.flavour
                var.targets[0].id = armature
                var.targets[0].data_path = variable.data_path
            # set the drivers expression...
            drv.driver.expression = driver.expression
            # and remove any sneaky curve modifiers...
            for mod in drv.modifiers:
                drv.modifiers.remove(mod)

def add_spline_shapes(self, armature):
    prefs = bpy.context.preferences.addons["BLEND-ArmatureRiggingModules"].preferences
    pbs = armature.pose.bones
    bone_shapes = self.get_shapes()
    # iterate on the bones to get the source bones axis based shapes...
    brackets = {'X' : "Bone_Shape_Default_Medial_Bracket_X_Positive", 'X_NEGATIVE' : "Bone_Shape_Default_Medial_Bracket_X_Negative",
        'Z' : "Bone_Shape_Default_Medial_Bracket_Z_Positive", 'Z_NEGATIVE' : "Bone_Shape_Default_Medial_Bracket_Z_Negative"}
    for bone in self.bones:
        bracket = brackets[bone.axis]
        # and append or add them into the bone shapes dictionary...
        if bracket in bone_shapes:
            bone_shapes[bracket].append(bone.source)
        else:
            bone_shapes[bracket] = [bone.source]
    # get the names of any shapes that do not already exists in the .blend...
    load_shapes = [sh for sh in bone_shapes.keys() if sh not in bpy.data.objects]
    # if we have shapes to load...
    if load_shapes:
        # load the them from their library.blend...
        with bpy.data.libraries.load(prefs.shape_path, link=False) as (data_from, data_to):
            data_to.objects = [shape for shape in data_from.objects if shape in load_shapes]
    # then iterate on the bone shapes dictionary...
    for shape, bones in bone_shapes.items():
        for bone in bones:
            # setting all existing pose bones...
            pb = pbs.get(bone)
            if pb:
                # to use their designated shape...
                pb.custom_shape = bpy.data.objects[shape]

def add_spline_groups(self, armature):
    prefs = bpy.context.preferences.addons["BLEND-ArmatureRiggingModules"].preferences
    pbs = armature.pose.bones
    bone_groups = self.get_groups()
    # get the names of any groups that do not already exist on the armature...
    load_groups = [gr for gr in bone_groups.keys() if gr not in armature.pose.bone_groups]
     # if we have any groups to load...
    if load_groups:
        # create them and set their colour...
        for load_group in load_groups:
            grp = armature.pose.bone_groups.new(name=load_group)
            grp.color_set = prefs.group_colours[load_group]
    # then iterate on the bone groups dictionary...
    for group, bones in bone_groups.items():
        for bone in bones:
            # setting all existing pose bones...
            pb = pbs.get(bone)
            if pb:
                # to use their designated group...
                pb.bone_group = armature.pose.bone_groups[group]

def add_spline_layers(self, armature):
    prefs = bpy.context.preferences.addons["BLEND-ArmatureRiggingModules"].preferences
    pbs = armature.pose.bones
    bone_layers = self.get_groups()
    # then iterate on the bone layers dictionary...
    for layer, bones in bone_layers.items():
        for bone in bones:
            # setting all existing pose bones...
            pb = pbs.get(bone)
            if pb:
                # to use their designated layer...
                pb.bone.layers = prefs.group_layers[layer]

def add_spline_chain(self, armature):
    # don't touch the symmetry! (Thanks Jon V.D, you are a star)
    is_mirror_x = armature.data.use_mirror_x
    if is_mirror_x:
        armature.data.use_mirror_x = False
    # don't want to trigger the mode callback during setup...
    is_detecting = armature.jk_arm.use_edit_detection
    if is_detecting:
        armature.jk_arm.use_edit_detection = False
    # need to add bones in edit mode...
    bpy.ops.object.mode_set(mode='EDIT')
    add_spline_targets(self, armature)
    add_spline_curve(self, armature)
    add_spline_bones(self, armature)
    #if self.auto_roll:
        #add_spline_rolls(self, armature)
    # and add constraints and drivers in pose mode...
    bpy.ops.object.mode_set(mode='POSE')
    add_spline_constraints(self, armature)
    add_spline_drivers(self, armature)
    # if we are using default shapes or groups, add them...
    if self.use_default_shapes:
        add_spline_shapes(self, armature)
    if self.use_default_groups:
        add_spline_groups(self, armature)
    if self.use_default_layers:
        add_spline_layers(self, armature)
    # give x mirror back... (if it was turned on)
    armature.data.use_mirror_x = is_mirror_x
    # give edit detection back... (if it was turned on)
    armature.jk_arm.use_edit_detection = is_detecting

def remove_spline_chain(self, armature):
    references = self.get_references()
    #print(references['constraints'])
    # first we should get rid of anything in pose mode...
    if armature.mode != 'POSE':
        bpy.ops.object.mode_set(mode='POSE')
    # drivers do not get removed when bones/constraints get removed so get rid of them...
    for drv_refs in references['drivers']:
        if drv_refs['constraint']:
            drv_refs['constraint'].driver_remove(drv_refs['setting'])
        elif drv_refs['source']:
            drv_refs['source'].driver_remove(drv_refs['setting'])
    # constraints need removing, we are, only removing the bone of one...
    for con_refs in references['constraints']:
        if con_refs['source'] and con_refs['constraint']:
            con_refs['source'].constraints.remove(con_refs['constraint'])
    # clear shapes/groups from source bones... (what should i do about layers?)
    for bone_refs in references['bones']:
        if bone_refs['source']:
            bone_refs['source'].custom_shape, bone_refs['source'].bone_group = None, None
    #curve = bpy.data.objects[self.spline.curve]
    curve = self.spline.curve
    if curve:
        curve_data = curve.data
        bpy.data.objects.remove(curve)
        bpy.data.curves.remove(curve_data)
    # then we need to kill any added bones in edit mode...
    bpy.ops.object.mode_set(mode='EDIT')
    ebs, remove_bones = armature.data.edit_bones, []
    for target in self.targets:
        target_eb = ebs.get(target.bone)
        if target_eb:
            for child in target_eb.children:
                child.parent = ebs.get(target.source)
        remove_bones.append(target.bone)
    for bone in self.bones:
        source_eb = ebs.get(bone.source)
        if source_eb:
            source_eb.parent = ebs.get(bone.origin)
        remove_bones.append(bone.gizmo)
        remove_bones.append(bone.stretch)
    remove_bones.append(self.spline.parent)
    # iterate on the names of the bones to be removed...
    for name in remove_bones:
        # if they exist...
        eb = ebs.get(name)
        if eb:
            # remove them...
            ebs.remove(eb)
    # then return to pose mode like nothing ever happened...
    bpy.ops.object.mode_set(mode='POSE')

#------------------------------------------------------------------------------------------------------------------------------------------------------#

#----- PROPERTIES -------------------------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------------------------------------------------------------------------------#

class JK_PG_ARM_Spline_Constraint(bpy.types.PropertyGroup):
    
    def update_constraint(self, context):
        armature = self.id_data
        rigging = armature.jk_arm.rigging[armature.jk_arm.active].spline
        if not rigging.is_editing:
            rigging.update_rigging(context)

    source: StringProperty(name="Source", description="Name of the bone the constraint is on",
        default="", maxlen=63)

    constraint: StringProperty(name="Constraint", description="Name of the actual constraint",
        default="", maxlen=63)

    flavour: EnumProperty(name="Flavour", description="The type of constraint",
        items=[('COPY_ROTATION', 'Copy Rotation', ""), ('COPY_LOCATION', 'Copy Location', ""), 
            ('COPY_SCALE', 'Copy Scale', ""), ('SPLINE_IK', 'Spline IK', "")],
        default='COPY_ROTATION')
    
    subtarget: StringProperty(name="Subtarget", description="Name of the subtarget. (if any)",
        default="", maxlen=1024)#, update=update_constraint)

    use_x: BoolProperty(name="Use X", description="Use X", default=True)
    invert_x: BoolProperty(name="Invert X", description="Invert X", default=False)

    use_y: BoolProperty(name="Use Y", description="Use Y", default=True)
    invert_y: BoolProperty(name="Invert Y", description="Invert Y", default=False)

    use_z: BoolProperty(name="Use Z", description="Use Z limit", default=True)
    invert_z: BoolProperty(name="Invert Z", description="Invert Z", default=False)

    use_offset: BoolProperty(name="Use Offset", description="Add original transform into copied transform. (location/scale copy constraint)", 
        default=False)

    mix_mode: EnumProperty(name="Mix Mode", description="Specify how the copied and existing rotations are combined",
        items=[('REPLACE', "Replace", "Replace original rotation with copied"), 
            ('ADD', "Add", "Add euler component values together"),
            ('BEFORE', "Before Original", "Apply copied rotation before original, as if the constraint target is a parent"),
            ('AFTER', "After Original", "Apply copied rotation after original, as if the constraint target is a child"),
            ('OFFSET', "Fit Curve", "Combine rotations like the original offset checkbox. Does not work well for multiple axis rotations")],
        default='REPLACE')

    y_scale_mode: EnumProperty(name="Y Scale Mode", description="Method used for determining the scaling of the Y axis of the bones, on top of the shape and scaling of the curve itself",
        items=[('NONE', "None", "Don't scale on the Y axis"), 
            ('BONE_ORIGINAL', "Bone Original", "Use original Y scale"), 
            ('FIT_CURVE', "Fit Curve", "Scale bones to fit the entire length of the curve")],
        default='BONE_ORIGINAL')

    target_space: EnumProperty(name="Target Space", description="Space that target is evaluated in",
        items=[('WORLD', "World Space", ""), ('POSE', "Pose Space", ""), 
            ('LOCAL', "local Space", ""), ('LOCAL_WITH_PARENT', "local With Parent Space", "")],
        default='LOCAL')

    owner_space: EnumProperty(name="owner Space", description="Space that owner is evaluated in",
        items=[('WORLD', "World Space", ""), ('POSE', "Pose Space", ""), 
            ('LOCAL', "local Space", ""), ('LOCAL_WITH_PARENT', "local With Parent", "")],
        default='LOCAL')

    chain_count: IntProperty(name="Chain Length", description="How many bones are included in the IK effect",
        default=3, min=2)

    influence: FloatProperty(name="Influence", description="influence of this constraint", default=1.0, min=0.0, max=1.0, subtype='FACTOR')

class JK_PG_ARM_Spline_Variable(bpy.types.PropertyGroup):

    flavour: EnumProperty(name="Type", description="What kind of driver variable is this?",
        items=[('SINGLE_PROP', "Single Property", ""), ('TRANSFORMS', "Transforms", ""),
            ('ROTATION_DIFF', "Rotation Difference", ""), ('LOC_DIFF', "Location Difference", "")])

    data_path: StringProperty(name="Data Path", description="The data path if single property",
        default="")

class JK_PG_ARM_Spline_Driver(bpy.types.PropertyGroup):

    is_pose_bone: BoolProperty(name="Is Pose Bone", description="Is this drivers source a pose bone or a bone bone?",
        default=True)

    source: StringProperty(name="Source", description="Name of the bone the driver is on",
        default="", maxlen=63)

    constraint: StringProperty(name="Constraint", description="Name of constraint on the bone the driver is on",
        default="", maxlen=63)

    setting: StringProperty(name="Setting", description="Name of the setting the driver is on",
        default="")

    expression: StringProperty(name="Expression", description="The expression of the driver",
        default="")

    variables: CollectionProperty(type=JK_PG_ARM_Spline_Variable)

class JK_PG_ARM_Spline_Curve(bpy.types.PropertyGroup):

    def update_spline(self, context):
        armature = self.id_data
        rigging = armature.jk_arm.rigging[armature.jk_arm.active].spline
        if not rigging.is_editing:
            # changing the source is a little complicated because we need it to remove/update rigging...
            bones = armature.data.edit_bones if armature.mode == 'EDIT' else armature.data.bones
            # deselect everything depending on mode...
            if armature.mode == 'EDIT':
                bpy.ops.armature.select_all(action='DESELECT')
            elif armature.mode == 'POSE':
                bpy.ops.pose.select_all(action='DESELECT')
            # make the new source active and save a reference of it...
            bones.active = bones.get(self.end)
            #new_end, new_length, new_distance = self.end, self.length, self.distance
            new_end = self.end
            # remove the rigging and set "is_editing" true...
            rigging.is_rigged, rigging.is_editing = False, True
            # while is_editing is false set the new source to what we want it to be...
            #self.end, self.length, self.distance, rigging.is_editing = new_end, new_length, new_distance, False
            self.end, rigging.is_editing = new_end, False
            # then we can update the rigging...
            rigging.update_rigging(context)
    
    #curve: StringProperty(name="Curve", description="Name of the spline curve",
        #default="", maxlen=63)

    curve: PointerProperty(type=bpy.types.Object)

    parent: StringProperty(name="Parent", description="Name of the target bones parent",
        default="", maxlen=63)

    end: StringProperty(name="From", description="Name of the bone at the end of the chain",
        default="", maxlen=63, update=update_spline)

    length: IntProperty(name="Chain Length", description="How many bones are included in this IK chain",
        default=3, min=3, update=update_spline)

    bevel_depth: FloatProperty(name="Depth", description="Bevel depth when not using a bevel object", default=0.015, min=0.0)

    axis: EnumProperty(name="Curve", description="The local axis of the armature that the targets and curve are created away from the source bones",
        items=[('X', 'X axis', "", "CON_LOCLIKE", 0),
        ('X_NEGATIVE', '-X axis', "", "CON_LOCLIKE", 1),
        ('Y', 'Y axis', "", "CON_LOCLIKE", 2),
        ('Y_NEGATIVE', '-Y axis', "", "CON_LOCLIKE", 3),
        ('Z', 'Z axis', "", "CON_LOCLIKE", 4),
        ('Z_NEGATIVE', '-Z axis', "", "CON_LOCLIKE", 5)],
        default='Y', update=update_spline)

    distance: FloatProperty(name="Distance", description="The distance the targets and curve are from the source bones. (in metres)", 
        default=0.3, update=update_spline)

class JK_PG_ARM_Spline_Bone(bpy.types.PropertyGroup):

    def update_bone(self, context):
        armature = self.id_data
        rigging = armature.jk_arm.rigging[armature.jk_arm.active].spline
        if not rigging.is_editing:
            # changing the source is a little complicated because we need it to remove/update rigging...
            bones = armature.data.edit_bones if armature.mode == 'EDIT' else armature.data.bones
            # deselect everything depending on mode...
            if armature.mode == 'EDIT':
                bpy.ops.armature.select_all(action='DESELECT')
            elif armature.mode == 'POSE':
                bpy.ops.pose.select_all(action='DESELECT')
            # make the new source active and save a reference of it...
            bones.active = bones.get(self.source)
            new_source, new_axis = self.source, self.axis
            # remove the rigging and set "is_editing" true...
            rigging.is_rigged, rigging.is_editing = False, True
            # while is_editing is false set the new source to what we want it to be...
            self.source, self.axis, rigging.is_editing = new_source, new_axis, False
            # then we can update the rigging...
            rigging.update_rigging(context)

    source: StringProperty(name="Source", description="Name of the source bone that does the twisting",
        default="", maxlen=63)

    origin: StringProperty(name="Origin", description="Name of the source bones original parent",
        default="", maxlen=63)
    
    gizmo: StringProperty(name="Gizmo", description="Name of the gizmo bone that follows the curve",
        default="", maxlen=63)

    stretch: StringProperty(name="Stretch", description="Name of the stretch bone that fits to the curve",
        default="", maxlen=63)

    roll: FloatProperty(name="Roll", description="The source bones roll before rigging", 
        default=0.0, subtype='ANGLE', unit='ROTATION')

    axis: EnumProperty(name="Shape Axis", description="The local axis of the bone that defines which custom shape to use",
        items=[('X', 'X axis', "", "CON_LOCLIKE", 0),
        ('X_NEGATIVE', '-X axis', "", "CON_LOCLIKE", 1),
        ('Z', 'Z axis', "", "CON_LOCLIKE", 4),
        ('Z_NEGATIVE', '-Z axis', "", "CON_LOCLIKE", 5)],
        default='Z_NEGATIVE', update=update_bone)

class JK_PG_ARM_Spline_Target(bpy.types.PropertyGroup):
    
    def update_target(self, context):
        armature = self.id_data
        rigging = armature.jk_arm.rigging[armature.jk_arm.active].spline
        if not rigging.is_editing:
            # changing the source is a little complicated because we need it to remove/update rigging...
            bones = armature.data.edit_bones if armature.mode == 'EDIT' else armature.data.bones
            # deselect everything depending on mode...
            if armature.mode == 'EDIT':
                bpy.ops.armature.select_all(action='DESELECT')
            elif armature.mode == 'POSE':
                bpy.ops.pose.select_all(action='DESELECT')
            # make the new source active and save a reference of it...
            bones.active = bones.get(self.source)
            new_source, new_use, self.use_edited = self.source, self.use, True
            # remove the rigging and set "is_editing" true...
            rigging.is_rigged, rigging.is_editing = False, True
            # while is_editing is false set the new use bool to what we want it to be...
            self.source, self.use, rigging.is_editing = new_source, new_use, False
            rigging.update_rigging(context)

    use: BoolProperty(name="Use", description="Use this bone to create a target", default=False, update=update_target)

    use_edited: BoolProperty(name="Use Edited", description="The user set this bone to use a target", default=False)

    source: StringProperty(name="Source", description="Name of the source bone to create target from",
        default="", maxlen=63)

    bone: StringProperty(name="Bone", description="Name of the target bone itself",
        default="", maxlen=63)

    origin: StringProperty(name="Origin", description="Name of the source bones original parent",
        default="", maxlen=63)

    co: FloatVectorProperty(name="Co", description="The target bones head/tail location. (used to set up the curve)",
        default=(0.0, 0.0, 0.0), size=3, subtype='TRANSLATION')

class JK_PG_ARM_Spline_Chain(bpy.types.PropertyGroup):

    def apply_transforms(self):
        # when applying transforms we need to reset the pole distance...
        armature = self.id_data
        bbs, pbs = armature.data.bones, armature.pose.bones
        parent_pb = pbs.get(self.spline.parent)
        parent_shape_scale = parent_pb.custom_shape_scale
        # this will trigger a full update of the rigging and should apply all transform differences...
        source_bb, target_bb = bbs.get(self.targets[0].source), bbs.get(self.targets[0].bone)
        start, end = source_bb.head_local, target_bb.head_local
        distance = math.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2 + (end[2] - start[2])**2)
        self.spline.bevel_depth = (distance * 0.5) * 0.1
        self.spline.distance = abs(distance)
        # but the full update will remove all added bones... (so reset custom shape scales)
        parent_pb = pbs.get(self.spline.parent)
        parent_pb.custom_shape_scale = parent_shape_scale

    targets: CollectionProperty(type=JK_PG_ARM_Spline_Target)

    bones: CollectionProperty(type=JK_PG_ARM_Spline_Bone)

    spline: PointerProperty(type=JK_PG_ARM_Spline_Curve)

    constraints: CollectionProperty(type=JK_PG_ARM_Spline_Constraint)

    drivers: CollectionProperty(type=JK_PG_ARM_Spline_Driver)

    def get_references(self):
        return get_spline_refs(self)

    def get_sources(self):
        sources = [bone.source for bone in self.bones]
        return sources

    def get_groups(self):
        groups = {
            "Chain Bones" : [bone.source for bone in self.bones],
            "Control Bones" : [self.spline.parent],
            "Gizmo Bones" : [bone.gizmo for bone in self.bones],
            "Mechanic Bones" : [bone.stretch for bone in self.bones],
            "Kinematic Targets": [target.bone for target in self.targets]}
        return groups

    def get_shapes(self):
        shapes = {
            "Bone_Shape_Default_Head_Socket" : [self.spline.parent],
            "Bone_Shape_Default_Head_Sphere" : [target.bone for target in self.targets],
            "Bone_Shape_Default_Medial_Ring_Even" : [bone.gizmo for bone in self.bones],
            "Bone_Shape_Default_Medial_Ring_Odd" : [bone.stretch for bone in self.bones]}
        return shapes

    def get_is_riggable(self):
        # we are going to need to know if the rigging in the properties is riggable...
        armature, is_riggable = self.id_data, True
        bones = armature.data.edit_bones if armature.mode == 'EDIT' else armature.data.bones
        # for this rigging we iterate on some names...
        for name in [bone.source for bone in self.bones]:
            bone = bones.get(name)
            # if those names are not existing bones...
            if bone == None:
                # this riggin' ain't riggable...
                is_riggable = False
                break
        return is_riggable

    is_riggable: BoolProperty(name="Is Riggable", description="Can this chain have it's rigging applied?",
        get=get_is_riggable)

    def update_is_rigged(self, context):
        # whenever we set "is_rigged" to false, kill the rigging...
        if not self.is_rigged:
            remove_spline_chain(self, self.id_data)

    is_rigged: BoolProperty(name="Is Rigged", description="Is this chain currently rigged?",
        default=False, update=update_is_rigged)

    is_editing: BoolProperty(name="Is Editing", description="Is this rigging being edited internally? (if it is we need to stop update functions from firing)",
        default=False)

    has_properties: BoolProperty(name="Has Properties", description="Have we added all the needed properties for this rigging?", 
        default=False)

    def update_rigging(self, context):
        # if this rigging is currently rigged, unrig it...
        if self.is_rigged:
            self.is_rigged = False
        # if it hasn't had properties created for it...
        if not self.has_properties:
            # try to get the essentials...
            get_spline_props(self, self.id_data)
            self.has_properties = True
        # always set the properties that get calculated from the essentials...
        set_spline_props(self, self.id_data)
        # if we can rig from the properties...
        if self.is_riggable:
            # add the rigging...
            add_spline_chain(self, self.id_data)
            self.is_rigged = True

    auto_roll: BoolProperty(name="Auto Roll", description="Automatically align bone rolls so all bones in the chain transform to the orientation of the targets",
        default=False, update=update_rigging)

    use_default_groups: BoolProperty(name="Use Default Groups", description="Do you want this rigging to use some default bone groups?",
        default=False, update=update_rigging)

    use_default_shapes: BoolProperty(name="Use Default Shapes", description="Do you want this rigging to use some default bone shapes?",
        default=False, update=update_rigging)

    use_default_layers: BoolProperty(name="Use Default Layers", description="Do you want this rigging to use some default armature layers?",
        default=False, update=update_rigging)

    fit_curve: FloatProperty(name="Fit Curve", description="Follow rotations from bones stretched to fit the entire curve", 
        default=0.5, min=0.0, max=1.0, subtype='FACTOR')