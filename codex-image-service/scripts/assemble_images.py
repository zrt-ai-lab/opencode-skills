"""Local post-processing for Codex image projects.

This script never generates images. It only joins existing local files into a
vertical long image or a contact-sheet preview.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageColor, ImageOps


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


def stitch_vertical(
    images: list[Image.Image], gap: int, background: str
) -> Image.Image:
    width = max(image.width for image in images)
    resized: list[Image.Image] = []
    for image in images:
        if image.width == width:
            resized.append(image)
            continue
        height = round(image.height * width / image.width)
        resized.append(image.resize((width, height), Image.Resampling.LANCZOS))

    total_height = sum(image.height for image in resized) + gap * (len(resized) - 1)
    canvas = Image.new("RGB", (width, total_height), ImageColor.getrgb(background))
    y = 0
    for image in resized:
        canvas.paste(image, (0, y))
        y += image.height + gap
    return canvas


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    stitch = subparsers.add_parser("stitch-vertical", help="join images top to bottom")
    stitch.add_argument("images", nargs="+")
    stitch.add_argument("--output", required=True)
    stitch.add_argument("--gap", type=int, default=0)
    stitch.add_argument("--background", default="#ffffff")

    sheet = subparsers.add_parser("contact-sheet", help="build a preview grid")
    sheet.add_argument("images", nargs="+")
    sheet.add_argument("--output", required=True)
    sheet.add_argument("--columns", type=int, default=3)
    sheet.add_argument("--cell-width", type=int, default=720)
    sheet.add_argument("--gap", type=int, default=24)
    sheet.add_argument("--background", default="#f5f5f5")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    images = load_images(args.images)
    if args.command == "stitch-vertical":
        result = stitch_vertical(images, args.gap, args.background)
    else:
        result = contact_sheet(
            images, args.columns, args.cell_width, args.gap, args.background
        )
    output = save_image(result, args.output)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
