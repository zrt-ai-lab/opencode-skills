#!/usr/bin/env bash
# Check credentials in the current shell without reading or writing secret files.

missing=()
[[ -n "${WECHAT_APP_ID:-}" ]] || missing+=("WECHAT_APP_ID")
[[ -n "${WECHAT_APP_SECRET:-}" ]] || missing+=("WECHAT_APP_SECRET")

if [[ ${#missing[@]} -gt 0 ]]; then
  echo "缺少环境变量: ${missing[*]}" >&2
  echo "请通过 shell、密钥管理器或 CI Secret 注入后再执行发布。" >&2
  if [[ "${BASH_SOURCE[0]}" != "$0" ]]; then
    return 1
  fi
  exit 1
fi

echo "微信公众号环境变量已配置（凭证值不会显示）。"
