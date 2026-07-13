# 主题与代码高亮

先使用 `wenyan theme -l` 查看当前版本实际可用的主题。常见组合如下：

| 场景 | 主题 | 代码高亮 |
|---|---|---|
| 技术教程 | `lapis` | `solarized-light` |
| 简洁通用 | `default` | `github` |
| 轻量现代 | `phycat` | `atom-one-light` |
| 深色代码 | `lapis` | `dracula` |

## 常见命令

```bash
wenyan publish -f article.md -t lapis -h solarized-light
wenyan render -f article.md -t lapis -h github
wenyan publish -f article.md -c /path/to/custom-theme.css
wenyan theme -l
```

常见代码高亮包括 `github`、`github-dark`、`dracula`、`monokai`、`solarized-light`、`solarized-dark` 和 `xcode`。具体名称以本地 CLI 帮助为准。

参考：

- [wenyan-cli](https://github.com/caol64/wenyan-cli)
- [wenyan themes](https://github.com/caol64/wenyan-core/tree/main/src/assets/themes)
