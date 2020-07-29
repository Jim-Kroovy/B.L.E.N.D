# B.L.E.N.D
(Blenders Life Easing Niche Developments) or B.L.E.N.D is a series of add-ons for  [Blender](https://www.blender.org/) aimed at making life a little easier, fixing common mistakes and generally filling in gaps that should maybe exist by default.

All of the stable add-ons should be pretty self explanatory from their tooltips but i will work on written guides for each of them.

I reserve my right to rename and re-organise and re-license everything as i see fit and i will not be doing backwards compatibility for previous versions of Blender.

Will fill in the contribution rules and installation when i find the time.

## Support Development
(Please consider supporting financially! More help = more time i can put into updates, new features and support.)

- Donate to your chosen add-on on [Gumroad](https://gumroad.com/jimkroovy) - Gives me a metric of which add-ons should get priority.
- Purchase the bundle on [Blender Market] (link coming soon!) - Gives the Blender Foundation 25% of profits.
- Support me on [Patreon](https://patreon.com/JimKroovy) - Gives you a discord server for feedback, ideas and help as well as giveaways.

## License Overview
Currently everything has a GPL-3.0 license, credit is not required but greatly appreciated.

## Stable Add-ons
*These add-ons should be working in the current release of Blender*

**Switch Rotation Mode**
- *Dope Sheet > Key*
- Simple little operator that switches the rotation mode on the fcurves of actions.
- Tasks:
    - [ ] Rename.
    - [ ] Release.

**Armature Editing Stages**
- *Properties > Armature/Bone* 
- Modular armature stages, easy to revert/progress through changes and switch between rigging on the fly.
- Tasks:
    - [ ] Rework object and data pushing to account for bones.
    - [ ] Release.

## Unstable Add-ons
*Some of these might work but i don't advise trying to use them*

**Add Control Bones**
- *View 3D > Edit Mode (Armature) > Add* 
- Builds mechanism bones that manipulate the selected bones indirectly via control bones.
- Tasks:
    - [ ] Fix the bugs with Armature Editing Stages.
    - [ ] Improve functionality.
    - [ ] Continue bug checking.

**Apply Mesh Posing** 
- *View 3D > Pose Mode (Armature) > Pose*  
- Apply/Re-apply the armature modifier on meshes and apply the armature pose to rest pose.
- Tasks:
    - [ ] Improve functionality.
    - [ ] Continue bug checking.

**Armature Action Retargeting** 
- *Properties > Armature/Bone*
- Retargets actions between armatures with realtime offset tweaking.
- Tasks:
    - [ ] Finish offset action logic.
    - [ ] Test action baking.
    - [ ] Improve functionality.
    - [ ] Check for bugs.

**Armature Bone Mapping** 
- *Properties > Armature/Bone*
- Maps bone names to integers in order to save and transfer mesh and animation data.
- Tasks:
    - [ ] Make it work.
    - [ ] Integrate into other add-ons.

**Scale Action Length** 
- *Dope Sheet > Key* 
- Scales the playhead of actions to the desired framerate or time.
- Tasks:
    - [ ] Finish off playhead scaling logic.
    - [ ] Check selection code.

**Switch Transform Space** 
- *3D View > Toolbar > Item* 
- Adds keyable and switchable world and local space transform modes to bones and objects.
- Tasks:
    - [ ] Implement tested code.

**Switch Unit Scale** 
- Coming Soon!

**Better Action Baking** 
- Coming Soon!

**Add Group Parent** 
- Coming Soon!

**Apply Action Scale** 
- Coming Soon!

