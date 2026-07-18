"""Local post-processing for Codex image projects.

This script never generates images. It joins existing local files into a
vertical long image, a contact-sheet preview, or a deterministic custom grid.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Iterable

from PIL import Image, ImageColor, ImageDraw, ImageOps, ImageStat


def load_images(paths: Iterable[str]) -> list[Image.Image]:
    images: list[Image.Image] = []
    for raw_path in paths:
        path = Path(raw_path)
        if not path.is_file():
            raise FileNotFoundError(f"image does not exist: {path}")
        with Image.open(path) as image:
            images.append(ImageOps.exif_transpose(image).convert("RGB"))
    if not images:
        raise ValueError("at least one input image is required")
    return images


def save_image(image: Image.Image, output: str) -> Path:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)
    return path


def _resize_to_common_width(images: list[Image.Image]) -> list[Image.Image]:
    width = max(image.width for image in images)
    resized: list[Image.Image] = []
    for image in images:
        if image.width == width:
            resized.append(image)
            continue
        height = round(image.height * width / image.width)
        resized.append(image.resize((width, height), Image.Resampling.LANCZOS))
    return resized


def _vertical_mask(width: int, height: int, mode: str, reverse: bool = False) -> Image.Image:
    if height < 1:
        raise ValueError("mask height must be at least 1")
    denominator = max(1, height - 1)
    values: list[int] = []
    for y in range(height):
        position = y / denominator
        if mode == "cosine":
            weight = (1 - math.cos(math.pi * position)) / 2
        elif mode == "linear":
            weight = position
        else:
            raise ValueError(f"unsupported blend mode: {mode}")
        if reverse:
            weight = 1 - weight
        values.append(round(weight * 255))
    column = Image.new("L", (1, height))
    column.putdata(values)
    return column.resize((width, height))


def _locally_match_top(
    image: Image.Image,
    reference: Image.Image,
    sample_height: int,
    span: int,
) -> Image.Image:
    sample_height = min(sample_height, image.height, reference.height)
    span = min(span, image.height)
    if sample_height < 1 or span < 1:
        return image

    reference_band = reference.crop(
        (0, reference.height - sample_height, reference.width, reference.height)
    )
    source_band = image.crop((0, 0, image.width, sample_height))
    reference_means = ImageStat.Stat(reference_band).mean[:3]
    source_means = ImageStat.Stat(source_band).mean[:3]
    offsets = [
        max(-48, min(48, round(target - source)))
        for target, source in zip(reference_means, source_means)
    ]

    lookup: list[int] = []
    for offset in offsets:
        lookup.extend(max(0, min(255, value + offset)) for value in range(256))
    adjusted = image.point(lookup)
    mask = Image.new("L", image.size, 0)
    matched_height = min(sample_height, span)
    mask.paste(255, (0, 0, image.width, matched_height))
    fade_height = span - matched_height
    if fade_height:
        fade = _vertical_mask(image.width, fade_height, "cosine", reverse=True)
        mask.paste(fade, (0, matched_height))
    return Image.composite(adjusted, image, mask)


def stitch_vertical(
    images: list[Image.Image],
    gap: int,
    background: str,
    overlap: int = 0,
    blend: str = "none",
    color_match: bool = False,
    color_match_span: int = 0,
) -> tuple[Image.Image, list[int]]:
    if gap < 0 or overlap < 0:
        raise ValueError("gap and overlap must not be negative")
    if gap and overlap:
        raise ValueError("gap and overlap cannot be used together")
    if overlap and blend == "none":
        raise ValueError("overlap requires linear or cosine blending")
    if not overlap and blend != "none":
        raise ValueError("a blend mode requires a positive overlap")
    if color_match and not overlap:
        raise ValueError("color matching requires a positive overlap")

    resized = _resize_to_common_width(images)
    width = resized[0].width
    canvas = resized[0].copy()
    seam_positions: list[int] = []

    for next_image in resized[1:]:
        if overlap >= min(canvas.height, next_image.height):
            raise ValueError("overlap must be smaller than every adjacent image")
        if color_match:
            span = color_match_span or overlap * 2
            next_image = _locally_match_top(next_image, canvas, overlap, span)

        if overlap:
            seam_start = canvas.height - overlap
            output = Image.new(
                "RGB", (width, canvas.height + next_image.height - overlap)
            )
            output.paste(canvas, (0, 0))
            previous_band = canvas.crop((0, seam_start, width, canvas.height))
            next_band = next_image.crop((0, 0, width, overlap))
            mask = _vertical_mask(width, overlap, blend)
            blended = Image.composite(next_band, previous_band, mask)
            output.paste(blended, (0, seam_start))
            output.paste(
                next_image.crop((0, overlap, width, next_image.height)),
                (0, canvas.height),
            )
            seam_positions.append(seam_start + overlap // 2)
        else:
            output = Image.new(
                "RGB",
                (width, canvas.height + gap + next_image.height),
                ImageColor.getrgb(background),
            )
            output.paste(canvas, (0, 0))
            output.paste(next_image, (0, canvas.height + gap))
            seam_positions.append(canvas.height + gap // 2)
        canvas = output
    return canvas, seam_positions


def seam_preview(
    image: Image.Image,
    seam_positions: list[int],
    band_height: int,
    gap: int = 16,
    background: str = "#111827",
) -> Image.Image:
    if band_height < 2:
        raise ValueError("seam preview height must be at least 2")
    if not seam_positions:
        raise ValueError("at least two input images are required for a seam preview")

    bands: list[Image.Image] = []
    for position in seam_positions:
        top = max(0, position - band_height // 2)
        bottom = min(image.height, top + band_height)
        top = max(0, bottom - band_height)
        band = image.crop((0, top, image.width, bottom))
        bands.append(
            ImageOps.pad(
                band,
                (image.width, band_height),
                color=ImageColor.getrgb(background),
            )
        )

    preview_height = sum(band.height for band in bands) + gap * (len(bands) - 1)
    preview = Image.new(
        "RGB", (image.width, preview_height), ImageColor.getrgb(background)
    )
    y = 0
    for band in bands:
        preview.paste(band, (0, y))
        y += band.height + gap
    return preview


def contact_sheet(
    images: list[Image.Image], columns: int, cell_width: int, gap: int, background: str
) -> Image.Image:
    if columns < 1:
        raise ValueError("columns must be at least 1")
    rows = math.ceil(len(images) / columns)
    ratios = [image.height / image.width for image in images]
    cell_height = round(cell_width * max(ratios))
    canvas_width = columns * cell_width + (columns + 1) * gap
    canvas_height = rows * cell_height + (rows + 1) * gap
    canvas = Image.new("RGB", (canvas_width, canvas_height), ImageColor.getrgb(background))

    for index, image in enumerate(images):
        thumb = ImageOps.contain(image, (cell_width, cell_height), Image.Resampling.LANCZOS)
        column = index % columns
        row = index // columns
        x = gap + column * (cell_width + gap) + (cell_width - thumb.width) // 2
        y = gap + row * (cell_height + gap) + (cell_height - thumb.height) // 2
        canvas.paste(thumb, (x, y))
    return canvas


ANCHOR_CENTERING = {
    "center": (0.5, 0.5),
    "top": (0.5, 0.0),
    "bottom": (0.5, 1.0),
    "left": (0.0, 0.5),
    "right": (1.0, 0.5),
    "top-left": (0.0, 0.0),
    "top-right": (1.0, 0.0),
    "bottom-left": (0.0, 1.0),
    "bottom-right": (1.0, 1.0),
}


def _positive_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{field} must be a positive integer")
    return value


def _non_negative_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field} must be a non-negative integer")
    return value


def _resolve_source(source: Any, paths: list[str]) -> int:
    if isinstance(source, int) and not isinstance(source, bool):
        index = source
    elif isinstance(source, str) and source.isdigit():
        index = int(source)
    elif isinstance(source, str):
        matches = [
            index
            for index, raw_path in enumerate(paths)
            if source in {Path(raw_path).name, Path(raw_path).stem}
        ]
        if len(matches) != 1:
            raise ValueError(
                f"cell source must match exactly one input image: {source}"
            )
        index = matches[0]
    else:
        raise ValueError("cell source must be an input index, filename, or stem")
    if index < 0 or index >= len(paths):
        raise ValueError(f"cell source index is out of range: {index}")
    return index


def _cell_box(
    cell: dict[str, Any],
    canvas_width: int,
    canvas_height: int,
    grid: dict[str, Any] | None,
) -> tuple[int, int, int, int, list[tuple[int, int]]]:
    if grid is None:
        x = _non_negative_int(cell.get("x"), "cell.x")
        y = _non_negative_int(cell.get("y"), "cell.y")
        width = _positive_int(cell.get("width"), "cell.width")
        height = _positive_int(cell.get("height"), "cell.height")
        if x + width > canvas_width or y + height > canvas_height:
            raise ValueError("cell extends outside the canvas")
        return x, y, width, height, []

    columns = _positive_int(grid.get("columns"), "grid.columns")
    rows = _positive_int(grid.get("rows"), "grid.rows")
    padding = _non_negative_int(grid.get("padding", 0), "grid.padding")
    gap = _non_negative_int(grid.get("gap", 0), "grid.gap")
    gap_x = _non_negative_int(grid.get("gap_x", gap), "grid.gap_x")
    gap_y = _non_negative_int(grid.get("gap_y", gap), "grid.gap_y")
    column = _non_negative_int(cell.get("column"), "cell.column")
    row = _non_negative_int(cell.get("row"), "cell.row")
    column_span = _positive_int(cell.get("column_span", 1), "cell.column_span")
    row_span = _positive_int(cell.get("row_span", 1), "cell.row_span")
    if column + column_span > columns or row + row_span > rows:
        raise ValueError("cell grid coordinates extend outside the grid")

    usable_width = canvas_width - padding * 2 - gap_x * (columns - 1)
    usable_height = canvas_height - padding * 2 - gap_y * (rows - 1)
    if usable_width < columns or usable_height < rows:
        raise ValueError("grid padding and gaps leave no usable cell area")
    unit_width = usable_width / columns
    unit_height = usable_height / rows
    x = round(padding + column * (unit_width + gap_x))
    y = round(padding + row * (unit_height + gap_y))
    right = round(x + column_span * unit_width + (column_span - 1) * gap_x)
    bottom = round(y + row_span * unit_height + (row_span - 1) * gap_y)
    occupied = [
        (grid_column, grid_row)
        for grid_row in range(row, row + row_span)
        for grid_column in range(column, column + column_span)
    ]
    return x, y, right - x, bottom - y, occupied


def _fit_cell(
    image: Image.Image,
    size: tuple[int, int],
    fit: str,
    anchor: str,
    background: str,
) -> Image.Image:
    if anchor not in ANCHOR_CENTERING:
        raise ValueError(f"unsupported cell anchor: {anchor}")
    if fit == "stretch":
        return image.resize(size, Image.Resampling.LANCZOS)
    if fit == "cover":
        return ImageOps.fit(
            image,
            size,
            Image.Resampling.LANCZOS,
            centering=ANCHOR_CENTERING[anchor],
        )
    if fit == "contain":
        contained = ImageOps.contain(image, size, Image.Resampling.LANCZOS)
        result = Image.new("RGB", size, ImageColor.getrgb(background))
        center_x, center_y = ANCHOR_CENTERING[anchor]
        x = round((size[0] - contained.width) * center_x)
        y = round((size[1] - contained.height) * center_y)
        result.paste(contained, (x, y))
        return result
    raise ValueError(f"unsupported cell fit: {fit}")


def custom_grid(
    images: list[Image.Image],
    paths: list[str],
    layout: dict[str, Any],
) -> tuple[Image.Image, dict[str, Any]]:
    canvas_spec = layout.get("canvas")
    cells = layout.get("cells")
    if not isinstance(canvas_spec, dict):
        raise ValueError("layout.canvas must be an object")
    if not isinstance(cells, list) or not cells:
        raise ValueError("layout.cells must be a non-empty list")

    width = _positive_int(canvas_spec.get("width"), "canvas.width")
    height = _positive_int(canvas_spec.get("height"), "canvas.height")
    background = str(canvas_spec.get("background", "#050816"))
    canvas = Image.new("RGB", (width, height), ImageColor.getrgb(background))
    grid = layout.get("grid")
    if grid is not None and not isinstance(grid, dict):
        raise ValueError("layout.grid must be an object")

    occupied_cells: set[tuple[int, int]] = set()
    report_cells: list[dict[str, Any]] = []
    for order, raw_cell in enumerate(cells):
        if not isinstance(raw_cell, dict):
            raise ValueError("each layout cell must be an object")
        source_index = _resolve_source(raw_cell.get("source", order), paths)
        x, y, cell_width, cell_height, occupied = _cell_box(
            raw_cell, width, height, grid
        )
        conflicts = occupied_cells.intersection(occupied)
        if conflicts:
            raise ValueError(f"grid cells overlap at: {sorted(conflicts)}")
        occupied_cells.update(occupied)

        fit = str(raw_cell.get("fit", "cover"))
        anchor = str(raw_cell.get("anchor", "center"))
        cell_background = str(raw_cell.get("background", background))
        rendered = _fit_cell(
            images[source_index],
            (cell_width, cell_height),
            fit,
            anchor,
            cell_background,
        )
        radius = _non_negative_int(raw_cell.get("radius", 0), "cell.radius")
        radius = min(radius, cell_width // 2, cell_height // 2)
        if radius:
            mask = Image.new("L", rendered.size, 0)
            ImageDraw.Draw(mask).rounded_rectangle(
                (0, 0, cell_width - 1, cell_height - 1),
                radius=radius,
                fill=255,
            )
            canvas.paste(rendered, (x, y), mask)
        else:
            canvas.paste(rendered, (x, y))

        border = raw_cell.get("border")
        if border is not None:
            if not isinstance(border, dict):
                raise ValueError("cell.border must be an object")
            border_width = _non_negative_int(
                border.get("width", 0), "cell.border.width"
            )
            if border_width:
                border_color = ImageColor.getrgb(
                    str(border.get("color", "#ffffff"))
                )
                ImageDraw.Draw(canvas).rounded_rectangle(
                    (x, y, x + cell_width - 1, y + cell_height - 1),
                    radius=radius,
                    outline=border_color,
                    width=border_width,
                )

        report_cells.append(
            {
                "order": order,
                "source": paths[source_index],
                "source_index": source_index,
                "box": [x, y, cell_width, cell_height],
                "fit": fit,
                "anchor": anchor,
            }
        )

    return canvas, {
        "canvas": {"width": width, "height": height, "background": background},
        "cells": report_cells,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    stitch = subparsers.add_parser("stitch-vertical", help="join images top to bottom")
    stitch.add_argument("images", nargs="+")
    stitch.add_argument("--output", required=True)
    stitch.add_argument("--gap", type=int, default=0)
    stitch.add_argument("--background", default="#ffffff")
    stitch.add_argument("--overlap", type=int, default=0)
    stitch.add_argument(
        "--blend", choices=("none", "linear", "cosine"), default="none"
    )
    stitch.add_argument("--color-match", action="store_true")
    stitch.add_argument("--color-match-span", type=int, default=0)
    stitch.add_argument("--seam-preview")
    stitch.add_argument("--seam-height", type=int, default=240)

    sheet = subparsers.add_parser("contact-sheet", help="build a preview grid")
    sheet.add_argument("images", nargs="+")
    sheet.add_argument("--output", required=True)
    sheet.add_argument("--columns", type=int, default=3)
    sheet.add_argument("--cell-width", type=int, default=720)
    sheet.add_argument("--gap", type=int, default=24)
    sheet.add_argument("--background", default="#f5f5f5")

    grid = subparsers.add_parser(
        "custom-grid", help="compose images with a JSON grid layout"
    )
    grid.add_argument("images", nargs="+")
    grid.add_argument("--output", required=True)
    grid.add_argument("--layout", required=True)
    grid.add_argument("--layout-report")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    images = load_images(args.images)
    if args.command == "stitch-vertical":
        result, seams = stitch_vertical(
            images,
            args.gap,
            args.background,
            args.overlap,
            args.blend,
            args.color_match,
            args.color_match_span,
        )
    elif args.command == "contact-sheet":
        result = contact_sheet(
            images, args.columns, args.cell_width, args.gap, args.background
        )
    else:
        layout_path = Path(args.layout)
        if not layout_path.is_file():
            raise FileNotFoundError(f"layout does not exist: {layout_path}")
        layout = json.loads(layout_path.read_text(encoding="utf-8"))
        result, report = custom_grid(images, args.images, layout)
    output = save_image(result, args.output)
    print(output)
    if args.command == "stitch-vertical" and args.seam_preview:
        preview = seam_preview(result, seams, args.seam_height)
        preview_output = save_image(preview, args.seam_preview)
        print(preview_output)
    if args.command == "custom-grid" and args.layout_report:
        report_path = Path(args.layout_report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(report_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
