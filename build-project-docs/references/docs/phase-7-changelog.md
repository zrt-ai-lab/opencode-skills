# 阶段7：生成变更日志

为每个已文档化的模块（包括基础模块和业务模块）生成 `docs/{模块}/CHANGELOG.md`。静态文档描述"是什么"，CHANGELOG 描述"最近改了什么"。

> 基础模块（如 common、dao）的变更往往影响所有业务模块，CHANGELOG 对排查跨模块 bug 尤为重要。

## 7.1 识别需要生成 CHANGELOG 的模块

```bash
# 列出有 docs 但没有 CHANGELOG 的模块
for dir in .claude/docs/*/; do
  module=$(basename "$dir")
  [ ! -f "$dir/CHANGELOG.md" ] && echo "$module"
done

# 列出有 CHANGELOG 但可能有新提交的模块
for f in .claude/docs/*/CHANGELOG.md; do
  module=$(basename $(dirname "$f"))
  echo "$module"
done
```

## 7.2 提取 Git 历史

```bash
# 获取最近10个涉及该模块的提交
git log --oneline -10 -- {模块目录}/

# 对每个提交，获取变更文件和统计
git show --stat {commit-hash} -- {模块目录}/

# 获取实际 diff 来理解改了什么
git show {commit-hash} -- {模块目录}/

# 检查同一提交是否也修改了公共模块（跨模块影响）
git show --stat {commit-hash} -- {公共模块目录}/
```

## 7.3 去重检查

如果 CHANGELOG.md 已存在，先提取已记录的 commit hash，跳过已有条目：
```bash
grep -oP '(?<=\*\*提交\*\*: |Commit\*\*: )[a-f0-9, ]+' .claude/docs/{模块}/CHANGELOG.md
```

## 7.4 分析每个提交

对每个提交确定：

1. **类型**: feat / fix / refactor / perf / chore
   - 关键词："修复"→fix，"增加/新增/支持"→feat，"优化"→perf，"调整"→refactor

2. **变更文件**：列出每个文件的 +/- 行数
   - **必须包含实际文件名和变更行数**（从 `git show --stat` 获取）
   - **禁止使用占位符**如"（需通过 git show 查看）"

3. **影响分析**：
   - 哪些 API 端点受影响？
   - 是否有新参数、字段或方法？
   - 跨模块变更（公共模块在同一提交中被修改）？
   - 数据库变更（新列、修改查询）？
   - 配置变更？

4. **风险评估**：
   - `LOW`：仅本模块、装饰性/日志变更
   - `MEDIUM`：API参数变更、业务逻辑变更
   - `HIGH`：跨模块变更、数据模型变更、核心流程变更

## 7.5 条目格式

```markdown
## [{日期}] {提交消息}

**类型**: {feat|fix|refactor|perf|chore}
**提交**: {短hash}
**风险**: {LOW|MEDIUM|HIGH}

### 变更文件
| 文件 | 变更 | 说明 |
|------|------|------|
| {类名.java} | +5/-2 | {改了什么以及为什么} |

### 影响范围
- **API**: {受影响的端点、新参数}
- **跨模块**: {公共模块是否也变更了}
- **数据模型**: {PO/Mapper 是否变更}
- **配置**: {配置是否变更}

### 回滚指南（仅 HIGH 风险）
- 回滚: `git revert {hash}`
- 检查文件: {列表}
- 副作用: {什么可能被影响}
```

## 7.6 写入规则

- 新条目追加到顶部（最新在最上面）
- 如果文件不存在，创建时加头部：

```markdown
# Changelog - {模块名}

> 模块变更历史。最新变更在最上方。
> 排查问题时优先阅读本文件。

---
```

## 7.7 重要规则

- **具体描述文件变更** — "修改了Controller" 没用，"BucketResourceController.changeBasePro() 新增 replicationPipeline 参数" 有用
- **每个提交必须运行 git show --stat** — 禁止文件表为空或使用占位符
- **总是标注跨模块影响** — 如果公共模块在同一提交中被修改，这是关键信息
- **HIGH 风险必须包含回滚指南**
- **合并相关提交** — 如果多个提交明显是同一功能，合并为一条记录
- **写入前去重** — 检查已有 CHANGELOG 的 hash 避免重复条目

## 7.8 进度追踪

阶段7开始时将其标记为 `🔄 进行中`，并在 `_progress.md` 中追加：

```markdown
## 阶段7 变更日志
- common: ✅ CHANGELOG (3条)
- dao: ✅ CHANGELOG (2条)
- oss-server: ⏳ 待处理
```

每写完一个模块的 CHANGELOG，将该模块从 `⏳` 改为 `✅`。全部完成后将阶段7标记为 `✅ 已完成`。
