# 阶段8：交叉引用验证与自检

全部文档和变更日志写完后，进行最终验证。

## 文档完整性

1. .claude/CLAUDE.md 中每个模块的文件数和描述是否正确
2. 每个 .claude/docs/ 文件是否在 .claude/CLAUDE.md 文档索引中有链接
3. 基础层文档被业务模块文档引用（而非重复）
4. 无孤儿信息 — 每个事实只存在于一个地方
5. 坑点放在最具体的适用位置

## CHANGELOG 质量

6. 每个已文档化的模块（含基础模块）都有 CHANGELOG
7. 每个 CHANGELOG 条目都有完整的文件列表（无占位符）
8. HIGH 风险条目都有回滚指南

## 验证命令

```bash
# 检查 CHANGELOG 覆盖度
ls .claude/docs/*/CHANGELOG.md 2>/dev/null

# 检查占位符
grep -rn "需通过\|查看详细\|TBD" .claude/docs/*/CHANGELOG.md

# 检查每个 README 是否链接了所有子文件
for module in $(ls .claude/docs/); do
  for f in $(ls .claude/docs/$module/*.md 2>/dev/null | xargs -I{} basename {}); do
    if [ "$f" != "README.md" ] && [ "$f" != "CHANGELOG.md" ]; then
      grep -q "$f" .claude/docs/$module/README.md || echo "MISSING: $module/README.md -> $f"
    fi
  done
done

# 检查 .claude/CLAUDE.md 是否链接了所有模块
for module in $(ls .claude/docs/); do
  grep -q "docs/$module/" .claude/CLAUDE.md || echo "NOT LINKED: $module"
done

# 检查有 API 的模块是否都有 api-*.md 子文件
for module in $(ls .claude/docs/); do
  dir=".claude/docs/$module"
  # 跳过没有 README 的目录
  [ ! -f "$dir/README.md" ] && continue
  # 检查 README 中是否提到了 API（Controller/@Tool/gRPC/Handler 等）
  if grep -qiE "Controller|@Tool|gRPC|Handler|Resolver|端点|endpoint|API" "$dir/README.md"; then
    # 有 API 的模块必须有 api-*.md
    api_count=$(ls "$dir"/api-*.md 2>/dev/null | wc -l)
    if [ "$api_count" -eq 0 ]; then
      echo "MISSING API DOCS: $module has APIs but no api-*.md files"
    fi
    # 有 API 的模块必须有 data-model.md 和 pitfalls.md
    [ ! -f "$dir/data-model.md" ] && echo "MISSING: $module/data-model.md"
    [ ! -f "$dir/pitfalls.md" ] && echo "MISSING: $module/pitfalls.md"
  fi
done
```

如果验证发现问题，**必须修复后再报告**。常见修复：
- `MISSING API DOCS` → 回到阶段5为该模块补写 api-*.md
- `MISSING: data-model.md / pitfalls.md` → 补写对应文件
- `NOT LINKED` → 在 .claude/CLAUDE.md 中补充链接

## 完成收尾

全部验证通过后：
1. 在 `_progress.md` 中将阶段8标记为 `✅ 已完成`
2. **删除 `_progress.md`**（临时文件，全部完成后不再需要）
3. 输出最终进度报告给用户
