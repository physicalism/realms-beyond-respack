# Chef Ivy: red kibble bowl trial

13 November 2026: replaced carrot and bread with a full red kibble bowl. The 16 × 32 texture retains the original first 23 rows exactly, including hat, face, tongue, and green neckerchief. Lower nine rows are sampled from the generated concept. Item ID, model, UVs, and frame remain unchanged.

Regenerate from the pack root: `python3 tools/chef-ivy/generate.py`.

Revert from the pack root:

```sh
cp builds/chef-ivy-backups/ivy_chef-before-kibble-2026-11-13.png assets/realm/textures/item/painting/ivy_chef.png
```

`source/original.png` is also an exact pre-edit copy. Do not regenerate after reverting unless the bowl is wanted again. Preview: `builds/chef-ivy/kibble-preview.png`. Henry approved the bowl version before the spoon edit. Asset validation passed; in-game appearance of subsequent changes still needs review. No version bump or release.

## Wooden spoon

Added a wooden spoon in the paw on the viewer's left, sampled from `source/spoon-concept.png`. Only warm wooden pixels in the spoon area are imported; all other approved bowl-version pixels are preserved. Validation passed; in-game spoon appearance still needs review.

To restore the approved bowl version, copy `builds/chef-ivy-backups/ivy_chef-approved-bowl-before-spoon-2026-11-13.png` over `assets/realm/textures/item/painting/ivy_chef.png` and restore the generator from `builds/chef-ivy-backups/generate-before-spoon-2026-11-13.py` to `tools/chef-ivy/generate.py`.

## Larger tilted spoon revision

After the in-game screenshot showed the first spoon reading as a stick, enlarged the head, added a darker cup and lighter rim, and tilted the handle down towards the paw. Source: `source/spoon-tilted-concept.png`. All pixels outside the spoon area remain identical to the approved bowl portrait. Validation passed; revised in-game appearance awaits review. Prior spoon texture and generator are backed up as `ivy_chef-before-tilted-spoon-2026-11-13.png` and `generate-before-tilted-spoon-2026-11-13.py` under `builds/chef-ivy-backups/`.

## Carrots and apples trial

Replaced the bowl and kibble with carrots on the left and red apples on the right, resting on the counter. Retained the tilted wooden spoon and original upper portrait. Source: `source/carrots-apples-concept.png`; regenerate with the same script. Upper 23 rows verified unchanged from the previous spoon version. Asset validation passed; in-game review pending.

To revert this trial, restore `builds/chef-ivy-backups/ivy_chef-bowl-and-tilted-spoon-2026-11-13.png` to `assets/realm/textures/item/painting/ivy_chef.png` and `builds/chef-ivy-backups/generate-bowl-and-tilted-spoon-2026-11-13.py` to `tools/chef-ivy/generate.py`. No version bump, commit, or publication.

## Current: kibble bowl and carrot, no spoon

Restored a full red kibble bowl with one carrot beside it, removed the apples and spoon. Source: `source/kibble-carrot-concept.png`. Generator now imports this foreground without applying any spoon overlay. Upper 23 rows match the original portrait exactly. Validation passed; in-game appearance awaits review. The previous apples/carrot/spoon texture and generator are saved under `builds/chef-ivy-backups/ivy_chef-apples-carrots-spoon-2026-11-13.png` and `generate-apples-carrots-spoon-2026-11-13.py`. No commit, version bump, or publication.

## Current: original collar, two carrots, kibble bowl

Restored the original collar/tag row by extending the protected original portrait to the first 24 rows. Two carrots now sit to the left of the full red kibble bowl; no spoon. Source: `source/kibble-two-carrots-concept.png`. First 24 rows verified pixel-for-pixel against `source/original.png`; validation passed. In-game appearance pending review. Previous texture/generator saved as `ivy_chef-before-two-carrots-2026-11-13.png` and `generate-before-two-carrots-2026-11-13.py` in `builds/chef-ivy-backups/`. No commit, release, or version bump.

## Current workflow: complete high-resolution remake

At Henry's request, replaced the patch-and-overlay workflow with one complete high-resolution painting: `source/full-painting-kibble-two-carrots.png`. It includes the olive collar and gold tag, full red kibble bowl, two carrots, and no spoon. `generate.py` area-averages the entire 1:2 portrait to 16 × 32 in one pass. No rows, collar pixels, or foreground pieces are pasted from older textures. The preview is a nearest-neighbour enlargement of the actual installed texture.

Regenerate: `python3 tools/chef-ivy/generate.py`. Asset validation passed; in-game review is pending. Model, item ID, and frame are unchanged. Previous texture and generator are backed up as `builds/chef-ivy-backups/ivy_chef-before-full-remake-2026-11-13.png` and `generate-before-full-remake-2026-11-13.py`; restore both to revert. No commit, version bump, or publication.

## Current: all painting edits reverted

Henry requested reverting all changes to the painting. The live texture is restored byte-for-byte from `builds/chef-ivy-backups/ivy_chef-before-kibble-2026-11-13.png`, the original carrot-and-bread version. The generator now restores that original rather than reapplying any trial. Experiments remain only as source/backups.
