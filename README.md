# B.L.E.N.D
(Blenders Life Easing Niche Developments) or B.L.E.N.D is a series of add-ons for  [Blender](https://www.blender.org/) aimed at making life a little easier, fixing common mistakes and generally filling in gaps that should maybe exist by default.

All of the stable add-ons should be pretty self explanatory from their tooltips but i will work on written guides for each of them.

I reserve my right to rename and re-organise and re-license everything as i see fit and i will not be doing backwards compatibility for previous versions of Blender.

Will fill in the contribution rules and installation methods when i find the time.

## Support Development
(Please consider supporting financially! More help = more time i can put into updates, new features and support.)

- Donate to your chosen add-on on [Gumroad](https://gumroad.com/jimkroovy) - Gives me a metric of which add-ons should get priority.
- Purchase the bundle on [Blender Market] (link coming soon!) - Gives the Blender Foundation 25% of profits.
- Support me on [Patreon](https://patreon.com/JimKroovy) - Gives you a discord server for feedback, ideas and help as well as giveaways.

## License Overview

**GNU GPL 3.0**
- All Python scripts used in Blender add-ons must have a GNU GPL compatible license. All the python scripting in the add-on(s) have a GNU GPL 3.0 License.
- See [Sharing or selling Blender add-ons (Python scripts)](https://www.blender.org/about/license/) and [GNU GPL - 3.0](https://www.gnu.org/licenses/gpl-3.0.en.html)
- "Blender’s Python API is an integral part of the software, used to define the user interface or develop tools for example. The GNU GPL license therefore requires that such scripts (if published) are being shared under a GPL compatible license. You are free to sell such scripts, but the sales then is restricted to the download service itself. Your customers will receive the script under the same license (GPL), with the same free conditions as everyone has for Blender."
- *So you can do anything you like with my Python scripts but credit is greatly appreciated.*

**CC BY 4.0**
- All .blend files and their mesh, armature, material and texture contents and anything created with them have a CC-BY license. (Creative Commons - Attribution) 
- See [Creative Commons - CC BY](https://creativecommons.org/licenses/by/4.0/)
- "All CC licenses require that others who use your work in any way must give you credit the way you request, but not in a way that suggests you endorse them or their use. If they want to use your work without giving you credit or for endorsement purposes, they must get your permission first."
- "This license allows reusers to distribute, remix, adapt, and build upon the material in any medium or format, so long as attribution is given to the creator. The license allows for commercial use."
- *Attribution conditions*
  - Do whatever you want with the .blend files but if you upload or distribute them (or any derivatives of them) you must give me credit. If you need special permissions please ask. I frequently give special permission for people using my products to create online storefront assets. (eg: The UE4 Marketplace, Blender Market, Flipped Normals, etc will require me to alter permissions so while the creator must credit me people who purchase the created assets do not have to) 
  - To give credit you must visibly state that the specific file(s) or add-on was created by Jim Kroovy and (if possible) provide links to my [Patreon](https://www.patreon.com/JimKroovy) and/or [YouTube Channel](https://www.youtube.com/c/JimKroovy). 

**By downloading any/all of these files you agree to the above licenses where applicable!**

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

