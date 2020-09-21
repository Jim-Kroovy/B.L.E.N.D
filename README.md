# B.L.E.N.D

![Cover Image](B.L.E.N.D_Cover.jpg)

**Blenders Life Easing Niche Developments or B.L.E.N.D is a series of add-ons for [Blender](https://www.blender.org/) aimed at making life a little easier, fixing common mistakes and generally filling in gaps that should maybe exist by default and adding features from other programs that Blender could do with.**

The purpose of this project is to provide easy to use, stable and modular add-ons that you can pick and choose from. Add-ons that do not require you to do things a certain way by enforcing meta-rigs, hardcoded variables and out-dated methods. It may seem as though i am re-inventing the wheel with some of this, but when the wheel is square and you want it to fit into a round hole it requires some new angles.

Most of the add-ons in this repository are small single purpose operators, some are medium sized systems to enable specific functionality and a few will be much larger but only as complicated as you need them to be. 

All of the B.L.E.N.D add-ons will work idenpendently from each other and where relevant they will work with each other as well.

*I don't expect you to read everything in this readme so here are the contents.*

1. **Support Development:** Promotion for financial support because i put many hours into development every week.
2. **Installation:** A little explanation of downloading and installing because i don't want to have to use LFS.
3. **Contributing, Bugs and Requests:** Some rules for contributions if by some miracle anybody wants to help out.
4. **License Overview:** The licensing overview section that you should probably read.
5. **Stable Add-ons:** The list and tasks of currently stable add-ons.
6. **Unstable Add-ons:** The list and tasks of planned and work in progress add-ons that are not yet stable.

*Here are some further notes about me and this project*

- **Want to get to know me a little?** Hello i'm Jim and i have been working with Blender for 5 years and Python for a little over 2 years and i have learned many little tricks and become very familiar with almost every aspect of the Blender API so i figured it was high time i started making some improvements both for the Blender community and myself by turning all my scripts and ideas into add-ons. I thoroughly enjoy writing Python and i can easily spend 12-16 hours a day working in Blender on these add-ons if i get the chance. I'm strongest with Armatures and Rigging and weakest with Materials and Lighting. 

- **Please report any/all bugs!** This repository is going to steadily grow to contain a lot of add-ons and it will get hard to stay on top of Blender updates that might break things in individual add-ons, so any help on that front would be awesome. See section 4.

- **Request new add-ons and features!** I'm always looking for new add-on ideas both big and small and i like to implement shiny new features to the existing add-ons, feel free make requests! See section 4.

- **This is an ongoing project!** I will continue to update and improve the code of all these add-ons as i myself learn and advance my Blender and Python abilities.

- **Let there be guides!** Most of the add-ons should be pretty self explanatory from their tooltips but i will work on written and video guides for each of them.

## 1 - Support Development
*Please consider supporting financially! More help means more time i can put into updates, new features and support*

- Donate to your chosen add-on on [Gumroad](https://gumroad.com/jimkroovy) - Gives me a metric of which add-ons should get more work.
- Purchase the bundle on [Blender Market] (link coming soon!) - Gives the Blender Foundation 25% of profits.
- Support me on [Patreon](https://patreon.com/JimKroovy) - Gives you higher priority in my discord server for feedback, ideas and support.

If you want to stay up to date on what i'm working on you can also subscribe/follow me on:
- [Youtube](https://www.youtube.com/c/JimKroovy) 
- [Twitter](https://twitter.com/JimKroovy) 
- [Facebook](https://www.facebook.com/JimKroovy/) 
- [Instagram](https://www.instagram.com/jimkroovy/)

## 2 - Installation
*For the most part this is pretty straight forward... but just incase*

Okay right now this isn't too much of a problem but because i know that i will end up needing to provide .blend libraries and want to avoid Git-LFS...

- Download the add-on(s) or the full bundle from the releases section.
- Installing an add-on to Blender is as simple as Edit > Preferences > Add-ons > Install > Navigate to the .zip file > Install Add-on.
- If you want to clone and work with the repo locally you will need to extract any/all resources folders and their contents from the .zip files and then paste them into you local repo.

I'll add an instructional video here when i get the time.

## 3 - Contributing, Bugs and Requests
*I might need to have a few rules to keep me sane if people show an interest*

**Contributing:**
- All pull requests must be well described and their code must be well commented or i won't even look at them before they get rejected. *(time is money)*
- It's fine to put an "i fixed/added this" comment in the code, i'll leave it there, but credit will not be given anywhere else. *(i had to check/edit it anyway)*
- I will not be accepting anything other than scripts that do not conflict with the GPL license that all the Python falls under. *(obviously...)*

**Bugs:**
- All bug issues must use the bug template. *(i need the basic information)*
- Please check it's not already a bug before making it one. *(it's better if more people chime in on the same issues)*
- See if you can find the answer from an internet search or a written/video guide. *(i'm not a private tutor)*

**Requests:**
- All request issues must use the request template. *(like the bugs, i need the basics presented well)*
- Please check it's not already an issue before making it one. *(more input = better results)*
- Nothing too ridiculous, i'm up for a challenge but there are limitations. *(i'm not doing custom Blender builds lol)*

## 4 - License Overview
*The boring stuff i need to keep myself and my creations safe*

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
  - Do whatever you want with the .blend files and their contents but if you upload or distribute them (or any derivatives of them) you must give me credit. 
  - If you need special permissions please ask. I frequently give special permission for people using my products to create online storefront assets. For example the UE4 Marketplace or Blender Market might require me to alter permissions so that while the creator must credit me in the asset(s) people who purchase the created asset(s) do not have to. That being said i still reserve my right to decline special permissions requests. 
  - To give credit you must visibly state that the specific file(s) or add-on was created by Jim Kroovy and (if possible) provide links to my [Patreon](https://www.patreon.com/JimKroovy) and/or [YouTube Channel](https://www.youtube.com/c/JimKroovy). 

**By downloading any/all of these files you agree to the above licenses where applicable!**

## 5 - Stable Add-ons
*These add-ons should be working in the current release of Blender*

**Armature Editing Stages**
- *Properties > Armature/Bone > Stages* 
- Modular armature stages, easy to revert/progress through changes and switch between rigging on the fly.
- Tasks:
    - [x] Final bug and process check
    - [x] Make guides
    - [ ] Push rigging?
    - [ ] Release
    - [ ] Create stage presets?

**Armature Active Retargeting** 
- *Properties > Armature/Bone > Retargeting*
- Retargets actions between armatures with realtime tweaking.
- Tasks:
    - [ ] Final bug and process check (Check performance on save mapping)
    - [ ] Make guides
    - [ ] Release
    - [ ] Write binding to text operator
    - [ ] Auto bind bones function? - could take a while to write

**Armature Control Bones**
- *Properties > Controls* 
- Builds mechanism bones that manipulate the selected bones indirectly via control bones.
- Tasks:
    - [x] Make guides
    - [ ] Release
    - [ ] Add loc/rot/scale edit sync options?

**Armature Rigging Library**
- *Properties > Rigging* 
- Adds modular bits of rigging with pose controls to any armature
- Tasks:
    - [x] Final bug and process check
    - [x] Make guides
    - [ ] Release
    - [ ] Improve automatic chain keyframing?
    - [ ] Improve spline curve generation and rigging
    - [ ] Add update function to bone affixes
    - [ ] User preference bone layers
    - [ ] Facial rigging

**Armature Better Symmetrize**
- *View 3D > Armature*
- Simple little operator that symmetrizes armatures with more options than default.
- Tasks:
    - [x] Final bug and process check
    - [ ] Make guides
    - [ ] Release

**Mesh Apply Posing** 
- *View 3D > Pose*  
- Apply/Re-apply the armature modifier on meshes and apply the armature pose to rest pose.
- Tasks:
    - [ ] Add "Only Selected" bone option
    - [ ] Add "Keep Original" option
    - [ ] Final bug and process check
    - [ ] Release

**Action Rotation Mode**
- *Dope Sheet > Key*
- Simple little operator that switches the rotation mode on the fcurves of actions.
- Tasks:
    - [x] Final bug and process check
    - [ ] Make guides
    - [ ] Release
    - [ ] Make dedicated action variables

## 6 - Unstable Add-ons
*Some of these might work but i don't advise trying to use them*

**Armature Bone Mapping** 
- *Properties > Armature/Bone*
- Maps bone names to integers in order to save and transfer mesh and animation data.
- Tasks:
    - [ ] Impliment tested code
    - [ ] Integrate into other add-ons

**Scale Action Length** 
- *Dope Sheet > Key* 
- Scales the playhead of actions to the desired framerate or time.
- Tasks:
    - [ ] Finish off playhead scaling logic
    - [ ] Check selection code

**Switch Transform Space** 
- *View 3D > Toolbar > Item* 
- Adds keyable and switchable world and local space transform modes to bones and objects.
- Tasks:
    - [ ] Impliment tested code

**Switch Unit Scale** 
- Coming Soon!

**Better Action Baking** 
- Coming Soon!

**Add Group Parent** 
- Coming Soon!

**Apply Action Scale** 
- Coming Soon!

**Full Action Mirror**
- Coming Soon!

**Scene Time Warp**
- Coming Soon!