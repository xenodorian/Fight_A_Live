#!/usr/bin/env python3
"""Fresh slice of the Shinobi protagonist preview sheets.

Background removal is edge-connected: a pixel is only "background" if it's
reachable from the image border through other background-colored pixels
(flood fill), not just because its color happens to be close to gray. This
naturally leaves the character's own colors alone even where they're
grayish, and also sweeps up stray floating background-colored specks since
those are still connected to the border through the surrounding background.

After that cutout, every frame gets a flat, unconditional 1px erosion of
its alpha mask to remove the leftover anti-aliasing/compression fringe --
no color heuristics, just shrink the opaque region by one pixel everywhere.
"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

BG = np.array([162, 162, 162])
SEG_THRESH = 9
MERGE_DILATE = 11
LABEL_ZONE_X = 100
SPLIT_WIDTH_RATIO = 1.6

ROWS_PER_SHEET = 5
SHEET_H = 480
MIN_ROW_GAP = 4


def edge_bg_mask(rgb, close_gaps=False):
    """Background = connected to the image border through bg-colored pixels.
    close_gaps bridges single-pixel compression-dither gaps in the
    background color (common right around a tight crop's own edge) so the
    flood fill doesn't get trapped by them -- without it, those tiny gaps
    fragment the background into disconnected pockets that fail the
    border-connectivity test and get left behind as a speckled halo."""
    dist = np.abs(rgb.astype(int) - BG).sum(axis=-1)
    is_bg_color = dist < SEG_THRESH
    if close_gaps:
        # border_value=1: without it, closing's erosion pass treats pixels
        # outside the image as background, which strips the true background
        # right at the crop's own edge and disconnects it from the border
        # entirely -- the flood fill then finds nothing to anchor on.
        is_bg_color = ndimage.binary_closing(is_bg_color, iterations=2, border_value=1)
    labels, n = ndimage.label(is_bg_color)
    if n == 0:
        return np.zeros(rgb.shape[:2], dtype=bool)
    border_labels = set(labels[0, :]) | set(labels[-1, :]) | set(labels[:, 0]) | set(labels[:, -1])
    border_labels.discard(0)
    if not border_labels:
        return np.zeros(rgb.shape[:2], dtype=bool)
    return np.isin(labels, list(border_labels))


def find_row_bands(arr, expected_rows=ROWS_PER_SHEET):
    mask_fg = ~edge_bg_mask(arr)
    has_content = mask_fg.any(axis=1)

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


def split_wide_islands(islands, mask_fg):
    if len(islands) < 2:
        return islands
    widths = sorted(x1 - x0 + 1 for x0, x1 in islands)
    median_w = widths[len(widths) // 2]

    result = []
    for (x0, x1) in islands:
        w = x1 - x0 + 1
        if w > SPLIT_WIDTH_RATIO * median_w and w > 40:
            col_has = mask_fg[:, x0:x1 + 1].any(axis=0)
            gaps = []
            i = 0
            while i < len(col_has):
                if not col_has[i]:
                    j = i
                    while j < len(col_has) and not col_has[j]:
                        j += 1
                    if i > 0 and j < len(col_has):
                        gaps.append((i, j - 1))
                    i = j
                else:
                    i += 1
            if gaps:
                gx0, gx1 = max(gaps, key=lambda g: g[1] - g[0])
                split_at = x0 + (gx0 + gx1) // 2
                result.extend(split_wide_islands([(x0, split_at)], mask_fg))
                result.extend(split_wide_islands([(split_at + 1, x1)], mask_fg))
                continue
        result.append((x0, x1))
    return result


CHROMA_THRESH = 18   # max(R,G,B)-min(R,G,B) below this = essentially neutral/gray, not a real hue
MIN_BRIGHTNESS = 60  # protects near-black outline pixels, which are also low-chroma but must stay
RIM_ITERS = 3


def strip_gray_border(rgb, alpha):
    """Targeted cleanup: only remove boundary pixels that are neutral gray
    (low chroma) and light enough to be background fringe rather than the
    character's own dark outline. A pixel that's muted-but-colored (e.g.
    navy shadow) has real chroma and is left alone even at the same
    brightness as this fringe; a near-black outline pixel is protected by
    the brightness floor. Only ever touches pixels already on the boundary
    (opaque next to transparent), so interior detail is never at risk."""
    rgb = rgb.astype(int)
    chroma = rgb.max(axis=-1) - rgb.min(axis=-1)
    brightness = rgb.mean(axis=-1)
    grayish = (chroma < CHROMA_THRESH) & (brightness > MIN_BRIGHTNESS)

    mask = alpha.copy()
    for _ in range(RIM_ITERS):
        boundary = mask & ~ndimage.binary_erosion(mask)
        strip = boundary & grayish
        if not strip.any():
            break
        mask = mask & ~strip
    return mask


def process_row(row_rgb, out_dir, row_name):
    mask_fg = ~edge_bg_mask(row_rgb)
    mask_fg[:, :LABEL_ZONE_X] = False

    despeckled = ndimage.binary_opening(mask_fg, iterations=1)
    dilated = ndimage.binary_dilation(despeckled, iterations=MERGE_DILATE)
    labels, n = ndimage.label(dilated)

    islands = []
    for i in range(1, n + 1):
        ys, xs = np.where(labels == i)
        if len(xs) < 20:
            continue
        islands.append((xs.min(), xs.max()))
    islands.sort()

    islands = split_wide_islands(islands, mask_fg)
    islands.sort()

    frames = []
    for (x0, x1) in islands:
        col_slice = mask_fg[:, x0:x1 + 1]
        ys, xs = np.where(col_slice)
        if len(xs) == 0:
            continue
        fy0, fy1 = ys.min(), ys.max()
        fx0, fx1 = xs.min() + x0, xs.max() + x0
        frames.append((fx0, fy0, fx1, fy1))

    out_dir.mkdir(parents=True, exist_ok=True)
    saved = []
    rh, rw, _ = row_rgb.shape
    PAD = 4  # extra margin so the flood fill has clean background to anchor from at the crop's own border
    for idx, (x0, y0, x1, y1) in enumerate(frames):
        px0, py0 = max(0, x0 - PAD), max(0, y0 - PAD)
        px1, py1 = min(rw, x1 + 1 + PAD), min(rh, y1 + 1 + PAD)
        crop_rgb = row_rgb[py0:py1, px0:px1]

        # step 1: edge-connected background removal on the padded crop
        crop_bg = edge_bg_mask(crop_rgb, close_gaps=True)
        alpha = ~crop_bg

        # step 2: targeted removal of remaining gray border pixels only
        # (low-saturation fringe), leaving real color and dark outline alone
        alpha = strip_gray_border(crop_rgb, alpha)

        # trim back down to the tight opaque bbox (drop the padding margin)
        ys, xs = np.where(alpha)
        if len(xs) == 0:
            continue
        ty0, ty1 = ys.min(), ys.max()
        tx0, tx1 = xs.min(), xs.max()
        crop_rgb = crop_rgb[ty0:ty1 + 1, tx0:tx1 + 1]
        alpha = alpha[ty0:ty1 + 1, tx0:tx1 + 1]

        rgba = np.dstack([crop_rgb, np.where(alpha, 255, 0).astype(np.uint8)])
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
        pad = 3
        row_rgb = arr[max(0, y0 - pad):min(SHEET_H, y1 + 1 + pad)]
        saved = process_row(row_rgb, out_dir, row_name)
        report[row_name] = len(saved)
    return report


if __name__ == "__main__":
    src_dir = Path(sys.argv[1])
    out_root = Path(sys.argv[2])

    sheets = [
        ("protagonist", src_dir / "1.png", ["idle", "walk", "run", "jump", "attack1"]),
        ("protagonist", src_dir / "2.png", ["attack2", "attack3", "shield", "hurt", "dead"]),
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
