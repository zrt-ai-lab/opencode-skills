# 阶段5：生成模块开发文档

为每个功能模块生成详细的开发文档，放在 `.claude/docs/{模块}/` 下。

## 5.1 每个模块必须生成的文件

### README.md — 模块概览

```markdown
# {模块名}

## 概述
{模块职责，一句话}

## API 列表
| 方法 | 路径 | 说明 | 请求体 | 响应 |
|------|------|------|--------|------|
| POST | /api/v1/workspace/create | 创建工作空间 | CreateWorkspaceRequest | RestResult<Integer> |
| GET | /api/v1/workspace/{code} | 查询详情 | - | RestResult<WorkspaceDto> |

## 依赖
- 依赖模块：common（工具类、异常）
- 外部依赖：MySQL, Redis

## 详细文档
- [API 详情](api-{域}.md)
- [数据模型](data-model.md)
- [开发清单](dev-checklist.md)
```

### api-{域}.md — API 详细设计

对每个 API 端点：

```markdown
## POST /api/v1/workspace/create

### 说明
创建新工作空间

### 请求体 CreateWorkspaceRequest

| 字段 | 类型 | 必填 | 校验 | 说明 |
|------|------|------|------|------|
| name | String | 是 | @NotBlank @Size(max=64) | 工作空间名称 |
| workspaceCode | String | 是 | @NotBlank @Pattern | 编码，唯一 |
| product | String | 是 | @NotNull | 产品标识 |
| members | List<MemberRoleDto> | 是 | @NotEmpty @Valid | 成员列表 |

### 响应
RestResult<Integer> — 返回新建的工作空间 ID

### 业务逻辑
1. 校验 workspaceCode 唯一性
2. 创建工作空间记录
3. 批量添加成员
4. 返回 ID

### 错误码
| 错误码 | 说明 |
|--------|------|
| 200001 | 项目不存在 |
| 200002 | 编码已存在 |
```

### data-model.md — 数据模型

```markdown
# 数据模型

## t_workspace 工作空间表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT UNSIGNED | 主键 |
| name | VARCHAR(64) | 名称 |
| code | VARCHAR(64) | 编码，唯一 |
| ... | | |

## 实体关系
workspace 1:N workspace_member N:1 user

## 索引
- uk_code (code) — 唯一索引
- idx_name (name) — 普通索引
```

### dev-checklist.md — 开发清单

从阶段3任务清单中提取该模块的任务，加上代码规范提醒：

```markdown
# {模块} 开发清单

## 待开发
- [ ] 建表 SQL
- [ ] 实体类 Workspace.java（@Data @TableName("t_workspace")）
- [ ] Mapper 接口 WorkspaceDao.java（@Repository extends BaseMapper）
- [ ] DTO：CreateWorkspaceRequest（@Valid 校验注解）
- [ ] Service 接口 + 实现（@Transactional(rollbackFor=Exception.class)）
- [ ] Controller（@RestController @Tag @Operation）
- [ ] 单元测试

## 规范提醒
- Controller 不写 try-catch，走全局异常处理器
- Service 用双层 catch 模式（BizException + Exception）
- DTO 字段用包装类型，不设默认值
- Mapper 参数加 @Param
- 禁止 SELECT *
```

## 5.2 执行流程

```
1. 按模块优先级顺序，逐模块处理
2. 每个模块：写 README → api-*.md → data-model.md → dev-checklist.md
3. 写完一个模块 → 更新 _progress.md
4. 全部完成 → 更新 CLAUDE.md 的文档索引 → 删除 _progress.md
```

## 5.3 完成标志

- 每个功能模块都有 README + api-*.md + data-model.md + dev-checklist.md
- CLAUDE.md 的文档索引链接到所有文件
- `_progress.md` 已删除

## 5.4 最终输出

完成后汇报：

```
| 模块 | 文档 | API数 | 备注 |
|------|------|-------|------|
| .claude/CLAUDE.md | 已完成 | - | 开发指南 |
| docs/workspace/ | 已完成 | 8 | README + api + data-model + checklist |
| docs/user/ | 已完成 | 5 | README + api + data-model + checklist |
| docs/_task-list.md | 已完成 | - | 完整开发任务清单 |
```
