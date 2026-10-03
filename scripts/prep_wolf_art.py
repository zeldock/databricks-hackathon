"""Prepare hand-drawn wolf art for the app: make white backgrounds transparent, shrink, and copy into web/public/wolf.

    python scripts/prep_wolf_art.py ~/Downloads/wolf-art                 # every PNG/WebP in the folder
    python scripts/prep_wolf_art.py ~/Downloads/wolf-art --map names.json # also rename (see docs/WOLF_ART_GUIDE.md)

Only white that touches the image border is removed, so white inside the art (eye whites, glints on glasses) stays.
Files that already have transparency are left as they are. Names must follow docs/WOLF_ART_GUIDE.md.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent.parent / "web" / "public" / "wolf"


def has_transparency(img: Image.Image) -> bool:
    return img.mode == "RGBA" and img.getchannel("A").getextrema()[0] < 250


def knock_out_background(img: Image.Image, thresh: int = 28) -> Image.Image:
    """Flood-fill the near-white background from every border pixel to transparent."""
    img = img.convert("RGBA")
    w, h = img.size
    seeds = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1), (w // 2, 0), (w // 2, h - 1), (0, h // 2), (w - 1, h // 2)]
    for seed in seeds:
        r, g, b, a = img.getpixel(seed)
        if a > 0 and min(r, g, b) >= 235:
            ImageDraw.floodfill(img, seed, (255, 255, 255, 0), thresh=thresh)
    return img


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder", type=Path)
    ap.add_argument("--map", type=Path, help="JSON file {\"original-name.png\": \"hat-crown.png\", ...}")
    ap.add_argument("--size", type=int, default=1200, help="shrink so the longest side is at most this many pixels")
    args = ap.parse_args()
    names = json.loads(args.map.read_text()) if args.map else {}
    OUT.mkdir(parents=True, exist_ok=True)
    done = 0
    for path in sorted(f for f in args.folder.expanduser().iterdir() if f.suffix.lower() in (".png", ".webp")):
        img = Image.open(path)
        if not has_transparency(img):
            img = knock_out_background(img)
        img.thumbnail((args.size, args.size), Image.LANCZOS)
        target = OUT / names.get(path.name, path.name)
        img.save(target, optimize=True)
        print(f"{path.name} -> {target.relative_to(OUT.parent.parent)}")
        done += 1
    print(f"{done} image(s) written to {OUT}")
    return 0 if done else 1


if __name__ == "__main__":
    sys.exit(main())
