# 故障排查

## `wenyan: command not found`

按 `wenyan-cli` 官方文档完成安装，然后执行：

```bash
wenyan --help
```

`publish.sh` 不会自动安装全局依赖。

## 缺少 `title` 或封面

确保 Markdown 文件最顶部存在：

```markdown
---
title: 文章标题
cover: ./assets/cover.jpg
---
```

没有 `cover` 时，至少提供一张正文图片，并先通过本 Skill 的校验器。

## `ip not in whitelist` 或错误码 45166

登录微信公众号后台，在开发设置中将实际运行机器的公网 IP 加入白名单。不要使用 `0.0.0.0/0` 作为长期配置。

## `WECHAT_APP_ID is required` 或凭证无效

确认当前 shell 或 CI Secret 已注入以下两个变量，且没有额外空格：

```bash
export WECHAT_APP_ID='安全注入的 AppID'
export WECHAT_APP_SECRET='安全注入的 AppSecret'
```

执行 `scripts/setup.sh` 只会检查变量是否存在，不会显示值、读取私有配置或写入文件。

## 图片上传失败

按以下顺序检查：

1. 使用相对路径，确认文件确实存在。
2. 确认格式和大小符合当前微信限制。
3. 对网络图片执行独立连通性检查，必要时改成本地图片。
4. 使用 `wenyan render` 先验证排版，再重试草稿提交。

## 文章内容触发安全校验

`validate_article.py` 会阻断疑似凭证、私钥和本机路径，并且只报告问题类型，不回显匹配值。清理文章后重新运行校验；不要通过删除校验器来绕过检查。

更多参数以以下命令为准：

```bash
wenyan publish --help
wenyan render --help
```
