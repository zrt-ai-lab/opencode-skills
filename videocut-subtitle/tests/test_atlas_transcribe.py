import importlib.util
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError


SCRIPT = Path(__file__).parents[1] / "scripts" / "atlas_transcribe.py"
SPEC = importlib.util.spec_from_file_location("atlas_transcribe", SCRIPT)
atlas_transcribe = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(atlas_transcribe)


class FakeResponse:
    def __init__(self, body):
        self.body = json.dumps(body).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self.body


class AtlasTranscribeTests(unittest.TestCase):
    def test_preview_uses_placeholder_without_network(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            media = root / "clip.mp4"
            media.write_bytes(b"media")

            def opener(*_args, **_kwargs):
                raise AssertionError("preview must not access the network")

            with patch.object(Path, "cwd", return_value=root), redirect_stdout(
                io.StringIO()
            ):
                result = atlas_transcribe.run(
                    ["--input", str(media)], opener=opener
                )

        self.assertEqual("preview", result["mode"])
        self.assertFalse(result["billable_request_sent"])
        self.assertEqual("<base64 local file: clip.mp4 (5 bytes)>", result["payload"]["audio"])

    def test_submit_failure_is_not_retried(self):
        requests = []

        def opener(request, **_kwargs):
            requests.append(request)
            raise HTTPError(request.full_url, 503, "unavailable", {}, None)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(Path, "cwd", return_value=root), patch.dict(
                os.environ, {"ATLASCLOUD_API_KEY": "test-key"}
            ), self.assertRaises(HTTPError):
                atlas_transcribe.run(
                    ["--audio-url", "https://example.com/clip.mp4", "--execute"],
                    opener=opener,
                )

        self.assertEqual(1, len(requests))
        self.assertEqual("POST", requests[0].get_method())

    def test_retryable_poll_error_retries_only_get_and_writes_words(self):
        requests = []
        responses = [
            FakeResponse({"data": {"id": "pred-1"}}),
            HTTPError("https://api.example/prediction", 503, "unavailable", {}, None),
            FakeResponse(
                {
                    "data": {
                        "status": "completed",
                        "stt_result": {
                            "text": "hello",
                            "words": [{"text": "hello", "start": 0.1, "end": 0.5}],
                        },
                    }
                }
            ),
        ]

        def opener(request, **_kwargs):
            requests.append(request)
            response = responses.pop(0)
            if isinstance(response, Exception):
                raise response
            return response

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "transcript.json"
            with patch.object(Path, "cwd", return_value=root), patch.dict(
                os.environ, {"ATLASCLOUD_API_KEY": "test-key"}
            ), redirect_stdout(io.StringIO()):
                result = atlas_transcribe.run(
                    [
                        "--audio-url",
                        "https://example.com/clip.mp4",
                        "--output",
                        "transcript.json",
                        "--poll-interval",
                        "0",
                        "--execute",
                    ],
                    opener=opener,
                    sleeper=lambda _seconds: None,
                )

            saved = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(1, result["words"])
        self.assertEqual("hello", saved["words"][0]["text"])
        self.assertEqual(1, sum(request.get_method() == "POST" for request in requests))
        self.assertEqual(2, sum(request.get_method() == "GET" for request in requests))

    def test_output_must_be_new_and_inside_working_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            existing = root / "existing.json"
            existing.write_text("{}", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                atlas_transcribe.resolve_output(existing, root)
            with self.assertRaises(ValueError):
                atlas_transcribe.resolve_output(root.parent / "escape.json", root)

    def test_text_normalization_requires_language(self):
        args = atlas_transcribe.parse_args(
            [
                "--audio-url",
                "https://example.com/clip.mp4",
                "--text-normalization",
            ]
        )
        with self.assertRaisesRegex(ValueError, "requires --language"):
            atlas_transcribe.build_payload(args, preview=True)


if __name__ == "__main__":
    unittest.main()
