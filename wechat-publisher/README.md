# wechat-publisher

将 Markdown 文章提交到微信公众号草稿箱的可分享 Skill。

## 特性

- 使用 `wenyan-cli` 转换 Markdown、上传图片并提交草稿。
- 支持主题和代码高亮参数。
- 提供文章、教程、产品更新和周报模板。
- 发布前检查 frontmatter、疑似凭证、私钥和本机绝对路径。
- 凭证只从当前 shell、CI Secret 或外部密钥管理器注入。

## 安装依赖

按 `wenyan-cli` 官方文档安装并验证：

```bash
npm install -g @wenyan-md/cli
wenyan --help
```

脚本不会自动执行全局安装，避免在未确认时改变机器环境。

## 使用

```bash
# 先校验和预览，不访问微信 API
python3 scripts/validate_article.py assets/templates/article-template.md
./scripts/publish.sh --dry-run assets/templates/article-template.md

# 明确准备提交草稿后再注入凭证并执行
export WECHAT_APP_ID='从密钥管理器注入的值'
export WECHAT_APP_SECRET='从密钥管理器注入的值'
./scripts/publish.sh path/to/article.md lapis solarized-light
```

`wenyan publish` 的结果是微信公众号草稿。正式发布仍需在公众号后台审核操作。

## 文件结构

```text
wechat-publisher/
├── SKILL.md
├── README.md
├── scripts/
│   ├── publish.sh
│   ├── setup.sh
│   └── validate_article.py
├── references/
└── assets/templates/
```

## 许可

`wenyan-cli` 的许可与使用限制以其官方项目为准。
