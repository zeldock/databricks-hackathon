# Wolf art guide (hand-drawn Procreate art)

**Current set:** `wolf-happy.png` (used whenever you're studying: ecstatic / happy / content), `wolf-sad.png` (worried / sad) and `tail.png`,
plus the accessories: hats `party crown wizard gradcap fedora propeller cap_black cap_blue cap_pink cap_yellow`, eyewear `glasses square shades monocle`,
neckwear `bandana_<black|blue|pink|yellow>`, `bowtie_<black|blue|pink|yellow>` and `chain`. The Golden Halo (`halo`) is the only vector accessory.
The shop sells exactly these (see `CATALOG` in `utils/pet.py`); Back and Fur customization were removed.
The dancing wolves reuse the same drawing, recoloured with a CSS tint (`CREW_TINTS`) and given a random outfit (`web/src/components/Crew.tsx`).

Drop PNG (or WebP/SVG) files into `web/public/wolf/` — the app detects them automatically (no code changes, just refresh).
Anything that is missing falls back to the built-in vector wolf, so you can add art a piece at a time.

## Canvas
* **Square**, any size (yours is ~1920 x 1920). Export from Procreate with the **background hidden** (transparent PNG).
  If a layer has a white background, run `python scripts/prep_wolf_art.py <folder>` — it makes the outside white transparent.
* **Every layer uses the same canvas and the same wolf position**, so a hat is drawn where it sits on the head and a
  bandana where it sits on the neck. Nothing is moved or scaled by the app.

## File names
| What | File name | Notes |
|---|---|---|
| Wolf (whole body + face, no tail) | `wolf-<mood>.png` | moods: `ecstatic` `happy` `content` `worried` `sad`. A missing mood uses the nearest one you drew |
| Tail | `tail.png` | drawn behind the wolf; the app wags it |
| Hats | `hat-<id>.png` | |
| Eyewear | `eyewear-<id>.png` | |
| Neckwear | `neck-<id>.png` | |
| Back items | `back-<id>.png` | drawn behind the wolf; optional `back-backpack-front.png` for straps in front |
| Scenes | `scene-<id>.png` | full background, any square size |
| Other fur colours (optional) | `wolf-<mood>-<fur>.png`, `tail-<fur>.png` | `fur_snow` `fur_midnight` `fur_ember` `fur_emerald` `fur_golden`. Without these, the grey wolf is tinted |

`<id>` is the item id in `utils/pet.py` (for example `hat-crown.png`, `neck-bandana.png`). To add a brand-new item, add it to
the catalog in `utils/pet.py` (with a `slot`) and drop `<slot>-<id>.png` in the folder.

## Tuning the position
If the art sits a little off in the app, change the three numbers in `ART` near the bottom of `web/src/components/Wolf.tsx`
(`s` = size, `x`/`y` = offset) — it moves every layer together.

## Rename from a file list
`python scripts/prep_wolf_art.py ~/Downloads/wolf-art --map names.json` with a JSON like
`{"IMG_001.png": "wolf-content.png", "IMG_002.png": "wolf-sad.png", "IMG_003.png": "hat-crown.png"}`.
