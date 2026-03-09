# 阶段5：编写业务模块文档

## 每个业务模块的文档要求

### 必须创建：README.md

`docs/{模块}/README.md` 包含：
- 模块概述和依赖
- 对外 API 索引（含路径/方法/工具名）
- 关键服务流程（仅非平凡的）
- 数据模型引用（尽量链接到基础层文档）
- 模块特定配置
- 本模块已知坑点

### 必须创建：按 API 分组拆分的子文件

**只要模块对外暴露了 API（不论形式），就必须为每个 API 分组创建独立的 api-{域}.md 文件。**

API 的形式包括但不限于：
- REST Controller（Spring MVC / Express / Gin 等）
- MCP Server 的 @Tool 方法
- gRPC Service 定义
- GraphQL Resolver
- WebSocket Handler
- CLI 命令入口

按**业务域**拆分，每个域一个文件：
- `docs/{模块}/api-{域}.md` — 该域下所有 API 的详细文档（路径/方法签名、参数、返回值、调用示例）
- `docs/{模块}/data-model.md` — 模块核心数据模型（DTO/VO/PO/Tool参数 及其关系）
- `docs/{模块}/pitfalls.md` — 已知坑点和注意事项

README.md 的作用是**索引**，api-*.md 才是**详情**。README 中必须有「详细文档」章节链接到所有 api-*.md。

### 判断标准

写完 README 后，**必须执行以下检查**：
```
该模块对外暴露了 API 吗？（Controller / @Tool / gRPC Service / Handler / ...）
→ 没有：只写 README（如纯工具库模块）
→ 有：按业务域拆分 api-{域}.md + data-model.md + pitfalls.md
```

---

## 单模块执行流程

```
1. 读取当前模块的所有源文件（Controller/Tool/Service/DTO 等）
2. 写 README.md（模块概览 + API 索引表）
3. 判断：该模块对外暴露了 API 吗？
   → 没有（纯工具库/纯模型模块）：跳到步骤 6
   → 有：继续步骤 4-5
4. 按业务域拆分，每个域写一个 api-{域}.md + 写 data-model.md + 写 pitfalls.md
5. 验证所有文件已写入（ls 检查）
6. 更新 _progress.md：将该模块从 ⏳ 改为 ✅，补充文件清单
7. 进入下一个模块，回到步骤1
8. 处理 3+ 个大模块后，主动提示用户：
   「建议开新会话继续，运行 /build-project-docs 会自动读取 _progress.md 进入增量模式」
```

### 进度文件 `.claude/docs/_progress.md`

阶段5开始时，将阶段5标记为 `🔄 进行中`，并在已有进度基础上追加模块级进度：

```markdown
## 阶段5 业务模块
- oss: ✅ README + api-bucket + api-cluster + api-region + api-user + api-ec + api-schedule + data-model + pitfalls (7域/124个API)
- mcp-obs: ✅ README + api-tools + data-model + pitfalls (1域/15个Tool)
- hdfs-server: ⏳ 待处理
- hdfs-service: ⏳ 待处理
```

每完成一个模块，将该模块从 `⏳` 改为 `✅` 并补充文件清单。全部完成后将阶段5标记为 `✅ 已完成`。

### 执行顺序（从小到大）

1. 先统计所有业务模块的 API 数量（端点数 / Tool 数 / 方法数）
2. 按数量从少到多排序
3. 逐个处理，每完成一个模块必须写入 _progress.md
4. 处理 3+ 个大模块后，主动提示用户开新会话继续（_progress.md 保证进度不丢）

### 禁止事项

- ❌ 同时读取多个模块的源码
- ❌ 跳过写 _progress.md 直接处理下一个模块
- ❌ 处理大量模块后不提示用户（应建议开新会话继续）
- ❌ **只写 README 不写 api-*.md 子文件就算"完成"**
- ❌ 把所有 API 详情全塞进 README 里

### 完成标志

阶段5完成的判定标准：
- 每个对外暴露 API 的模块都有对应的 api-*.md 文件
- 每个业务模块都有 data-model.md + pitfalls.md
- 每个 README.md 都有「详细文档」章节链接到所有子文件
- `_progress.md` 中所有业务模块标记为 ✅，阶段5标记为 `✅ 已完成`

> 注意：`_progress.md` 在阶段8验证全部通过后才删除，阶段5完成时**不要删**。
