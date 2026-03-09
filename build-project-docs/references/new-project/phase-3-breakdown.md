# 阶段3：需求拆解

基于阶段1的 PRD 解析 + 阶段2的架构设计，将需求拆解为可执行的开发任务。

## 3.1 拆解维度

每个功能模块拆解为：

### 数据层任务
- 建表 SQL（doc/sql/）
- 实体类（domain/）
- Mapper 接口 + XML（dao/ + mapper/）

### 业务层任务
- Service 接口定义
- Service 实现（含业务逻辑、事务、异常处理）
- DTO / Request / Response 定义（vo/）

### 接入层任务
- Controller（路由、参数校验、Swagger 注解）
- 权限配置（如需）

### 基础设施任务
- 配置类（config/）
- 异常体系（exception/ + ErrorCode）
- 全局处理器（GlobalExceptionHandler）
- 工具类（utils/）

## 3.2 输出格式

```markdown
# 开发任务清单

## 基础设施（所有功能的前置依赖）

| # | 任务 | 文件 | 优先级 | 预估 |
|---|------|------|--------|------|
| 0.1 | 项目脚手架搭建 | pom.xml, Application, 配置文件 | P0 | - |
| 0.2 | 统一响应 RestResult | vo/RestResult.java | P0 | - |
| 0.3 | 异常体系 | exception/BizException + ErrorCode | P0 | - |
| 0.4 | 全局异常处理器 | exception/GlobalExceptionHandler | P0 | - |
| 0.5 | Swagger 配置 | config/OpenApiConfig | P0 | - |
| 0.6 | MyBatis-Plus 配置 | config/MybatisConfig | P0 | - |
| 0.7 | 数据库初始化脚本 | doc/sql/init.sql | P0 | - |

## 模块1：{模块名}

| # | 任务 | 文件 | 依赖 | 优先级 |
|---|------|------|------|--------|
| 1.1 | 建表 SQL | doc/sql/V1.0.0__init.sql | 0.7 | P0 |
| 1.2 | 实体类 | domain/Workspace.java | 1.1 | P0 |
| 1.3 | Mapper | dao/WorkspaceDao.java + mapper/WorkspaceMapper.xml | 1.2 | P0 |
| 1.4 | DTO 定义 | vo/CreateWorkspaceRequest.java 等 | - | P0 |
| 1.5 | Service 接口 | service/WorkspaceService.java | 1.3, 1.4 | P0 |
| 1.6 | Service 实现 | service/impl/WorkspaceServiceImpl.java | 1.5 | P0 |
| 1.7 | Controller | controller/WorkspaceController.java | 1.6 | P0 |
| 1.8 | 单元测试 | test/WorkspaceServiceTest.java | 1.6 | P1 |

## 模块2：...
```

## 3.3 规则

- **基础设施任务排最前**（所有模块依赖）
- 模块内按 数据层 → 业务层 → 接入层 顺序
- 标注任务间依赖关系
- P0 任务构成 MVP，P1/P2 后续迭代
- 任务粒度：一个任务 = 一个可独立提交的工作单元

**输出后等用户确认**，确认后进入阶段4。
