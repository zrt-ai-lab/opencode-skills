# 阶段4：生成 CLAUDE.md 开发指南

基于前3个阶段的结果，生成 `.claude/CLAUDE.md` 作为 AI 编程的项目级开发指南。

**执行前必须阅读**：
- [java-code.md](../standards/java-code.md) — Java 代码规范
- [springboot-scaffold.md](../standards/springboot-scaffold.md) — 脚手架规范

## 4.1 CLAUDE.md 结构

```markdown
# {项目名}

## 概述
{一句话描述，来自阶段1}

## 技术栈
- Java {版本} / Spring Boot {版本}
- MyBatis-Plus / MySQL
- Redis（如有）
- OpenTelemetry 可观测性

## 构建与运行
{来自脚手架规范的构建命令和启动方式}

## 项目结构
{来自阶段2的项目结构树}

## 包结构与依赖方向
{来自脚手架规范第三章}
controller -> service -> dao -> domain

## 开发规范摘要

### 命名规范
- 包名：全小写，com.example.{project}.{module}
- 类名：UpperCamelCase，DTO/VO/Request/Response 后缀
- 方法名：lowerCamelCase，get/list/create/update/delete 前缀
- 常量：UPPER_SNAKE_CASE，禁止魔法值
{从 java-code.md 提取关键条目，不超过 20 行}

### Controller 规范
- URL 全小写，单词用 `-` 分隔
- @RestController + @RequestMapping("/api/v1/{resource}")
- @RequestBody 搭配 @Valid
- 返回 RestResult<T>，禁止返回 null
- 每个方法必须有 @Operation(summary)

### Service 规范
- @Transactional(rollbackFor = Exception.class)
- 双层 catch：BizException 原样抛 + Exception 包装
- 方法体不超过 80 行

### 数据库规范
- 表名 t_ 前缀，字段小写下划线
- 必须有 id/create_time/update_time/is_deleted
- 禁止 SELECT *，禁止无 WHERE 的 UPDATE/DELETE

### 异常处理
- BizException + ErrorCode 枚举
- Controller 不写 try-catch，走 GlobalExceptionHandler
- 错误码按模块分段：通用 1xxxxx，模块A 2xxxxx ...

### 日志规范
- @Slf4j + 占位符，禁止字符串拼接
- error 必须带异常对象：log.error("msg", e)
- 外部调用前后各一条日志（含耗时）

## 模块索引
{来自阶段1的功能模块表，链接到 .claude/docs/ 下的详细文档}

## 开发任务
{来自阶段3的任务清单摘要，链接到完整任务文档}

## 文档索引
{链接到所有 .claude/docs/ 文件}
```

## 4.2 关键规则

- **150 行以内**（始终加载到上下文）
- 规范摘要只放最关键的条目，详细规范链接到 standards/ 文件
- 项目特定信息（模块、API、数据模型）链接到 docs/ 子文件
- 必须包含构建命令、包结构、依赖方向（AI 写代码最常参考）

## 4.3 同时生成 .claude/docs/_task-list.md

将阶段3的完整任务清单写入 `.claude/docs/_task-list.md`，作为开发进度追踪文件。

CLAUDE.md 中链接到此文件：`[开发任务清单](docs/_task-list.md)`

## 4.4 写入进度

完成后创建 `.claude/docs/_progress.md`：

```markdown
# 执行进度

## 阶段状态
- 阶段1 PRD解析: ✅ 已完成
- 阶段2 架构设计: ✅ 已完成
- 阶段3 需求拆解: ✅ 已完成
- 阶段4 开发指南: ✅ 已完成
- 阶段5 模块文档: ⏳ 待执行
```
