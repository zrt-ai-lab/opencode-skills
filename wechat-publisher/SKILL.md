---
name: wechat-publisher
description: This skill should be used when preparing Markdown articles for a WeChat Official Account draft box, selecting wenyan-cli themes, processing article images, or troubleshooting authentication and whitelist failures.
---

# 微信公众号发布

将 Markdown 文章转换为微信公众号格式并提交到草稿箱。基于 `wenyan-cli`，支持主题、代码高亮和本地/网络图片上传。

## 触发场景

- 要求“发到公众号”“推送公众号”“提交公众号草稿”。
- 需要把 Markdown 排版为微信公众号图文。
- 需要选择文章主题、代码高亮或排查图片/API/白名单问题。

## 安全边界

- 默认只提交草稿箱，不代替公众号后台的审核和正式发布。
- 只有明确要求时才执行联网发布；先运行 `--dry-run`。
- 从当前 shell、CI Secret 或外部密钥管理器读取 `WECHAT_APP_ID`、`WECHAT_APP_SECRET`；禁止把凭证写入仓库、模板、文章或命令历史。
- 发布前运行 `scripts/validate_article.py`。发现疑似凭证、私钥或本机路径时停止并要求清理，不回显匹配值。
- 不读取宿主环境私有配置、个人配置或固定绝对路径；不自动安装全局依赖。

## 标准流程

1. 准备带 frontmatter 的 Markdown 文件，优先复制 `assets/templates/article-template.md`。
2. 在 frontmatter 中填写 `title` 和 `cover`；正文至少保留一张可访问的图片作为后备封面。
3. 使用 `python3 scripts/validate_article.py ARTICLE.md` 检查结构和敏感信息。
4. 使用 `scripts/publish.sh --dry-run ARTICLE.md` 预览命令。
5. 明确获得“提交草稿”意图后，设置凭证并执行：

   ```bash
   export WECHAT_APP_ID='从密钥管理器注入的值'
   export WECHAT_APP_SECRET='从密钥管理器注入的值'
   ./scripts/publish.sh ARTICLE.md lapis solarized-light
   ```

6. 到微信公众号后台审核草稿；需要正式发布时由操作者在后台完成。

## 模板与参考资料

- `assets/templates/article-template.md`：通用文章骨架。
- `assets/templates/technical-tutorial.md`：技术教程模板。
- `assets/templates/product-update.md`：产品/版本更新模板。
- `assets/templates/weekly-digest.md`：周报或资讯汇总模板。
- `assets/templates/cover-prompt.txt`：封面图生成提示词模板。
- `references/themes.md`：主题与代码高亮选型。
- `references/content-checklist.md`：发布前内容检查单。
- `references/troubleshooting.md`：常见错误和排查路径。

## 命令速查

```bash
./scripts/publish.sh --help
./scripts/publish.sh --dry-run path/to/article.md
./scripts/publish.sh path/to/article.md
./scripts/setup.sh
```

`publish.sh` 默认使用 `lapis` 主题和 `solarized-light` 代码高亮，也可通过参数或环境变量 `WECHAT_PUBLISH_THEME`、`WECHAT_PUBLISH_HIGHLIGHT` 覆盖。
