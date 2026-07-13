#!/usr/bin/env python3
"""Report security-relevant pattern locations in a skill directory."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Optional, Sequence


@dataclass(frozen=True)
class Finding:
    """A finding without source text or matched values."""

    type: str
    file: str
    line: int


PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "credential",
        re.compile(
            r"(?ix)"
            r"\b(?:api[-_ ]?key|access[-_ ]?token|auth[-_ ]?token|"
            r"client[-_ ]?secret|password|passwd|secret|token)\b\s*[:=]\s*"
            r"(?:['\"][^'\"\r\n]{4,}['\"]|[^\s#]{4,})"
            r"|\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"
            r"|\bgh[pousr]_[A-Za-z0-9_]{20,}\b"
        ),
    ),
    (
        "private-key",
        re.compile(r"-----BEGIN(?: [A-Z]+)? PRIVATE KEY-----"),
    ),
    (
        "absolute-path",
        re.compile(
            r'''(?<![\w./:~}])/(?:[^/\s"'`]+/)+[^/\s"'`]*'''
            r'''|(?<![\w])(?:[A-Za-z]:\\|\\\\)[^\s"'`]+'''
        ),
    ),
    (
        "dangerous-command",
        re.compile(
            r"(?ix)"
            r"\brm\s+-[^\r\n]*r[^\r\n]*f\s+(?:/|~)"
            r"|\brm\s+-[^\r\n]*f[^\r\n]*r\s+(?:/|~)"
            r"|\b(?:sudo\s+)?(?:shutdown|reboot|halt)\b"
            r"|\b(?:crontab|launchctl|systemctl)\s+"
            r"(?:add|enable|start|load|install|edit|create|bootstrap)\b"
            r"|\b(?:chmod|chown)\s+-R\b"
            r"|\b(?:mkfs|dd)\b[^\r\n]*\bif="
            r"|\b(?:curl|wget)\b[^\r\n]*\|\s*"
            r"(?:sh|bash|zsh|python(?:3)?)\b"
            r"|\b(?:nc|ncat|netcat)\b[^\r\n]*\s-e(?:\s|$)"
            r"|/dev/tcp/"
        ),
    ),
    (
        "outbound-download",
        re.compile(
            r"(?ix)"
            r"\b(?:requests?|urllib(?:\.request)?|httpx|aiohttp)\s*\.\s*"
            r"(?:get|post|put|patch|delete|request|urlopen|urlretrieve)\s*\("
            r"|\b(?:urlopen|urlretrieve|fetch|curl|wget)\b"
            r"|\b(?:git|pip|npm|brew)\s+(?:clone|install|download)\b"
            r"|\b(?:socket|http\.client)\b"
        ),
    ),
    (
        "obfuscation",
        re.compile(
            r"(?ix)"
            r"\bbase64\s*\.\s*(?:b64|urlsafe_b64)decode\s*\("
            r"|\bbinascii\s*\.\s*unhexlify\s*\("
            r"|\bcodecs\s*\.\s*decode\s*\("
            r"|\bmarshal\s*\.\s*loads\s*\("
            r"|\b(?:eval|exec|compile|__import__)\s*\("
            r"|(?:chr\s*\(\s*\d{2,3}\s*\)\s*){3,}"
        ),
    ),
    (
        "sensitive-directory",
        re.compile(
            r'''(?ix)'''
            r'''~[/\\]\.(?:ssh|aws|kube|config|docker)'''
            r'''|(?:^|[\s"'`/(])\.(?:ssh|aws|kube|config|docker)[/\\]'''
            r'''|(?:etc[/\\](?:passwd|shadow|sudoers)|proc[/\\](?:self|\d+)'''
            r'''|var[/\\]run|private[/\\]var|library[/\\]keychains)'''
            r'''|(?:^|[\s"'`/(])\.env(?:[/\\.'"`]|$)'''
        ),
    ),
)

SKIP_PARTS = {".git", "__pycache__"}

SEVERITY_BY_TYPE = {
    "credential": "high",
    "private-key": "critical",
    "absolute-path": "medium",
    "dangerous-command": "critical",
    "outbound-download": "medium",
    "obfuscation": "critical",
    "sensitive-directory": "critical",
}


def _iter_files(root: Path) -> Iterable[Path]:
    if root.is_file():
        yield root
        return

    for path in sorted(root.rglob("*")):
        if path.is_symlink() or not path.is_file():
            continue
        if any(part in SKIP_PARTS for part in path.relative_to(root).parts):
            continue
        yield path


def _read_lines(path: Path) -> Optional[list[str]]:
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if b"\x00" in data:
        return None
    return data.decode("utf-8", errors="replace").splitlines()


def scan_path(path: Path | str) -> list[Finding]:
    """Scan a directory or file and return only type, relative path, and line."""

    candidate = Path(path).expanduser()
    if not candidate.exists() or not (candidate.is_dir() or candidate.is_file()):
        raise ValueError("target is not a readable file or directory")

    root = candidate.resolve()
    base = root if root.is_dir() else root.parent
    findings: set[Finding] = set()
    for file_path in _iter_files(root):
        lines = _read_lines(file_path)
        if lines is None:
            continue
        relative_file = file_path.relative_to(base).as_posix()
        for line_number, line in enumerate(lines, start=1):
            for finding_type, pattern in PATTERNS:
                if pattern.search(line):
                    findings.add(Finding(finding_type, relative_file, line_number))

    return sorted(findings, key=lambda item: (item.file, item.line, item.type))


def render_text(findings: Sequence[Finding]) -> str:
    """Render one finding per line without source excerpts or values."""

    return "\n".join(
        f"{item.type}\t{item.file}:{item.line}" for item in findings
    )


def render_json(findings: Sequence[Finding]) -> str:
    """Render a JSON array containing only the approved report fields."""

    return json.dumps(
        [asdict(item) for item in findings],
        ensure_ascii=True,
        separators=(",", ":"),
    )


def scan_skill(path: Path | str) -> dict:
    """Return a structured report without source excerpts or absolute paths."""
    findings = scan_path(path)
    finding_data = [
        {
            "type": item.type,
            "severity": SEVERITY_BY_TYPE.get(item.type, "medium"),
            "file": item.file,
            "line": item.line,
        }
        for item in findings
    ]
    if any(item["severity"] == "critical" for item in finding_data):
        verdict = "reject"
    elif finding_data:
        verdict = "caution"
    else:
        verdict = "approved"
    return {"verdict": verdict, "findings": finding_data}


def render_markdown(report: dict) -> str:
    """Render a review report containing only safe locations and categories."""
    lines = [f"# Skill Scan: {report['verdict'].upper()}", ""]
    findings = report.get("findings", [])
    if not findings:
        lines.append("No findings.")
        return "\n".join(lines) + "\n"
    lines.extend(["## Findings", ""])
    for finding in findings:
        lines.append(
            f"- `{finding['severity']}` `{finding['type']}` "
            f"at `{finding['file']}:{finding['line']}`"
        )
    return "\n".join(lines) + "\n"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Scan a skill directory and report finding types with locations."
    )
    parser.add_argument("path", help="skill directory or file to scan")
    parser.add_argument("--json", action="store_true", help="render JSON")
    parser.add_argument("--output", type=Path, help="write the report to a file")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        structured_report = scan_skill(args.path)
        report = (
            json.dumps(structured_report, ensure_ascii=True, indent=2)
            if args.json
            else render_markdown(structured_report)
        )
        if args.output:
            args.output.write_text(report + ("\n" if report else ""), encoding="utf-8")
        elif report:
            print(report)
    except (OSError, ValueError):
        print("error: unable to scan target", file=sys.stderr)
        return 2
    if structured_report["verdict"] == "reject":
        return 2
    return 1 if structured_report["findings"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
