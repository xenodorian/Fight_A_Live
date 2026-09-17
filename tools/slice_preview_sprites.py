#!/usr/bin/env python3
"""Slice craftpix Shinobi preview sheets into individual frame PNGs with
background removed (chroma-keyed to alpha). Best-effort: these are the
webp *preview* screenshots (720x480, row labels baked in, no alpha), not
the original asset zip, so grid detection is done by background-color
connected-component analysis rather than known cell coordinates.
"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

BG = np.array([162, 162, 162])
SEG_THRESH = 9    # background-distance threshold used for island/label detection
ALPHA_THRESH = 24  # more generous threshold for the final alpha cutout, kills webp-compression speckle halos
MERGE_DILATE = 11  # px, merges nearby disconnected sprite parts (e.g. sword arc) into one frame island
LABEL_ZONE_X = 100  # px from left that always contains the row-name text label (measured: labels end by x=95 in every row/sheet but one); blanked out of the fg mask before dilation so it never fuses with frame 0

ROWS_PER_SHEET = 5
SHEET_H = 480
MIN_ROW_GAP = 4  # rows of all-background pixels shorter than this are noise, not a real row boundary


def find_row_bands(arr, expected_rows=ROWS_PER_SHEET):
    """Row heights in these sheets are NOT a uniform 96px grid -- jump/attack
    poses are taller than idle/walk, so a fixed division cuts into the next
    row and truncates heads. Detect real row boundaries instead, from bands
    of all-background rows spanning the full sheet width."""
    mask_fg = ~bg_mask(arr, SEG_THRESH)
    has_content = mask_fg.any(axis=1)

    # collapse gaps shorter than MIN_ROW_GAP (anti-aliasing noise, not a real row seam)
    merged = has_content.copy()
    i = 0
    h = len(has_content)
    while i < h:
        if not has_content[i]:
            j = i
            while j < h and not has_content[j]:
                j += 1
            if j - i < MIN_ROW_GAP:
                merged[i:j] = True
            i = j
        else:
            i += 1

    bands = []
    i = 0
    while i < h:
        if merged[i]:
            j = i
            while j < h and merged[j]:
                j += 1
            bands.append((i, j - 1))
            i = j
        else:
            i += 1

    assert len(bands) == expected_rows, f"expected {expected_rows} row bands, found {len(bands)}: {bands}"
    return bands


def bg_mask(arr, thresh):
    dist = np.abs(arr.astype(int) - BG).sum(axis=-1)
    return dist < thresh


def process_row(row_rgb, row_index, out_dir, char_name, row_name):
    h, w, _ = row_rgb.shape
    mask_fg = ~bg_mask(row_rgb, SEG_THRESH)
    mask_fg[:, :LABEL_ZONE_X] = False  # blank the row-name label before it can fuse with frame 0

    # remove isolated speckle pixels (webp compression noise) before merging parts
    despeckled = ndimage.binary_opening(mask_fg, iterations=1)

    # merge disconnected sprite parts (blade slashes, separated hands, etc.)
    dilated = ndimage.binary_dilation(despeckled, iterations=MERGE_DILATE)
    labels, n = ndimage.label(dilated)

    islands = []
    for i in range(1, n + 1):
        ys, xs = np.where(labels == i)
        if len(xs) < 20:
            continue
        x0, x1 = xs.min(), xs.max()
        islands.append((x0, x1))
    islands.sort()

    frames = []
    for (x0, x1) in islands:
        # tight bbox using the *real* (non-dilated, non-despeckled) fg mask within this island's x-range
        col_slice = mask_fg[:, x0:x1 + 1]
        ys, xs = np.where(col_slice)
        if len(xs) == 0:
            continue
        fy0, fy1 = ys.min(), ys.max()
        fx0, fx1 = xs.min() + x0, xs.max() + x0
        frames.append((fx0, fy0, fx1, fy1))

    out_dir.mkdir(parents=True, exist_ok=True)
    saved = []
    for idx, (x0, y0, x1, y1) in enumerate(frames):
        crop_rgb = row_rgb[y0:y1 + 1, x0:x1 + 1]
        crop_mask_bg = bg_mask(crop_rgb, ALPHA_THRESH)
        rgba = np.dstack([crop_rgb, np.full(crop_rgb.shape[:2], 255, dtype=np.uint8)])
        rgba[crop_mask_bg, 3] = 0
        img = Image.fromarray(rgba, mode="RGBA")
        fname = out_dir / f"{row_name}_{idx}.png"
        img.save(fname)
        saved.append(fname.name)
    return saved


def process_sheet(path, char_name, row_names, out_dir):
    im = Image.open(path).convert("RGB")
    arr = np.array(im)
    assert arr.shape[0] == SHEET_H, f"unexpected height {arr.shape[0]}"

    bands = find_row_bands(arr, expected_rows=len(row_names))

    report = {}
    for i, row_name in enumerate(row_names):
        y0, y1 = bands[i]
        # pad a couple rows top/bottom so nothing sits flush against the crop edge
        pad = 3
        row_rgb = arr[max(0, y0 - pad):min(SHEET_H, y1 + 1 + pad)]
        saved = process_row(row_rgb, i, out_dir, char_name, row_name)
        report[row_name] = len(saved)
    return report


if __name__ == "__main__":
    src_dir = Path(sys.argv[1])
    out_root = Path(sys.argv[2])

    sheets = [
        ("protagonist", src_dir / "Free-Shinobi-Sprites-Pixel-Art2-720x480.webp",
         ["idle", "walk", "run", "jump", "attack1"]),
        ("protagonist", src_dir / "Free-Shinobi-Sprites-Pixel-Art3-720x480.webp",
         ["attack2", "attack3", "shield", "hurt", "dead"]),
        ("enemy1", src_dir / "Free-Shinobi-Sprites-Pixel-Art4-720x480.webp",
         ["idle", "walk", "run", "jump", "attack1"]),
        ("enemy1", src_dir / "Free-Shinobi-Sprites-Pixel-Art5-720x480.webp",
         ["attack2", "attack3", "shield", "hurt", "dead"]),
        ("boss", src_dir / "Free-Shinobi-Sprites-Pixel-Art6-720x480.webp",
         ["idle", "walk", "run", "jump", "attack1"]),
        ("boss", src_dir / "Free-Shinobi-Sprites-Pixel-Art7-720x480.webp",
         ["attack2", "attack3", "shield", "hurt", "dead"]),
    ]

    full_report = {}
    for char_name, path, row_names in sheets:
        out_dir = out_root / char_name
        report = process_sheet(path, char_name, row_names, out_dir)
        full_report.setdefault(char_name, {}).update(report)

    for char, rows in full_report.items():
        print(f"== {char} ==")
        for row_name, count in rows.items():
            print(f"  {row_name}: {count} frames")
