---
name: build-project-docs
description: 为项目构建分层式LLM友好文档体系。已有项目：扫描项目结构→架构分类→生成CLAUDE.md主索引→基础模块文档→业务模块API/数据模型/坑点文档→配置文档→git变更日志(含风险评估+回滚指南)→交叉验证。新项目：解析PRD→按脚手架规范设计架构→需求拆解为开发任务→融合代码规范生成CLAUDE.md开发指南→模块级API设计+数据模型+开发清单。当用户需要为项目创建AI编程文档、建立项目索引、梳理代码、新建项目规划、或提到llm.txt/CLAUDE.md时使用。
metadata:
  author: zhairuitao
  version: "1.0"
  language: zh-CN
compatibility: 需要 git
allowed-tools: Bash(git:*,find:*,wc:*,head:*,ls:*) Read Write Edit Glob Grep
---

# 构建项目文档体系 (build-project-docs)

为项目创建完整的分层式 LLM 友好文档。支持两种模式：已有项目梳理文档、新项目从 PRD 驱动开发。

## 核心理念

LLM上下文窗口有限，文档必须分层：
- **.claude/CLAUDE.md** = 主索引（项目地图，始终加载到上下文）
- **.claude/docs/{模块}/README.md** = 模块级文档（按需加载）
- **.claude/docs/{模块}/*.md** = 深度参考文档（API详情、数据模型、坑点）
- **.claude/docs/{模块}/CHANGELOG.md** = 模块变更历史（调试和回滚参考）

---

## 模式检测

开始前先判断当前模式：

### 文档模式（已有项目，有源代码）

项目已有代码，需要梳理生成文档。

**全新**（无 `.claude/docs/`）→ 按顺序执行文档模式全部8个阶段。

**增量**（`.claude/docs/` 已存在）→
1. **先检查 `.claude/docs/_progress.md`**——如果存在，说明上次会话中断，读取它确定：
   - **阶段状态**：哪些阶段已完成、哪个阶段进行中、哪些待执行
   - **模块进度**：阶段4/5/7中哪些模块已完成、哪些待处理
   - **直接跳到第一个未完成的阶段继续**，不重复已完成的阶段
2. 如果 `_progress.md` 不存在，阅读现有 .claude/CLAUDE.md 和所有 .claude/docs/ 文件
3. 运行阶段1获取当前状态
4. 对比：新模块→加入，文件数变化→更新，缺失→创建，过期→更新
5. 跳过已完成且准确的阶段
6. **阶段7和阶段8 特殊处理**：即使 `_progress.md` 标记为已完成，如果源码比文档更新（`find -newer` 检测），仍需重新运行

### 新项目模式（PRD驱动）

用户提到 PRD、需求文档、新项目规划、开发规范，且项目为空或新建 → 执行新项目模式5个阶段。

用户提到 PRD + 项目已有代码 → 先用文档模式梳理现有代码，再用新项目模式的阶段1-3做增量功能的需求拆解。

---

## 文档模式（8个阶段）

为已有项目梳理代码、生成分层文档。

| 阶段 | 内容 | 详细流程 |
|------|------|----------|
| 1 | 项目探查 | → [phase-1-explore.md](references/docs/phase-1-explore.md) |
| 2 | 架构分类 | → [phase-2-classify.md](references/docs/phase-2-classify.md) |
| 3 | 编写 .claude/CLAUDE.md | → [phase-3-index.md](references/docs/phase-3-index.md) |
| 4 | 基础模块文档 | → [phase-4-foundation.md](references/docs/phase-4-foundation.md) |
| 5 | 业务模块文档 | → [phase-5-business.md](references/docs/phase-5-business.md) |
| 6 | 配置层文档 | → [phase-6-config.md](references/docs/phase-6-config.md) |
| 7 | 变更日志 | → [phase-7-changelog.md](references/docs/phase-7-changelog.md) |
| 8 | 交叉验证 | → [phase-8-verify.md](references/docs/phase-8-verify.md) |

**执行前必须阅读对应阶段的 reference 文件。**

---

## 新项目模式（5个阶段）

从 PRD 出发，生成架构设计、需求拆解、开发规范、模块文档。

| 阶段 | 内容 | 详细流程 |
|------|------|----------|
| 1 | PRD 解析 | → [phase-1-prd.md](references/new-project/phase-1-prd.md) |
| 2 | 架构设计 | → [phase-2-scaffold.md](references/new-project/phase-2-scaffold.md) |
| 3 | 需求拆解 | → [phase-3-breakdown.md](references/new-project/phase-3-breakdown.md) |
| 4 | 生成 CLAUDE.md 开发指南 | → [phase-4-guide.md](references/new-project/phase-4-guide.md) |
| 5 | 模块开发文档 | → [phase-5-devdocs.md](references/new-project/phase-5-devdocs.md) |

开发规范参考：
- [Java 代码规范](references/standards/java-code.md)
- [Spring Boot 脚手架规范](references/standards/springboot-scaffold.md)

**执行前必须阅读对应阶段的 reference 文件。**

---

## 关键规则

### 上下文管理（最重要！）

处理多模块时，**禁止一次性处理所有模块**。必须：
1. 逐模块串行处理（从小到大）
2. 每完成一个模块 → 更新 `_progress.md` → 不再引用该模块源码
3. 处理 3+ 个大模块后 → 主动提示用户开新会话继续

### 进度追踪（`_progress.md`）

`_progress.md` 是**全局进度文件**，两种模式通用：
- 每完成一个阶段或一个模块 → 立即更新 `_progress.md`
- 新会话读取后可直接跳到断点继续
- 全部完成后删除

### 文档完整性

- ❌ 只写 README 不写 api 子文件就算"完成"
- ✅ 只要模块对外暴露了 API（Controller / @Tool / gRPC / Handler 等），就必须按业务域拆分 `api-{域}.md`
- ✅ 每个业务模块必须有 `data-model.md` + `pitfalls.md`（文档模式）或 `data-model.md` + `dev-checklist.md`（新项目模式）
- ✅ README 是索引，api-*.md 才是详情，README 中必须链接到所有子文件

### 文件大小

- .claude/CLAUDE.md：**150行以内**
- 模块 README.md：**200行以内**
- 超过250行必须拆分子文件

### 核心原则

详见 [principles.md](references/docs/principles.md)

---

## 开始执行

根据模式检测结果，进入对应的阶段流程。每个阶段先展示结果给用户确认，再继续下一阶段。
