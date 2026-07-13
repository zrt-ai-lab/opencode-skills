#!/usr/bin/env python3
"""Validate a Markdown article before handing it to wenyan-cli."""

from __future__ import annotations

import re
import sys
from pathlib import Path


FRONTMATTER_BOUNDARY = re.compile(r"\A---\s*\n(?P<body>.*?)\n---\s*(?:\n|\Z)", re.DOTALL)
KEY_VALUE = re.compile(r"^(?P<key>[A-Za-z][A-Za-z0-9_-]*)\s*:\s*(?P<value>.*)$")
MARKDOWN_IMAGE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
PRIVATE_PATH = re.compile(
    r"(?:/(?:Users|home|private/var|var/folders)/[^\s`<>\"']+)|"
    r"(?:[A-Za-z]:\\Users\\[^\s`<>\"']+)",
)
SENSITIVE_VALUE = re.compile(
    r"(?ix)(?:"
    r"(?:WECHAT_APP_ID|WECHAT_APP_SECRET|API_KEY|API_TOKEN|ACCESS_TOKEN|CLIENT_SECRET)"
    r"\s*[=:]\s*[^\s`<>\"']+|"
    r"(?:sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]+)|"
    r"-----BEGIN [A-Z ]+ PRIVATE KEY-----"
    r")",
)


def _parse_frontmatter(text: str) -> tuple[dict[str, str], list[str]]:
    match = FRONTMATTER_BOUNDARY.match(text)
    if not match:
        return {}, ["缺少位于文件顶部的 YAML frontmatter"]

    fields: dict[str, str] = {}
    for line in match.group("body").splitlines():
        parsed = KEY_VALUE.match(line.strip())
        if parsed:
            fields[parsed.group("key").lower()] = parsed.group("value").strip().strip("\"'")
    return fields, []


def validate_article(article_path: str | Path) -> list[str]:
    """Return safe, non-sensitive validation errors for an article."""
    path = Path(article_path)
    if not path.is_file():
        return ["文章文件不存在"]

    text = path.read_text(encoding="utf-8")
    fields, errors = _parse_frontmatter(text)

    if not fields.get("title"):
        errors.append("frontmatter 缺少非空 title")
    if not fields.get("cover") and not MARKDOWN_IMAGE.search(text):
        errors.append("需要 cover 字段或至少一张正文图片")
    if SENSITIVE_VALUE.search(text):
        errors.append("发现疑似凭证或私钥，请清理后再发布")
    if PRIVATE_PATH.search(text):
        errors.append("发现疑似本机路径，请改为相对路径或通用占位符")

    return errors


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 1 or args[0] in {"-h", "--help"}:
        print(f"用法: {Path(sys.argv[0]).name} ARTICLE.md")
        return 0 if args and args[0] in {"-h", "--help"} else 2

    errors = validate_article(args[0])
    if errors:
        print("文章校验失败：")
        for error in errors:
            print(f"- {error}")
        return 1

    print("文章校验通过：未发现结构或敏感信息问题")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
