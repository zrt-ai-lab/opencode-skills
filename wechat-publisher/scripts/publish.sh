#!/usr/bin/env bash
# Publish a Markdown article to a WeChat Official Account draft box via wenyan-cli.

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_THEME="${WECHAT_PUBLISH_THEME:-lapis}"
DEFAULT_HIGHLIGHT="${WECHAT_PUBLISH_HIGHLIGHT:-solarized-light}"

usage() {
  cat <<'EOF'
用法:
  publish.sh [--dry-run] ARTICLE.md [THEME] [HIGHLIGHT]

默认主题:
  主题: lapis
  代码高亮: solarized-light

凭证:
  WECHAT_APP_ID 和 WECHAT_APP_SECRET 必须由当前 shell 或外部密钥管理器提供。
  本脚本不会读取仓库外的私有配置，也不会打印凭证值。
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" || $# -eq 0 ]]; then
  usage
  exit 0
fi

DRY_RUN=0
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=1
  shift
fi

if [[ $# -lt 1 || $# -gt 3 ]]; then
  usage >&2
  exit 2
fi

ARTICLE="$1"
THEME="${2:-$DEFAULT_THEME}"
HIGHLIGHT="${3:-$DEFAULT_HIGHLIGHT}"

python3 "$SCRIPT_DIR/validate_article.py" "$ARTICLE"

if [[ "$DRY_RUN" -eq 1 ]]; then
  printf '预览通过：%s\n' "$ARTICLE"
  printf '待执行: wenyan publish -f %q -t %q -h %q\n' "$ARTICLE" "$THEME" "$HIGHLIGHT"
  exit 0
fi

if [[ -z "${WECHAT_APP_ID:-}" || -z "${WECHAT_APP_SECRET:-}" ]]; then
  echo "缺少微信公众号凭证：请在当前 shell 设置 WECHAT_APP_ID 和 WECHAT_APP_SECRET。" >&2
  exit 1
fi

WENYAN_BIN="${WENYAN_BIN:-wenyan}"
if ! command -v "$WENYAN_BIN" >/dev/null 2>&1; then
  echo "未找到 wenyan-cli。请按其官方文档完成安装，再重试。" >&2
  exit 1
fi

echo "开始提交到微信公众号草稿箱：$ARTICLE"
"$WENYAN_BIN" publish -f "$ARTICLE" -t "$THEME" -h "$HIGHLIGHT"
echo "草稿提交完成，请在公众号后台审核后再正式发布。"
