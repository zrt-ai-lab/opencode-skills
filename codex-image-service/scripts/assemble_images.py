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

from long_image_pipeline import (
    find_best_overlap,
    interface_similarity,
    validate_project,
    write_json,
)


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


def _project_resource(project_path: Path, raw_path: Any) -> Path:
    resource = Path(str(raw_path))
    if not resource.is_absolute():
        resource = project_path.parent / resource
    return resource.resolve()


def validate_stitch_project(
    raw_project_path: str,
    image_paths: list[str],
    mode: str,
    min_seam_score: float,
) -> dict[str, Any]:
    project_path = Path(raw_project_path)
    if not project_path.is_file():
        raise FileNotFoundError(f"project does not exist: {project_path}")
    project = json.loads(project_path.read_text(encoding="utf-8"))
    validate_project(project)
    if project["mode"] != mode:
        raise ValueError(
            f"project mode {project['mode']} does not match stitch mode {mode}"
        )

    screens = project["screens"]
    if len(screens) != len(image_paths):
        raise ValueError("project screen count must match stitch input count")
    actual_inputs = [Path(path).resolve() for path in image_paths]
    declared_inputs = [
        _project_resource(project_path, screen["file"]) for screen in screens
    ]
    if declared_inputs != actual_inputs:
        raise ValueError(
            "stitch inputs must match project screens exactly and in declared order"
        )

    if mode == "continuous":
        for index, seam in enumerate(project["seams"]):
            interface_path = _project_resource(project_path, seam["interface"])
            if not interface_path.is_file():
                raise FileNotFoundError(
                    f"seam {index} interface does not exist: {interface_path}"
                )
            report_path = _project_resource(project_path, seam["comparison_report"])
            if not report_path.is_file():
                raise FileNotFoundError(
                    f"seam {index} comparison report does not exist: {report_path}"
                )
            comparison = json.loads(report_path.read_text(encoding="utf-8"))
            if comparison.get("passed") is not True:
                raise ValueError(f"seam {index} comparison report did not pass")
            score = comparison.get("score")
            if isinstance(score, bool) or not isinstance(score, (int, float)):
                raise ValueError(f"seam {index} comparison score must be numeric")
            if float(score) < min_seam_score:
                raise ValueError(
                    f"seam {index} comparison score {float(score):.3f} "
                    f"is below {min_seam_score:.3f}"
                )
            expected_previous = actual_inputs[index]
            expected_following = actual_inputs[index + 1]
            reported_previous = _project_resource(
                report_path, comparison.get("previous", "")
            )
            reported_following = _project_resource(
                report_path, comparison.get("following", "")
            )
            if (reported_previous, reported_following) != (
                expected_previous,
                expected_following,
            ):
                raise ValueError(
                    f"seam {index} comparison report does not match adjacent inputs"
                )
    return project


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
    mode: str,
    gap: int,
    background: str,
    overlap: int | str,
    blend: str,
    color_match: bool,
    color_match_span: int = 0,
    min_overlap_ratio: float = 0.08,
    max_overlap_ratio: float = 0.2,
    min_seam_score: float = 0.72,
    alignment: str = "translation",
    max_horizontal_shift_ratio: float = 0.08,
    min_alignment_confidence: float = 0.01,
) -> tuple[Image.Image, list[dict[str, Any]]]:
    if mode not in {"continuous", "cards"}:
        raise ValueError("mode must be continuous or cards")
    if gap < 0:
        raise ValueError("gap must not be negative")
    if not 0 <= min_seam_score <= 1:
        raise ValueError("min seam score must be between 0 and 1")
    if alignment not in {"none", "translation"}:
        raise ValueError("vertical stitch alignment must be none or translation")
    if not 0 <= max_horizontal_shift_ratio <= 0.25:
        raise ValueError("max horizontal shift ratio must be between 0 and 0.25")
    if not 0 <= min_alignment_confidence <= 1:
        raise ValueError("minimum alignment confidence must be between 0 and 1")
    if mode == "cards":
        if overlap not in {0, "0"}:
            raise ValueError("cards mode does not allow overlap; use gap for separation")
        if blend != "none" or color_match:
            raise ValueError("cards mode does not use blending or color matching")
    else:
        if gap:
            raise ValueError("continuous mode does not allow gaps")
        if overlap in {0, "0"}:
            raise ValueError("continuous mode forbids zero-overlap hard stitching")
        if blend not in {"linear", "cosine", "multiband"}:
            raise ValueError(
                "continuous mode requires linear, cosine, or multiband blending"
            )

    resized = _resize_to_common_width(images)
    width = resized[0].width
    canvas = resized[0].copy()
    previous_image = resized[0]
    seam_records: list[dict[str, Any]] = []

    for index, next_image in enumerate(resized[1:], start=1):
        if mode == "cards":
            output = Image.new(
                "RGB",
                (width, canvas.height + gap + next_image.height),
                ImageColor.getrgb(background),
            )
            output.paste(canvas, (0, 0))
            output.paste(next_image, (0, canvas.height + gap))
            seam_records.append(
                {
                    "from_index": index - 1,
                    "to_index": index,
                    "position": canvas.height + gap // 2,
                    "overlap": 0,
                    "score": None,
                    "mode": "cards",
                }
            )
            canvas = output
            previous_image = next_image
            continue

        if overlap == "auto":
            actual_overlap, score = find_best_overlap(
                previous_image,
                next_image,
                min_overlap_ratio,
                max_overlap_ratio,
            )
        else:
            actual_overlap = int(overlap)
            if actual_overlap < 1:
                raise ValueError("continuous overlap must be positive or auto")
            previous_band = previous_image.crop(
                (
                    0,
                    previous_image.height - actual_overlap,
                    previous_image.width,
                    previous_image.height,
                )
            )
            next_band = next_image.crop((0, 0, next_image.width, actual_overlap))
            score = interface_similarity(previous_band, next_band)

        if actual_overlap >= min(previous_image.height, next_image.height):
            raise ValueError("overlap must be smaller than every adjacent image")
        alignment_record: dict[str, Any] = {"method": "none"}
        if alignment == "translation":
            from adaptive_compositor import phase_correlation_translation, shift_image

            previous_band = previous_image.crop(
                (
                    0,
                    previous_image.height - actual_overlap,
                    previous_image.width,
                    previous_image.height,
                )
            )
            next_band = next_image.crop((0, 0, next_image.width, actual_overlap))
            dx, dy, confidence = phase_correlation_translation(
                previous_band, next_band
            )
            maximum_shift = round(width * max_horizontal_shift_ratio)
            if confidence >= min_alignment_confidence and abs(dx) <= maximum_shift:
                candidate = shift_image(next_image, dx, 0)
                candidate_band = candidate.crop((0, 0, width, actual_overlap))
                candidate_score = interface_similarity(previous_band, candidate_band)
                if candidate_score >= score:
                    next_image = candidate
                    score = candidate_score
                    alignment_record = {
                        "method": "translation",
                        "dx": dx,
                        "detected_dy": dy,
                        "applied_dy": 0,
                        "confidence": confidence,
                    }
        if score < min_seam_score:
            raise ValueError(
                "no trustworthy overlap for seam "
                f"{index - 1}->{index}: score {score:.3f} below {min_seam_score:.3f}"
            )
        if color_match:
            span = color_match_span or actual_overlap * 2
            next_image = _locally_match_top(
                next_image, previous_image, actual_overlap, span
            )

        seam_start = canvas.height - actual_overlap
        output = Image.new(
            "RGB", (width, canvas.height + next_image.height - actual_overlap)
        )
        output.paste(canvas, (0, 0))
        previous_band = canvas.crop((0, seam_start, width, canvas.height))
        next_band = next_image.crop((0, 0, width, actual_overlap))
        if blend == "multiband":
            from adaptive_compositor import multiband_blend, transition_mask

            blended = multiband_blend(
                previous_band,
                next_band,
                transition_mask((width, actual_overlap), "vertical"),
            )
        else:
            mask = _vertical_mask(width, actual_overlap, blend)
            blended = Image.composite(next_band, previous_band, mask)
        output.paste(blended, (0, seam_start))
        output.paste(
            next_image.crop((0, actual_overlap, width, next_image.height)),
            (0, canvas.height),
        )
        seam_records.append(
            {
                "from_index": index - 1,
                "to_index": index,
                "position": seam_start + actual_overlap // 2,
                "overlap": actual_overlap,
                "score": score,
                "mode": "continuous",
                "alignment": alignment_record,
                "seam": "overlap",
                "blend": blend,
            }
        )
        canvas = output
        previous_image = next_image
    return canvas, seam_records


def seam_preview(
    image: Image.Image,
    seam_records: list[dict[str, Any]],
    band_height: int,
    gap: int = 16,
    background: str = "#111827",
) -> Image.Image:
    if band_height < 2:
        raise ValueError("seam preview height must be at least 2")
    if not seam_records:
        raise ValueError("at least two input images are required for a seam preview")

    bands: list[Image.Image] = []
    for seam in seam_records:
        position = int(seam["position"])
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
    stitch.add_argument("--mode", choices=("continuous", "cards"), required=True)
    stitch.add_argument("--output", required=True)
    stitch.add_argument(
        "--project", help="validated long-image project JSON; required for continuous mode"
    )
    stitch.add_argument("--gap", type=int, default=0)
    stitch.add_argument("--background", default="#ffffff")
    stitch.add_argument("--overlap", default=None, help="positive pixels or auto")
    stitch.add_argument(
        "--blend", choices=("none", "linear", "cosine", "multiband"), default=None
    )
    stitch.add_argument(
        "--color-match", action=argparse.BooleanOptionalAction, default=None
    )
    stitch.add_argument("--color-match-span", type=int, default=0)
    stitch.add_argument("--seam-preview")
    stitch.add_argument("--seam-height", type=int, default=240)
    stitch.add_argument("--seam-report")
    stitch.add_argument("--min-overlap-ratio", type=float, default=0.08)
    stitch.add_argument("--max-overlap-ratio", type=float, default=0.2)
    stitch.add_argument("--min-seam-score", type=float, default=0.72)
    stitch.add_argument(
        "--alignment", choices=("none", "translation"), default="translation"
    )
    stitch.add_argument("--max-horizontal-shift-ratio", type=float, default=0.08)
    stitch.add_argument("--min-alignment-confidence", type=float, default=0.01)

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
        if args.mode == "continuous":
            if not args.seam_preview:
                raise ValueError("continuous mode requires --seam-preview")
            if not args.seam_report:
                raise ValueError("continuous mode requires --seam-report")
            if not args.project:
                raise ValueError("continuous mode requires --project")
            validate_stitch_project(
                args.project, args.images, args.mode, args.min_seam_score
            )
            overlap: int | str = args.overlap or "auto"
            blend = args.blend or "multiband"
            color_match = True if args.color_match is None else args.color_match
        else:
            overlap = int(args.overlap or 0)
            blend = args.blend or "none"
            color_match = False if args.color_match is None else args.color_match
        result, seams = stitch_vertical(
            images,
            args.mode,
            args.gap,
            args.background,
            overlap,
            blend,
            color_match,
            args.color_match_span,
            args.min_overlap_ratio,
            args.max_overlap_ratio,
            args.min_seam_score,
            args.alignment,
            args.max_horizontal_shift_ratio,
            args.min_alignment_confidence,
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
    if args.command == "stitch-vertical" and args.seam_report:
        report = {
            "mode": args.mode,
            "project": args.project,
            "images": args.images,
            "output": str(output),
            "seams": seams,
        }
        report_output = write_json(args.seam_report, report)
        print(report_output)
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
