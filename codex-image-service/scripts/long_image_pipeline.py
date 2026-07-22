"""Validate and prepare interfaces for continuous long-image projects."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from PIL import Image, ImageOps, ImageStat


REQUIRED_SEAM_FIELDS = {
    "from",
    "to",
    "shared_element",
    "direction",
    "color_light",
    "safe_zone_ratio",
    "method",
    "status",
    "interface",
    "comparison_report",
}


def load_image(path: str | Path) -> Image.Image:
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"image does not exist: {source}")
    with Image.open(source) as image:
        return ImageOps.exif_transpose(image).convert("RGB")


def extract_interface(image: Image.Image, edge: str, ratio: float) -> Image.Image:
    if not 0 < ratio < 0.5:
        raise ValueError("interface ratio must be greater than 0 and below 0.5")
    height = max(1, round(image.height * ratio))
    if edge == "top":
        return image.crop((0, 0, image.width, height))
    if edge == "bottom":
        return image.crop((0, image.height - height, image.width, image.height))
    raise ValueError(f"unsupported interface edge: {edge}")


def _sample_pair(
    first: Image.Image, second: Image.Image, sample_width: int = 96
) -> tuple[Image.Image, Image.Image]:
    height = max(
        16,
        round(
            sample_width
            * ((first.height / first.width) + (second.height / second.width))
            / 2
        ),
    )
    size = (sample_width, min(160, height))
    return (
        first.resize(size, Image.Resampling.LANCZOS),
        second.resize(size, Image.Resampling.LANCZOS),
    )


def interface_similarity(first: Image.Image, second: Image.Image) -> float:
    first, second = _sample_pair(first.convert("RGB"), second.convert("RGB"))
    first_gray = list(first.convert("L").getdata())
    second_gray = list(second.convert("L").getdata())
    first_mean = sum(first_gray) / len(first_gray)
    second_mean = sum(second_gray) / len(second_gray)
    first_variance = sum((value - first_mean) ** 2 for value in first_gray)
    second_variance = sum((value - second_mean) ** 2 for value in second_gray)
    if first_variance < 1e-9 or second_variance < 1e-9:
        correlation = 1.0 if first_gray == second_gray else 0.0
    else:
        numerator = sum(
            (left - first_mean) * (right - second_mean)
            for left, right in zip(first_gray, second_gray)
        )
        correlation = numerator / math.sqrt(first_variance * second_variance)
        correlation = max(-1.0, min(1.0, correlation))
        correlation = (correlation + 1.0) / 2.0

    first_color = ImageStat.Stat(first).mean[:3]
    second_color = ImageStat.Stat(second).mean[:3]
    color_distance = sum(
        abs(left - right) for left, right in zip(first_color, second_color)
    ) / (3 * 255)
    color_similarity = max(0.0, 1.0 - color_distance)
    return round(correlation * 0.8 + color_similarity * 0.2, 6)


def find_best_overlap(
    previous: Image.Image,
    following: Image.Image,
    min_ratio: float = 0.08,
    max_ratio: float = 0.2,
) -> tuple[int, float]:
    if not 0 < min_ratio <= max_ratio < 0.5:
        raise ValueError("overlap ratios must satisfy 0 < min <= max < 0.5")
    minimum_height = min(previous.height, following.height)
    minimum = max(2, round(minimum_height * min_ratio))
    maximum = max(minimum, round(minimum_height * max_ratio))
    best_overlap = minimum
    best_score = -1.0
    for overlap in range(minimum, maximum + 1):
        previous_band = previous.crop(
            (0, previous.height - overlap, previous.width, previous.height)
        )
        following_band = following.crop((0, 0, following.width, overlap))
        score = interface_similarity(previous_band, following_band)
        if score > best_score or (
            math.isclose(score, best_score, abs_tol=1e-6)
            and overlap > best_overlap
        ):
            best_overlap = overlap
            best_score = score
    return best_overlap, best_score


def compare_image_interfaces(
    previous: Image.Image, following: Image.Image, ratio: float
) -> float:
    previous_band = extract_interface(previous, "bottom", ratio)
    following_band = extract_interface(following, "top", ratio)
    return interface_similarity(previous_band, following_band)


def validate_project(project: dict[str, Any]) -> None:
    mode = project.get("mode")
    if mode not in {"continuous", "cards"}:
        raise ValueError("project.mode must be continuous or cards")
    if project.get("confirmed") is not True:
        raise ValueError("project must be explicitly confirmed before generation")
    screens = project.get("screens")
    if not isinstance(screens, list) or len(screens) < 2:
        raise ValueError("project.screens must contain at least 2 screens")
    screen_ids: list[str] = []
    for index, screen in enumerate(screens):
        if not isinstance(screen, dict):
            raise ValueError(f"screen {index} must be an object")
        for field in ("id", "file", "prompt"):
            if not str(screen.get(field, "")).strip():
                raise ValueError(f"screen {index} is missing {field}")
        screen_ids.append(str(screen["id"]))
    if len(screen_ids) != len(set(screen_ids)):
        raise ValueError("screen ids must be unique")

    seams = project.get("seams")
    expected = len(screens) - 1
    if not isinstance(seams, list) or len(seams) != expected:
        raise ValueError(f"continuous project requires exactly {expected} seam entries")
    if mode == "cards":
        return
    for index, screen in enumerate(screens):
        if index > 0:
            top_interface = str(screen.get("top_interface", "")).strip()
            references = screen.get("references")
            if not top_interface:
                raise ValueError(f"screen {index} is missing top_interface")
            if not isinstance(references, list):
                raise ValueError(f"screen {index} references must be a list")
            required_references = {str(screens[index - 1]["file"]), top_interface}
            if not required_references.issubset({str(item) for item in references}):
                raise ValueError(
                    f"screen {index} references must include the previous screen and top_interface"
                )
        if index < len(screens) - 1 and not str(
            screen.get("bottom_interface", "")
        ).strip():
            raise ValueError(f"screen {index} is missing bottom_interface")
    for index, seam in enumerate(seams):
        if not isinstance(seam, dict):
            raise ValueError(f"seam {index} must be an object")
        missing = sorted(
            field
            for field in REQUIRED_SEAM_FIELDS
            if field not in seam or seam[field] in (None, "")
        )
        if missing:
            raise ValueError(f"seam {index} is missing fields: {', '.join(missing)}")
        if str(seam["from"]) != screen_ids[index] or str(seam["to"]) != screen_ids[index + 1]:
            raise ValueError(f"seam {index} does not connect adjacent screens")
        ratio = seam["safe_zone_ratio"]
        if isinstance(ratio, bool) or not isinstance(ratio, (int, float)):
            raise ValueError(f"seam {index} safe_zone_ratio must be numeric")
        if not 0.08 <= float(ratio) <= 0.25:
            raise ValueError(f"seam {index} safe_zone_ratio must be between 0.08 and 0.25")
        if seam["method"] not in {"overlap", "bridge"}:
            raise ValueError(f"seam {index} method must be overlap or bridge")
        if seam["status"] != "confirmed":
            raise ValueError(f"seam {index} must be confirmed")
        if str(seam["interface"]) != str(screens[index]["bottom_interface"]):
            raise ValueError(
                f"seam {index} interface must match screen {index} bottom_interface"
            )
        if str(seam["interface"]) != str(screens[index + 1]["top_interface"]):
            raise ValueError(
                f"seam {index} interface must match screen {index + 1} top_interface"
            )


def write_json(path: str | Path, data: dict[str, Any]) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    extract = commands.add_parser("extract-interface")
    extract.add_argument("image")
    extract.add_argument("--edge", choices=("top", "bottom"), required=True)
    extract.add_argument("--ratio", type=float, default=0.15)
    extract.add_argument("--output", required=True)

    compare = commands.add_parser("compare-interfaces")
    compare.add_argument("previous")
    compare.add_argument("following")
    compare.add_argument("--ratio", type=float, default=0.15)
    compare.add_argument("--threshold", type=float, default=0.72)
    compare.add_argument("--report")

    validate = commands.add_parser("validate-project")
    validate.add_argument("project")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "extract-interface":
        interface = extract_interface(load_image(args.image), args.edge, args.ratio)
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        interface.save(output)
        print(output)
        return 0
    if args.command == "compare-interfaces":
        score = compare_image_interfaces(
            load_image(args.previous), load_image(args.following), args.ratio
        )
        result = {
            "previous": args.previous,
            "following": args.following,
            "ratio": args.ratio,
            "threshold": args.threshold,
            "score": score,
            "passed": score >= args.threshold,
        }
        if args.report:
            write_json(args.report, result)
        print(json.dumps(result, ensure_ascii=False))
        if not result["passed"]:
            raise ValueError(
                f"interface score {score:.3f} is below threshold {args.threshold:.3f}"
            )
        return 0

    project_path = Path(args.project)
    if not project_path.is_file():
        raise FileNotFoundError(f"project does not exist: {project_path}")
    project = json.loads(project_path.read_text(encoding="utf-8"))
    validate_project(project)
    print("valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
