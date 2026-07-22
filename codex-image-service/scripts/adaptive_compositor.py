"""Route and execute image-composition algorithms for batch image projects.

The planning and multiband paths require Pillow and NumPy. Geometry-aware
alignment, Graph Cut, panorama stitching, optical flow, and Poisson blending
require the optional OpenCV runtime and fail closed when it is unavailable.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Any


def activate_optional_runtime() -> Path | None:
    configured = os.environ.get("CODEX_IMAGE_RUNTIME")
    candidates = [Path(configured).expanduser()] if configured else []
    candidates.append(Path.home() / ".codex" / "image-runtime")
    for candidate in candidates:
        if candidate.is_dir():
            resolved = str(candidate.resolve())
            if resolved not in sys.path:
                sys.path.insert(0, resolved)
            return candidate
    return None


OPTIONAL_RUNTIME = activate_optional_runtime()

import numpy as np
from PIL import Image, ImageOps


PROFILE_POLICIES: dict[str, dict[str, Any]] = {
    "generated-continuous": {
        "operation": "pixel-fusion",
        "pipeline": {
            "alignment": "translation",
            "seam": "overlap",
            "blend": "multiband",
        },
        "optional_dependencies": [],
        "requires_mask": False,
    },
    "panorama": {
        "operation": "geometry-aware-fusion",
        "pipeline": {
            "alignment": "homography",
            "seam": "graph-cut",
            "blend": "multiband",
        },
        "optional_dependencies": ["opencv"],
        "requires_mask": False,
    },
    "object-blend": {
        "operation": "masked-composite",
        "pipeline": {
            "alignment": "mask-placement",
            "seam": "mask-boundary",
            "blend": "poisson",
        },
        "optional_dependencies": ["opencv"],
        "requires_mask": True,
    },
    "grid": {
        "operation": "deterministic-layout",
        "pipeline": {
            "alignment": "none",
            "seam": "layout-boundaries",
            "blend": "none",
        },
        "optional_dependencies": [],
        "requires_mask": False,
    },
    "storyboard": {
        "operation": "deterministic-layout",
        "pipeline": {
            "alignment": "none",
            "seam": "layout-boundaries",
            "blend": "none",
        },
        "optional_dependencies": [],
        "requires_mask": False,
    },
    "carousel": {
        "operation": "deterministic-layout",
        "pipeline": {
            "alignment": "none",
            "seam": "page-boundaries",
            "blend": "none",
        },
        "optional_dependencies": [],
        "requires_mask": False,
    },
    "document": {
        "operation": "deterministic-layout",
        "pipeline": {
            "alignment": "none",
            "seam": "page-boundaries",
            "blend": "none",
        },
        "optional_dependencies": [],
        "requires_mask": False,
    },
    "material-kit": {
        "operation": "independent-assets-plus-layout",
        "pipeline": {
            "alignment": "none",
            "seam": "layout-boundaries",
            "blend": "none",
        },
        "optional_dependencies": [],
        "requires_mask": False,
    },
}


def has_opencv() -> bool:
    return importlib.util.find_spec("cv2") is not None


def require_opencv():
    if not has_opencv():
        raise RuntimeError(
            "selected algorithm requires the optional OpenCV runtime; "
            "refusing to fall back to hard stitching"
        )
    import cv2

    return cv2


def choose_profile(intent: str, requested: str = "auto") -> str:
    if requested != "auto":
        return requested
    normalized = intent.lower()
    if any(word in normalized for word in ("植入", "抠图", "换背景", "融合进", "局部合成")):
        return "object-blend"
    if any(word in normalized for word in ("全景", "panorama", "实拍拼接", "环拍")):
        return "panorama"
    if any(word in normalized for word in ("九宫格", "网格", "拼图", "宫格")):
        return "grid"
    if any(word in normalized for word in ("分镜", "故事板", "漫画格")):
        return "storyboard"
    if any(word in normalized for word in ("轮播", "carousel", "滑动卡片")):
        return "carousel"
    if any(word in normalized for word in ("ppt", "幻灯片", "页面", "文档配图")):
        return "document"
    if any(word in normalized for word in ("长图", "连续叙事", "连续介绍", "多屏连续")):
        return "generated-continuous"
    return "material-kit"


def build_plan(intent: str, requested: str = "auto") -> dict[str, Any]:
    profile = choose_profile(intent, requested)
    policy = PROFILE_POLICIES[profile]
    return {
        "intent": intent,
        "profile": profile,
        "operation": policy["operation"],
        "pipeline": dict(policy["pipeline"]),
        "required_dependencies": ["pillow", "numpy"],
        "optional_dependencies": list(policy["optional_dependencies"]),
        "requires_mask": policy["requires_mask"],
        "runtime": {"opencv_available": has_opencv()},
        "optional_runtime": str(OPTIONAL_RUNTIME) if OPTIONAL_RUNTIME else None,
        "fallback": "reject-or-rework",
        "decision_rule": (
            "Preserve independent assets for layout profiles; apply pixel fusion only "
            "when the delivery semantics require visual continuity."
        ),
    }


def validate_composition_project(project: dict[str, Any]) -> dict[str, Any]:
    if project.get("confirmed") is not True:
        raise ValueError("composition project must be explicitly confirmed")
    intent = str(project.get("intent", "")).strip()
    if not intent:
        raise ValueError("composition project is missing intent")
    requested_profile = str(project.get("profile", "auto"))
    if requested_profile not in {"auto", *PROFILE_POLICIES}:
        raise ValueError(f"unsupported composition profile: {requested_profile}")
    assets = project.get("assets")
    if not isinstance(assets, list) or not assets:
        raise ValueError("composition project assets must be a non-empty list")
    asset_ids: list[str] = []
    for index, asset in enumerate(assets):
        if not isinstance(asset, dict):
            raise ValueError(f"asset {index} must be an object")
        for field in ("id", "file", "purpose", "status"):
            if not str(asset.get(field, "")).strip():
                raise ValueError(f"asset {index} is missing {field}")
        asset_ids.append(str(asset["id"]))
    if len(asset_ids) != len(set(asset_ids)):
        raise ValueError("composition project asset ids must be unique")
    deliverables = project.get("deliverables")
    if not isinstance(deliverables, list) or not deliverables:
        raise ValueError("composition project deliverables must be a non-empty list")
    for index, deliverable in enumerate(deliverables):
        if not isinstance(deliverable, dict):
            raise ValueError(f"deliverable {index} must be an object")
        for field in ("id", "type", "file"):
            if not str(deliverable.get(field, "")).strip():
                raise ValueError(f"deliverable {index} is missing {field}")
    plan = build_plan(intent, requested_profile)
    declared_pipeline = project.get("pipeline")
    if declared_pipeline is not None and declared_pipeline != plan["pipeline"]:
        raise ValueError("declared pipeline does not match the selected composition profile")
    return plan


def write_json(path: str | Path, data: dict[str, Any]) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output


def load_rgb(path: str | Path) -> Image.Image:
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"image does not exist: {source}")
    with Image.open(source) as image:
        return ImageOps.exif_transpose(image).convert("RGB")


def _resize_array(array: np.ndarray, size: tuple[int, int]) -> np.ndarray:
    clipped = np.clip(array, 0, 255).astype(np.uint8)
    return np.asarray(
        Image.fromarray(clipped).resize(size, Image.Resampling.BILINEAR),
        dtype=np.float32,
    )


def _gaussian_pyramid(array: np.ndarray, levels: int) -> list[np.ndarray]:
    pyramid = [array.astype(np.float32)]
    for _ in range(levels - 1):
        height, width = pyramid[-1].shape[:2]
        if min(height, width) <= 2:
            break
        pyramid.append(
            _resize_array(pyramid[-1], (max(1, width // 2), max(1, height // 2)))
        )
    return pyramid


def _laplacian_pyramid(gaussian: list[np.ndarray]) -> list[np.ndarray]:
    result: list[np.ndarray] = []
    for index in range(len(gaussian) - 1):
        height, width = gaussian[index].shape[:2]
        expanded = _resize_array(gaussian[index + 1], (width, height))
        result.append(gaussian[index] - expanded)
    result.append(gaussian[-1])
    return result


def transition_mask(size: tuple[int, int], direction: str) -> np.ndarray:
    width, height = size
    if direction == "vertical":
        ramp = np.linspace(1.0, 0.0, height, dtype=np.float32)[:, None]
        return np.repeat(ramp, width, axis=1)
    if direction == "horizontal":
        ramp = np.linspace(1.0, 0.0, width, dtype=np.float32)[None, :]
        return np.repeat(ramp, height, axis=0)
    raise ValueError("direction must be vertical or horizontal")


def multiband_blend(
    first: Image.Image,
    second: Image.Image,
    mask: np.ndarray,
    levels: int = 5,
) -> Image.Image:
    if first.size != second.size:
        raise ValueError("multiband inputs must have identical dimensions")
    if levels < 1:
        raise ValueError("levels must be at least 1")
    first_array = np.asarray(first.convert("RGB"), dtype=np.float32)
    second_array = np.asarray(second.convert("RGB"), dtype=np.float32)
    if mask.shape != first_array.shape[:2]:
        raise ValueError("blend mask dimensions must match input images")
    mask_rgb = np.repeat(mask[:, :, None], 3, axis=2) * 255.0

    first_laplacian = _laplacian_pyramid(_gaussian_pyramid(first_array, levels))
    second_laplacian = _laplacian_pyramid(_gaussian_pyramid(second_array, levels))
    mask_gaussian = _gaussian_pyramid(mask_rgb, len(first_laplacian))
    blended_levels = []
    for left, right, level_mask in zip(
        first_laplacian, second_laplacian, mask_gaussian
    ):
        weight = np.clip(level_mask / 255.0, 0.0, 1.0)
        blended_levels.append(left * weight + right * (1.0 - weight))

    reconstructed = blended_levels[-1]
    for level in reversed(blended_levels[:-1]):
        height, width = level.shape[:2]
        reconstructed = _resize_array(reconstructed, (width, height)) + level
    return Image.fromarray(np.clip(reconstructed, 0, 255).astype(np.uint8), "RGB")


def phase_correlation_translation(
    reference: Image.Image, moving: Image.Image
) -> tuple[int, int, float]:
    if reference.size != moving.size:
        raise ValueError("translation alignment inputs must have identical dimensions")
    left = np.asarray(reference.convert("L"), dtype=np.float32)
    right = np.asarray(moving.convert("L"), dtype=np.float32)
    left -= left.mean()
    right -= right.mean()
    cross = np.fft.fft2(left) * np.conj(np.fft.fft2(right))
    magnitude = np.abs(cross)
    cross /= np.where(magnitude < 1e-9, 1.0, magnitude)
    response = np.abs(np.fft.ifft2(cross))
    peak = np.unravel_index(np.argmax(response), response.shape)
    dy, dx = int(peak[0]), int(peak[1])
    if dy > left.shape[0] // 2:
        dy -= left.shape[0]
    if dx > left.shape[1] // 2:
        dx -= left.shape[1]
    confidence = float(response[peak] / max(1e-9, response.sum()))
    return dx, dy, confidence


def shift_image(image: Image.Image, dx: int, dy: int) -> Image.Image:
    source = np.asarray(image.convert("RGB"))
    output = np.zeros_like(source)
    height, width = source.shape[:2]
    src_x0 = max(0, -dx)
    src_x1 = min(width, width - dx)
    src_y0 = max(0, -dy)
    src_y1 = min(height, height - dy)
    dst_x0 = max(0, dx)
    dst_x1 = dst_x0 + max(0, src_x1 - src_x0)
    dst_y0 = max(0, dy)
    dst_y1 = dst_y0 + max(0, src_y1 - src_y0)
    if src_x1 > src_x0 and src_y1 > src_y0:
        output[dst_y0:dst_y1, dst_x0:dst_x1] = source[
            src_y0:src_y1, src_x0:src_x1
        ]
    return Image.fromarray(output, "RGB")


def estimate_homography(
    reference: Image.Image, moving: Image.Image
) -> tuple[np.ndarray, dict[str, Any]]:
    cv2 = require_opencv()
    left = cv2.cvtColor(np.asarray(reference), cv2.COLOR_RGB2GRAY)
    right = cv2.cvtColor(np.asarray(moving), cv2.COLOR_RGB2GRAY)
    detector = cv2.ORB_create(nfeatures=4000)
    left_points, left_desc = detector.detectAndCompute(left, None)
    right_points, right_desc = detector.detectAndCompute(right, None)
    if left_desc is None or right_desc is None:
        raise ValueError("homography alignment found no usable feature descriptors")
    matches = cv2.BFMatcher(cv2.NORM_HAMMING).knnMatch(right_desc, left_desc, k=2)
    good = [first for first, second in matches if first.distance < 0.75 * second.distance]
    if len(good) < 8:
        raise ValueError(f"homography alignment needs at least 8 matches; found {len(good)}")
    source = np.float32([right_points[item.queryIdx].pt for item in good]).reshape(-1, 1, 2)
    target = np.float32([left_points[item.trainIdx].pt for item in good]).reshape(-1, 1, 2)
    matrix, inliers = cv2.findHomography(source, target, cv2.RANSAC, 4.0)
    if matrix is None or inliers is None:
        raise ValueError("homography estimation failed")
    inlier_ratio = float(inliers.mean())
    if inlier_ratio < 0.35:
        raise ValueError(f"homography inlier ratio too low: {inlier_ratio:.3f}")
    return matrix, {
        "matches": len(good),
        "inlier_ratio": inlier_ratio,
        "matrix": matrix.tolist(),
    }


def align_homography(reference: Image.Image, moving: Image.Image) -> tuple[Image.Image, dict[str, Any]]:
    cv2 = require_opencv()
    matrix, details = estimate_homography(reference, moving)
    warped = cv2.warpPerspective(
        cv2.cvtColor(np.asarray(moving), cv2.COLOR_RGB2BGR),
        matrix,
        reference.size,
    )
    return Image.fromarray(cv2.cvtColor(warped, cv2.COLOR_BGR2RGB)), details


def align_optical_flow(reference: Image.Image, moving: Image.Image) -> tuple[Image.Image, dict[str, Any]]:
    cv2 = require_opencv()
    if reference.size != moving.size:
        raise ValueError("optical-flow inputs must have identical dimensions")
    left = cv2.cvtColor(np.asarray(reference), cv2.COLOR_RGB2GRAY)
    right = cv2.cvtColor(np.asarray(moving), cv2.COLOR_RGB2GRAY)
    flow = cv2.calcOpticalFlowFarneback(right, left, None, 0.5, 4, 21, 4, 7, 1.5, 0)
    height, width = left.shape
    grid_x, grid_y = np.meshgrid(np.arange(width), np.arange(height))
    map_x = (grid_x + flow[:, :, 0]).astype(np.float32)
    map_y = (grid_y + flow[:, :, 1]).astype(np.float32)
    warped = cv2.remap(
        cv2.cvtColor(np.asarray(moving), cv2.COLOR_RGB2BGR),
        map_x,
        map_y,
        cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REFLECT,
    )
    magnitude = np.linalg.norm(flow, axis=2)
    return Image.fromarray(cv2.cvtColor(warped, cv2.COLOR_BGR2RGB)), {
        "mean_motion": float(magnitude.mean()),
        "max_motion": float(magnitude.max()),
    }


def graphcut_mask(
    first: Image.Image,
    second: Image.Image,
    first_valid: np.ndarray | None = None,
    second_valid: np.ndarray | None = None,
) -> np.ndarray:
    cv2 = require_opencv()
    if first.size != second.size:
        raise ValueError("Graph Cut inputs must have identical dimensions")
    finder_type = getattr(cv2, "detail_GraphCutSeamFinder", None)
    if finder_type is None:
        raise RuntimeError("installed OpenCV runtime does not provide Graph Cut seam finding")
    images = [
        cv2.cvtColor(np.asarray(first), cv2.COLOR_RGB2BGR).astype(np.float32),
        cv2.cvtColor(np.asarray(second), cv2.COLOR_RGB2BGR).astype(np.float32),
    ]
    masks = [
        np.full(images[0].shape[:2], 255, np.uint8)
        if mask is None
        else np.where(mask > 0, 255, 0).astype(np.uint8)
        for mask in (first_valid, second_valid)
    ]
    finder = finder_type("COST_COLOR_GRAD")
    finder.find(images, [(0, 0), (0, 0)], masks)
    first_mask = masks[0].get() if hasattr(masks[0], "get") else masks[0]
    second_mask = masks[1].get() if hasattr(masks[1], "get") else masks[1]
    denominator = first_mask.astype(np.float32) + second_mask.astype(np.float32)
    return first_mask.astype(np.float32) / np.where(denominator == 0, 255.0, denominator)


def poisson_blend(
    background: Image.Image,
    foreground: Image.Image,
    mask_path: str,
    center: tuple[int, int] | None,
) -> Image.Image:
    cv2 = require_opencv()
    mask_image = Image.open(mask_path).convert("L")
    if foreground.size != mask_image.size:
        raise ValueError("Poisson foreground and mask must have identical dimensions")
    if center is None:
        center = (background.width // 2, background.height // 2)
    result = cv2.seamlessClone(
        cv2.cvtColor(np.asarray(foreground), cv2.COLOR_RGB2BGR),
        cv2.cvtColor(np.asarray(background), cv2.COLOR_RGB2BGR),
        np.asarray(mask_image),
        center,
        cv2.NORMAL_CLONE,
    )
    return Image.fromarray(cv2.cvtColor(result, cv2.COLOR_BGR2RGB))


def stitch_panorama_pair(
    reference: Image.Image, moving: Image.Image
) -> tuple[Image.Image, dict[str, Any]]:
    cv2 = require_opencv()
    matrix, homography = estimate_homography(reference, moving)
    ref_width, ref_height = reference.size
    mov_width, mov_height = moving.size
    reference_corners = np.float32(
        [[0, 0], [ref_width, 0], [ref_width, ref_height], [0, ref_height]]
    ).reshape(-1, 1, 2)
    moving_corners = np.float32(
        [[0, 0], [mov_width, 0], [mov_width, mov_height], [0, mov_height]]
    ).reshape(-1, 1, 2)
    warped_corners = cv2.perspectiveTransform(moving_corners, matrix)
    all_corners = np.concatenate((reference_corners, warped_corners), axis=0)
    minimum = np.floor(all_corners.min(axis=0).ravel()).astype(int)
    maximum = np.ceil(all_corners.max(axis=0).ravel()).astype(int)
    translation = np.array(
        [[1.0, 0.0, -minimum[0]], [0.0, 1.0, -minimum[1]], [0.0, 0.0, 1.0]],
        dtype=np.float64,
    )
    canvas_width = int(maximum[0] - minimum[0])
    canvas_height = int(maximum[1] - minimum[1])
    if canvas_width < 1 or canvas_height < 1:
        raise ValueError("homography produced an invalid panorama canvas")

    reference_array = cv2.cvtColor(np.asarray(reference), cv2.COLOR_RGB2BGR)
    moving_array = cv2.cvtColor(np.asarray(moving), cv2.COLOR_RGB2BGR)
    reference_warped = cv2.warpPerspective(
        reference_array, translation, (canvas_width, canvas_height)
    )
    moving_warped = cv2.warpPerspective(
        moving_array, translation @ matrix, (canvas_width, canvas_height)
    )
    reference_valid = cv2.warpPerspective(
        np.full((ref_height, ref_width), 255, np.uint8),
        translation,
        (canvas_width, canvas_height),
    )
    moving_valid = cv2.warpPerspective(
        np.full((mov_height, mov_width), 255, np.uint8),
        translation @ matrix,
        (canvas_width, canvas_height),
    )
    reference_rgb = Image.fromarray(cv2.cvtColor(reference_warped, cv2.COLOR_BGR2RGB))
    moving_rgb = Image.fromarray(cv2.cvtColor(moving_warped, cv2.COLOR_BGR2RGB))
    mask = graphcut_mask(reference_rgb, moving_rgb, reference_valid, moving_valid)
    mask = np.where(reference_valid > 0, mask, 0.0)
    mask = np.where((reference_valid > 0) & (moving_valid == 0), 1.0, mask)
    result = multiband_blend(reference_rgb, moving_rgb, mask, levels=6)
    union = (reference_valid > 0) | (moving_valid > 0)
    rows, columns = np.where(union)
    if len(rows) == 0:
        raise ValueError("panorama warp produced no visible pixels")
    result = result.crop(
        (int(columns.min()), int(rows.min()), int(columns.max()) + 1, int(rows.max()) + 1)
    )
    return result, {
        "alignment": "orb-ransac-homography",
        "seam": "graph-cut",
        "blend": "multiband",
        "matches": homography["matches"],
        "inlier_ratio": homography["inlier_ratio"],
        "matrix": homography["matrix"],
        "canvas": [canvas_width, canvas_height],
    }


def stitch_panorama(paths: list[str]) -> tuple[Image.Image, dict[str, Any]]:
    if len(paths) < 2:
        raise ValueError("panorama requires at least two images")
    result = load_rgb(paths[0])
    stages: list[dict[str, Any]] = []
    for index, path in enumerate(paths[1:], start=1):
        result, details = stitch_panorama_pair(result, load_rgb(path))
        details["input_index"] = index
        stages.append(details)
    return result, {
        "alignment": "orb-ransac-homography",
        "seam": "graph-cut",
        "blend": "multiband",
        "engine": "explicit-pipeline",
        "stages": stages,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    plan = commands.add_parser("plan", help="choose a composition pipeline")
    plan.add_argument("--intent", required=True)
    plan.add_argument("--profile", choices=("auto", *PROFILE_POLICIES), default="auto")
    plan.add_argument("--output", required=True)

    validate = commands.add_parser(
        "validate-project", help="validate a confirmed batch composition project"
    )
    validate.add_argument("project")
    validate.add_argument("--report")

    blend = commands.add_parser("blend-pair", help="blend two aligned images")
    blend.add_argument("first")
    blend.add_argument("second")
    blend.add_argument("--alignment", choices=("none", "translation", "homography", "optical-flow"), default="none")
    blend.add_argument("--seam", choices=("straight", "graph-cut"), default="straight")
    blend.add_argument("--blend", choices=("multiband", "poisson"), default="multiband")
    blend.add_argument("--direction", choices=("vertical", "horizontal"), default="vertical")
    blend.add_argument("--levels", type=int, default=5)
    blend.add_argument("--mask")
    blend.add_argument("--center-x", type=int)
    blend.add_argument("--center-y", type=int)
    blend.add_argument("--output", required=True)
    blend.add_argument("--report", required=True)

    panorama = commands.add_parser("panorama", help="stitch photographic panoramas")
    panorama.add_argument("images", nargs="+")
    panorama.add_argument("--output", required=True)
    panorama.add_argument("--report", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "plan":
        output = write_json(args.output, build_plan(args.intent, args.profile))
        print(output)
        return 0
    if args.command == "validate-project":
        project_path = Path(args.project)
        if not project_path.is_file():
            raise FileNotFoundError(f"project does not exist: {project_path}")
        project = json.loads(project_path.read_text(encoding="utf-8"))
        plan = validate_composition_project(project)
        result = {"valid": True, "project": str(project_path), "routing": plan}
        if args.report:
            write_json(args.report, result)
        print(json.dumps(result, ensure_ascii=False))
        return 0

    if args.command == "panorama":
        result, details = stitch_panorama(args.images)
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        result.save(output)
        report = {
            "algorithm": "panorama",
            "pipeline": details,
            "inputs": args.images,
            "output": str(output),
            "fallback": "none",
        }
        write_json(args.report, report)
        print(output)
        return 0

    first = load_rgb(args.first)
    second = load_rgb(args.second)
    alignment_details: dict[str, Any] = {"method": args.alignment}
    if args.alignment == "translation":
        dx, dy, confidence = phase_correlation_translation(first, second)
        if confidence < 0.01:
            raise ValueError(f"translation confidence too low: {confidence:.4f}")
        second = shift_image(second, dx, dy)
        alignment_details.update({"dx": dx, "dy": dy, "confidence": confidence})
    elif args.alignment == "homography":
        second, details = align_homography(first, second)
        alignment_details.update(details)
    elif args.alignment == "optical-flow":
        second, details = align_optical_flow(first, second)
        alignment_details.update(details)

    if args.blend == "poisson":
        if not args.mask:
            raise ValueError("Poisson blending requires --mask")
        center = None
        if args.center_x is not None or args.center_y is not None:
            if args.center_x is None or args.center_y is None:
                raise ValueError("Poisson center requires both --center-x and --center-y")
            center = (args.center_x, args.center_y)
        result = poisson_blend(first, second, args.mask, center)
        seam_method = "mask-boundary"
    else:
        if first.size != second.size:
            raise ValueError("multiband blend requires equal-size aligned inputs")
        if args.seam == "graph-cut":
            mask = graphcut_mask(first, second)
            seam_method = "graph-cut"
        else:
            mask = transition_mask(first.size, args.direction)
            seam_method = "straight"
        result = multiband_blend(first, second, mask, args.levels)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    result.save(output)
    write_json(
        args.report,
        {
            "algorithm": args.blend,
            "alignment": alignment_details,
            "seam": seam_method,
            "output": str(output),
            "fallback": "none",
        },
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
