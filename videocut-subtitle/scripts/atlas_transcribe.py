#!/usr/bin/env python3
"""Transcribe media with Atlas Cloud's xAI STT model."""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Callable, Sequence
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


BASE_URL = "https://api.atlascloud.ai/api/v1"
MODEL = "xai/stt-v1"
MAX_LOCAL_BYTES = 25 * 1024 * 1024
RETRYABLE_GET_STATUS = {429, 500, 502, 503, 504}
LANGUAGES = (
    "ar",
    "cs",
    "da",
    "nl",
    "en",
    "fil",
    "fr",
    "de",
    "hi",
    "id",
    "it",
    "ja",
    "ko",
    "mk",
    "ms",
    "fa",
    "pl",
    "pt",
    "ro",
    "ru",
    "es",
    "sv",
    "th",
    "tr",
    "vi",
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preview or execute an Atlas Cloud xAI STT request."
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", type=Path, help="Local media file (up to 25 MiB)")
    source.add_argument("--audio-url", help="Public HTTPS media URL")
    parser.add_argument("--output", type=Path, default=Path("atlas-transcript.json"))
    parser.add_argument("--language", choices=LANGUAGES)
    parser.add_argument("--text-normalization", action="store_true")
    parser.add_argument("--diarize", action="store_true")
    parser.add_argument("--filler-words", action="store_true")
    parser.add_argument("--keyterm", action="append", default=[])
    parser.add_argument("--poll-attempts", type=int, default=60)
    parser.add_argument("--poll-interval", type=float, default=2.0)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Submit the billable request; without this flag the command only previews",
    )
    return parser.parse_args(argv)


def resolve_output(path: Path, root: Path | None = None) -> Path:
    root = (root or Path.cwd()).resolve()
    output = (root / path).resolve() if not path.is_absolute() else path.resolve()
    try:
        output.relative_to(root)
    except ValueError as exc:
        raise ValueError("output must stay inside the current working directory") from exc
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing file: {output}")
    return output


def validate_args(args: argparse.Namespace) -> None:
    if args.poll_attempts < 1 or args.poll_interval < 0:
        raise ValueError("poll attempts must be positive and poll interval non-negative")
    if args.text_normalization and not args.language:
        raise ValueError("--text-normalization requires --language")
    if len(args.keyterm) > 100:
        raise ValueError("xai/stt-v1 accepts at most 100 key terms")
    if any(not term or len(term) > 50 for term in args.keyterm):
        raise ValueError("each key term must contain 1 to 50 characters")
    if args.audio_url:
        parsed = urlparse(args.audio_url)
        if parsed.scheme != "https" or not parsed.netloc:
            raise ValueError("--audio-url must be a public HTTPS URL")
        return
    if not args.input.is_file():
        raise ValueError(f"input file does not exist: {args.input}")
    size = args.input.stat().st_size
    if size == 0:
        raise ValueError("input file must not be empty")
    if size > MAX_LOCAL_BYTES:
        raise ValueError("local input exceeds 25 MiB; use --audio-url for larger media")


def audio_value(args: argparse.Namespace, preview: bool) -> str:
    if args.audio_url:
        return args.audio_url
    size = args.input.stat().st_size
    if preview:
        return f"<base64 local file: {args.input.name} ({size} bytes)>"
    return base64.b64encode(args.input.read_bytes()).decode("ascii")


def build_payload(args: argparse.Namespace, preview: bool) -> dict[str, Any]:
    validate_args(args)
    payload: dict[str, Any] = {
        "model": MODEL,
        "audio": audio_value(args, preview),
        "audio_format": "auto",
        "text_normalization": args.text_normalization,
        "diarize": args.diarize,
        "filler_words": args.filler_words,
        "keyterm": args.keyterm,
    }
    if args.language:
        payload["language"] = args.language
    return payload


def decode_response(response: Any) -> dict[str, Any]:
    payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError("Atlas Cloud returned a non-object response")
    data = payload.get("data", payload)
    if not isinstance(data, dict):
        raise RuntimeError("Atlas Cloud response is missing a data object")
    return data


def submit_once(
    payload: dict[str, Any], api_key: str, opener: Callable[..., Any]
) -> str:
    request = Request(
        f"{BASE_URL}/model/generateAudio",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "videocut-atlas-stt/1.0",
        },
        method="POST",
    )
    with opener(request, timeout=60) as response:
        prediction_id = decode_response(response).get("id")
    if not isinstance(prediction_id, str) or not prediction_id:
        raise RuntimeError("Atlas Cloud response is missing the prediction id")
    return prediction_id


def poll_prediction(
    prediction_id: str,
    api_key: str,
    attempts: int,
    interval: float,
    opener: Callable[..., Any],
    sleeper: Callable[[float], None],
) -> dict[str, Any]:
    url = f"{BASE_URL}/model/prediction/{prediction_id}"
    for attempt in range(attempts):
        request = Request(
            url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "User-Agent": "videocut-atlas-stt/1.0",
            },
            method="GET",
        )
        try:
            with opener(request, timeout=30) as response:
                result = decode_response(response)
        except HTTPError as exc:
            if exc.code not in RETRYABLE_GET_STATUS or attempt == attempts - 1:
                raise
            sleeper(min(interval * (2**attempt), 30.0))
            continue

        status = result.get("status")
        if status == "completed":
            transcription = result.get("stt_result")
            if not isinstance(transcription, dict) or not isinstance(
                transcription.get("words"), list
            ):
                raise RuntimeError("completed prediction is missing word timestamps")
            return transcription
        if status in ("failed", "timeout"):
            raise RuntimeError(
                f"Atlas Cloud transcription failed: {result.get('error', status)}"
            )
        if attempt < attempts - 1:
            sleeper(interval)
    raise TimeoutError("Atlas Cloud transcription did not complete within the polling limit")


def write_json_atomic(data: dict[str, Any], output: Path) -> int:
    output.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    fd, temporary = tempfile.mkstemp(prefix=f".{output.name}.", dir=output.parent)
    try:
        with os.fdopen(fd, "wb") as file_handle:
            file_handle.write(encoded)
            file_handle.flush()
            os.fsync(file_handle.fileno())
        os.link(temporary, output)
        os.unlink(temporary)
        return len(encoded)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def run(
    argv: Sequence[str] | None = None,
    opener: Callable[..., Any] = urlopen,
    sleeper: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    args = parse_args(argv)
    output = resolve_output(args.output)
    preview_payload = build_payload(args, preview=True)
    if not args.execute:
        result = {
            "mode": "preview",
            "billable_request_sent": False,
            "endpoint": f"{BASE_URL}/model/generateAudio",
            "payload": preview_payload,
            "output": str(output),
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return result

    api_key = os.environ.get("ATLASCLOUD_API_KEY")
    if not api_key:
        raise RuntimeError("ATLASCLOUD_API_KEY is required with --execute")
    payload = build_payload(args, preview=False)
    prediction_id = submit_once(payload, api_key, opener)
    transcription = poll_prediction(
        prediction_id,
        api_key,
        args.poll_attempts,
        args.poll_interval,
        opener,
        sleeper,
    )
    size = write_json_atomic(transcription, output)
    result = {
        "mode": "execute",
        "model": MODEL,
        "prediction_id": prediction_id,
        "output": str(output),
        "bytes": size,
        "words": len(transcription["words"]),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def main() -> int:
    try:
        run()
    except (HTTPError, OSError, RuntimeError, TimeoutError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
