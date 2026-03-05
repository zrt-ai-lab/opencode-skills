# 阶段2：架构设计

基于阶段1的 PRD 解析结果，按脚手架规范设计项目结构。

**执行前必须阅读**：[springboot-scaffold.md](../standards/springboot-scaffold.md)

## 2.1 判断项目类型

| 类型 | 判断标准 | 结构 |
|------|---------|------|
| 单模块 | 功能模块 ≤ 3 个，无需独立部署 | 单 Spring Boot 工程 |
| 多模块 | 功能模块 > 3 个，或需要共享基础库 | Maven 多模块 |
| 微服务 | 模块需独立部署、独立扩缩容 | 多个独立工程 |

## 2.2 生成项目结构

### 单模块项目

按脚手架规范的标准包结构生成：

```
project-name/
├── doc/sql/init.sql
├── src/main/java/net/qihoo/{project}/
│   ├── controller/
│   ├── service/impl/
│   ├── dao/
│   ├── domain/
│   ├── vo/
│   ├── config/
│   ├── exception/
│   ├── constants/
│   ├── utils/
│   └── {Project}Application.java
├── src/main/resources/
│   ├── application.yml
│   ├── application-dev.yml
│   ├── application-prod.yml
│   ├── logback-spring.xml
│   └── mapper/
├── bin/start.sh, stop.sh
├── pom.xml
├── README.md
└── .gitignore
```

### 多模块项目

```
project-name/
├── project-common/          # 基础层：工具类、异常、常量
├── project-dao/             # 数据层：Mapper、实体
├── project-service/         # 业务层：Service 接口 + 实现
├── project-web/             # 接入层：Controller、配置、启动类
├── doc/sql/
├── bin/
└── pom.xml                  # 父 POM
```

## 2.3 模块划分

基于阶段1的功能模块列表，确定每个功能模块放在哪一层：

```markdown
| 功能模块 | 所在层 | 包路径 |
|---------|--------|--------|
| 用户管理 | service + web | controller/user, service/user |
| 工作空间 | service + web | controller/workspace, service/workspace |
| 公共工具 | common | utils, exception, constants |
```

## 2.4 输出

生成项目结构树 + 模块划分表，展示给用户确认后进入下一阶段。
