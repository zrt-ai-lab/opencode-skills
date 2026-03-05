---
领域: Java/Spring Boot
创建日期: 2026-03-05
状态: 已验证
---

# Spring Boot 项目脚手架规范

> 新建 Spring Boot 项目时的标准模板,包含目录结构、打包配置、文档要求、中间件集成和可观测性接入。
> 搭配 java-code.md一起使用。

---

## 一、项目整体目录结构

项目根目录下的标准文件和目录:

```
project-name/
├── doc/                                # 项目文档
│   ├── sql/                            # 数据库脚本
│   │   ├── init.sql                    # 建库建表初始化脚本(全量)
│   │   ├── V1.0.0__init.sql           # 版本化增量脚本
│   │   ├── V1.1.0__add_member.sql
│   │   ├── data/                       # 初始化数据
│   │   │   ├── init_role.sql
│   │   │   └── init_config.sql
│   │   └── rollback/                   # 回滚脚本
│   │       └── V1.1.0__rollback.sql
│   ├── api/                            # 接口文档(导出的 OpenAPI JSON 等)
│   └── design/                         # 设计文档(架构图、流程图)
├── src/
│   ├── main/
│   │   ├── java/                       # Java 源码
│   │   ├── resources/                  # 配置文件、Mapper XML
│   │   └── assembly/                   # 打包描述文件
│   └── test/                           # 单元测试
├── bin/                                # 运维脚本
│   ├── start.sh
│   ├── stop.sh
│   └── health-check.sh
├── pom.xml
├── README.md                           # 项目说明(必须)
├── CHANGELOG.md                        # 变更日志(建议)
├── .gitignore
└── Dockerfile                          # 容器化构建(如需)
```

---

## 二、必要文件规范

### 2.1 README.md(必须)

每个项目根目录**必须**有 README.md,至少包含以下章节:

```markdown
# 项目名称

> 一句话描述项目用途

## 模块说明

简要说明项目包含的模块及职责。

## 技术栈

- Java 8 / 11 / 17
- Spring Boot 2.x / 3.x
- MyBatis-Plus
- MySQL 5.7+ / 8.0
- Redis(如有)

## 环境要求

| 依赖 | 版本 |
|------|------|
| JDK | 1.8+ |
| Maven | 3.6+ |
| MySQL | 5.7+ |

## 快速启动

### 本地开发

1. 导入 SQL:doc/sql/init.sql
2. 修改配置:src/main/resources/application-dev.yml
3. 启动:mvn spring-boot:run -Pdev
4. Swagger:http://localhost:8080/swagger-ui.html

### 生产部署

1. 打包:mvn clean package -Pprod
2. 解压分发包
3. 配置 config/application-prod.yml
4. 启动:bin/start.sh

## 项目结构

(简要说明包结构)

## 接口文档

Swagger:http://{host}:{port}/swagger-ui.html

## 联系人

- 负责人:xxx
```

### 2.2 SQL 文档规范(doc/sql/)

**目录结构**:

```
doc/sql/
├── init.sql                           # 完整建库建表(从零开始,新人直接执行)
├── V1.0.0__init.sql                   # 版本化:初始版本
├── V1.1.0__add_workspace_member.sql   # 版本化:新增表
├── V1.2.0__alter_workspace.sql        # 版本化:修改字段
├── data/                              # 初始化数据
│   ├── init_role.sql
│   └── init_config.sql
└── rollback/                          # 回滚脚本
    ├── V1.1.0__rollback.sql
    └── V1.2.0__rollback.sql
```

**命名规范**:

| 类型 | 命名格式 | 示例 |
|------|----------|------|
| 初始化全量 | init.sql | init.sql |
| 版本增量 | V{版本号}__{描述}.sql | V1.2.0__add_index.sql |
| 回滚脚本 | V{版本号}__rollback.sql | V1.2.0__rollback.sql |
| 数据初始化 | init_{描述}.sql | init_role.sql |

**SQL 脚本内容规范**:

```sql
-- ============================================
-- 版本: V1.1.0
-- 描述: 新增工作空间成员表
-- 作者: xubo
-- 日期: 2024-10-15
-- ============================================

CREATE TABLE IF NOT EXISTS `t_workspace_member` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
    `workspace_id` BIGINT UNSIGNED NOT NULL COMMENT '工作空间ID',
    `user_name` VARCHAR(64) NOT NULL COMMENT '用户名',
    `role_id` INT NOT NULL COMMENT '角色ID',
    `create_time` BIGINT NOT NULL COMMENT '创建时间(ms)',
    PRIMARY KEY (`id`),
    KEY `idx_workspace_id` (`workspace_id`),
    UNIQUE KEY `uk_workspace_user` (`workspace_id`, `user_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工作空间成员表';
```

**规则**:
- 每个 SQL 文件头部必须有版本、描述、作者、日期注释
- 建表用 CREATE TABLE IF NOT EXISTS
- 新增字段用 ALTER TABLE ... ADD COLUMN ... AFTER xxx,指定位置
- 每个增量脚本必须有对应的回滚脚本
- init.sql 是当前最新全量,新人拿到直接能跑
- 每次发版同步更新 init.sql

### 2.3 CHANGELOG.md(建议)

```markdown
# 变更日志

## [1.2.0] - 2024-12-01
### 新增
- 工作空间成员角色管理接口
### 修改
- 优化查询性能,添加联合索引
### 修复
- 修复并发创建时重复编码问题

## [1.1.0] - 2024-11-01
### 新增
- 工作空间收藏功能
```

### 2.4 .gitignore(必须)

```gitignore
# 编译
target/
build/
*.class

# IDE
.idea/
*.iml
.vscode/
.settings/
.project
.classpath

# 日志
logs/
*.log

# 系统
.DS_Store
Thumbs.db

# 敏感配置
**/application-prod.yml
**/application-secret.yml

# 打包产物
*.jar
*.war
*.tar.gz
!agent/*.jar
```

### 2.5 Dockerfile(容器化项目必须)

**示例配置（核心逻辑）**：

```dockerfile
FROM openjdk:8-jre-slim
LABEL maintainer="dev@example.com"

WORKDIR /app

COPY agent/opentelemetry-javaagent.jar /app/agent/
COPY lib/*.jar /app/app.jar
COPY config/ /app/config/

ENV JAVA_OPTS="-Xms512m -Xmx1024m"

EXPOSE 8080

ENTRYPOINT ["sh", "-c", "java ${JAVA_OPTS} -javaagent:/app/agent/opentelemetry-javaagent.jar -jar /app/app.jar --spring.profiles.active=prod"]
```

> **注意**：实际 Dockerfile 还需根据项目需求添加用户权限、健康检查等配置。

---

## 三、Java 包结构

### 3.1 标准布局

```
net.qihoo.{project}
├── controller/                 # REST Controller
├── service/                    # 业务接口
│   └── impl/                   # 业务实现
├── dao/                        # MyBatis Mapper 接口
├── domain/                     # 数据库实体
├── vo/                         # DTO / Request / Response
├── config/                     # 配置类
├── exception/                  # 异常 + 全局处理器
├── constants/                  # 常量 + 错误码枚举
├── utils/                      # 工具类
├── filter/                     # Filter / 拦截器
├── aspect/                     # AOP 切面
└── {ProjectName}Application.java
```

### 3.2 各包职责

| 包 | 职责 | 允许依赖 |
|----|------|----------|
| controller | 接收请求、参数校验、调用 Service | service, vo |
| service | 业务逻辑、事务控制 | dao, domain, vo, exception, constants |
| dao | 数据库访问 | domain |
| domain | 实体,只做字段映射 | 无 |
| vo | 传输对象 | 无 |
| config | Spring 配置 | 按需 |
| exception | 异常 + ControllerAdvice | constants |
| constants | 常量 + 错误码 | 无 |
| utils | 无状态工具 | 无 |

### 3.3 依赖方向

```
controller -> service -> dao -> domain
     |          |
     vo       constants
     |
  exception
```

- 禁止反向依赖、禁止 controller 调 dao、utils 不依赖业务代码

---

## 四、启动类

**示例代码（核心逻辑）**：

```java
@SpringBootApplication
@ServletComponentScan
@EnableScheduling
@ComponentScan(basePackages = {
    "net.qihoo.project.module.*"
})
@Slf4j
public class ProjectApplication {
    public static void main(String[] args) {
        try {
            SpringApplication.run(ProjectApplication.class, args);
        } catch (Exception e) {
            log.error("启动失败", e);
        }
    }
}
```

**规范要求**:
- 放在模块根包下
- @ComponentScan 只扫描必要包
- 启动异常必须 catch 打日志

---

## 五、Maven 打包

### 5.1 开发环境(fat jar)

**示例配置（核心配置项）**：

```xml
<profile>
    <id>dev</id>
    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
                <configuration>
                    <mainClass>net.qihoo.project.ProjectApplication</mainClass>
                    <includeSystemScope>true</includeSystemScope>
                </configuration>
                <executions>
                    <execution><goals><goal>repackage</goal></goals></execution>
                </executions>
            </plugin>
        </plugins>
    </build>
</profile>
```

### 5.2 生产环境(assembly 外置配置)

**示例配置（核心配置项）**：

```xml
<profile>
    <id>prod</id>
    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-jar-plugin</artifactId>
                <configuration>
                    <excludes>
                        <exclude>**/*.properties</exclude>
                        <exclude>**/*.yml</exclude>
                    </excludes>
                    <archive>
                        <manifest>
                            <addClasspath>true</addClasspath>
                            <mainClass>net.qihoo.project.ProjectApplication</mainClass>
                        </manifest>
                        <manifestEntries>
                            <Class-Path>../config/</Class-Path>
                        </manifestEntries>
                    </archive>
                </configuration>
            </plugin>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-assembly-plugin</artifactId>
                <version>3.7.1</version>
                <configuration>
                    <tarLongFileMode>posix</tarLongFileMode>
                    <appendAssemblyId>false</appendAssemblyId>
                    <descriptors>
                        <descriptor>src/main/assembly/assembly.xml</descriptor>
                    </descriptors>
                </configuration>
                <executions>
                    <execution>
                        <id>make-assembly</id>
                        <phase>package</phase>
                        <goals><goal>single</goal></goals>
                    </execution>
                </executions>
            </plugin>
        </plugins>
    </build>
</profile>
```

> **注意**：以上为核心配置项,实际使用时需根据项目需求补充完整的 pom.xml 配置。

### 5.3 打包产物

```
dist/
├── bin/
│   ├── start.sh
│   └── stop.sh
├── config/
│   ├── application.yml
│   └── application-prod.yml
├── lib/
│   └── project.jar
├── agent/
│   └── opentelemetry-javaagent.jar
└── logs/
```

---

## 六、配置管理

### 6.1 文件组织

```
src/main/resources/
├── application.yml             # 公共
├── application-dev.yml         # 开发
├── application-test.yml        # 测试
├── application-prod.yml        # 生产
├── logback-spring.xml          # 日志
└── mapper/                     # MyBatis XML
    ├── WorkspaceMapper.xml
    └── WorkspaceMemberMapper.xml
```

### 6.2 规则

- 敏感信息不入仓库,通过环境变量或配置中心注入
- 用 @ConfigurationProperties 绑定,不散落 @Value
- 超时、重试等运行参数必须可配置

**示例代码（核心逻辑）**：

```java
@Configuration
@ConfigurationProperties(prefix = "workspace")
@Data
public class WorkspaceProperties {
    private String produceList;
    private Boolean dockingPermissions = true;
    private Integer defaultPageSize = 20;
}
```

---

## 七、MyBatis-Plus 集成

**示例代码（核心配置）**：

```java
@Configuration
@MapperScan(
    basePackages = {"net.qihoo.project.dao"},
    sqlSessionFactoryRef = "sqlSessionFactory"
)
public class MybatisConfig {

    @Bean
    @ConfigurationProperties(prefix = "spring.datasource")
    public DataSource dataSource() {
        return DataSourceBuilder.create().build();
    }

    @Bean
    public SqlSessionFactory sqlSessionFactory(DataSource dataSource) throws Exception {
        MybatisSqlSessionFactoryBean factory = new MybatisSqlSessionFactoryBean();
        factory.setDataSource(dataSource);
        factory.setTypeAliasesPackage("net.qihoo.project.domain");
        factory.setMapperLocations(
            new PathMatchingResourcePatternResolver()
                .getResources("classpath:mapper/*.xml"));
        return factory.getObject();
    }

    @Bean
    public DataSourceTransactionManager transactionManager(DataSource dataSource) {
        return new DataSourceTransactionManager(dataSource);
    }
}
```

> **注意**：以上为核心配置代码,实际使用时需补充完整的 import 语句和异常处理。

---

## 八、OpenTelemetry 可观测性集成

### 8.1 架构

```
+---------------------------------------------+
|              Spring Boot 应用                |
|  +-------------------------------------+    |
|  |  opentelemetry-javaagent.jar        |    |
|  |  (自动注入 Traces/Metrics/Logs)      |    |
|  +-------------------------------------+    |
|  +-------------------------------------+    |
|  |  应用代码                            |    |
|  |  - @WithSpan 自定义链路              |    |
|  |  - MDC trace_id 日志关联             |    |
|  +-------------------------------------+    |
+---------------------------------------------+
                    |
                    v OTLP (gRPC/HTTP)
         +--------------------+
         |   OTel Collector   |
         +--------------------+
           |        |        |
           v        v        v
        Jaeger   Prometheus  Loki
```

### 8.2 Maven 依赖

在 pom.xml 中添加 OpenTelemetry JavaAgent 依赖:

```xml
<dependency>
    <groupId>net.qihoo.qilin</groupId>
    <artifactId>opentelemetry-javaagent</artifactId>
    <version>1.0</version>
</dependency>
```

### 8.3 JavaAgent 启动配置

**start.sh 核心配置**:

```bash
#!/bin/bash

# 应用名称（根据项目修改）
APP_NAME="project"
JAR_NAME="common-workspace-1.0-SNAPSHOT.jar"
AGENT_JAR="agent/opentelemetry-javaagent.jar"

# 固定配置
export OTEL_METRICS_EXPORTER=otlp
export OTEL_EXPORTER_OTLP_PROTOCOL=grpc
export OTEL_EXPORTER_OTLP_ENDPOINT=http://traces.dataway.lycc.qihoo.net:55682
export OTEL_EXPORTER_OTLP_COMPRESSION=gzip

# 服务名称（默认使用 APP_NAME，可通过环境变量覆盖）
if [ ! -n "$OPENTELEMETRY_SERVICE_NAME" ]; then
   OPENTELEMETRY_SERVICE_NAME=${APP_NAME}
fi
echo "OPENTELEMETRY_SERVICE_NAME:${OPENTELEMETRY_SERVICE_NAME}"

# 资源属性（根据项目调整 service.xHawkUserSpaceId）
export OTEL_RESOURCE_ATTRIBUTES=service.name=${OPENTELEMETRY_SERVICE_NAME},service.version=v1.0,service.xHawkUserSpaceId=1441348909877223426

# JVM 参数
JAVA_OPTS="-Xms512m -Xmx1024m"
JAVA_OPTS="${JAVA_OPTS} -javaagent:${AGENT_JAR}"

# 启动应用
java ${JAVA_OPTS} -jar lib/${JAR_NAME} --spring.profiles.active=prod
```

> **注意**：
> - `APP_NAME` 和 `JAR_NAME` 需根据实际项目调整
> - `OTEL_EXPORTER_OTLP_ENDPOINT` 为固定值：`http://traces.dataway.lycc.qihoo.net:55682`
> - `service.xHawkUserSpaceId` 需根据项目设置
> - 以上为核心配置，完整脚本还需添加日志、进程管理等逻辑

### 8.4 关键环境变量

| 变量 | 说明 | 必须 | 默认值/示例 |
|------|------|------|-------------|
| OPENTELEMETRY_SERVICE_NAME | 服务名称 | 否 | 默认使用 APP_NAME |
| OTEL_EXPORTER_OTLP_ENDPOINT | Collector 地址 | 是 | http://traces.dataway.lycc.qihoo.net:55682（固定值） |
| OTEL_EXPORTER_OTLP_PROTOCOL | 传输协议 | 是 | grpc |
| OTEL_METRICS_EXPORTER | Metrics 导出器 | 是 | otlp |
| OTEL_EXPORTER_OTLP_COMPRESSION | 压缩方式 | 建议 | gzip |
| OTEL_RESOURCE_ATTRIBUTES | 资源属性 | 是 | service.name/service.version/service.xHawkUserSpaceId |

### 8.5 自动埋点覆盖

JavaAgent 自动注入(无需改代码):

| 框架 | 说明 |
|------|------|
| Spring MVC | HTTP 入口 Span |
| JDBC / MyBatis | SQL 执行 Span |
| Redis (Jedis/Lettuce) | Redis 命令 Span |
| Kafka / RabbitMQ | 消息生产/消费 Span |
| gRPC | 客户端/服务端 |
| HttpClient / OkHttp | HTTP 出站 |
| Logback / Log4j2 | 自动注入 trace_id |

### 8.6 日志与 Trace 关联

**logback-spring.xml 核心配置**:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <appender name="CONSOLE" class="ch.qos.logback.core.ConsoleAppender">
        <encoder>
            <pattern>%d{yyyy-MM-dd HH:mm:ss.SSS} [%thread] [traceId=%X{trace_id}] [spanId=%X{span_id}] %-5level %logger{36} - %msg%n</pattern>
        </encoder>
    </appender>

    <appender name="FILE" class="ch.qos.logback.core.rolling.RollingFileAppender">
        <file>logs/app.log</file>
        <rollingPolicy class="ch.qos.logback.core.rolling.SizeAndTimeBasedRollingPolicy">
            <fileNamePattern>logs/app.%d{yyyy-MM-dd}.%i.log</fileNamePattern>
            <maxFileSize>100MB</maxFileSize>
            <maxHistory>30</maxHistory>
            <totalSizeCap>5GB</totalSizeCap>
        </rollingPolicy>
        <encoder>
            <pattern>%d{yyyy-MM-dd HH:mm:ss.SSS} [%thread] [traceId=%X{trace_id}] [spanId=%X{span_id}] %-5level %logger{36} - %msg%n</pattern>
        </encoder>
    </appender>

    <root level="INFO">
        <appender-ref ref="CONSOLE"/>
        <appender-ref ref="FILE"/>
    </root>
</configuration>
```

> **注意**：以上为核心 pattern 配置,完整的 logback-spring.xml 还需包含其他 appender 和 logger 配置。

### 8.7 注意事项

| 项 | 说明 |
|----|------|
| Maven 依赖 | 只需引入 `net.qihoo.qilin:opentelemetry-javaagent:1.0` |
| 自定义埋点 | 默认自动埋点已足够,无需额外注解 |
| 服务名称 | 通过 `OPENTELEMETRY_SERVICE_NAME` 设置,默认使用 APP_NAME |
| Collector 地址 | 固定值：http://traces.dataway.lycc.qihoo.net:55682 |
| 版本兼容 | 需 JDK 8+ |
| 内存开销 | Agent 约增加 50~100MB 堆外内存 |
| 敏感信息 | 不要在启动参数中暴露密码等敏感信息 |

---

## 九、标准依赖清单

**核心依赖示例**：

```xml
<dependencies>
    <!-- Spring Boot -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
    </dependency>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-validation</artifactId>
    </dependency>

    <!-- 数据库 -->
    <dependency>
        <groupId>com.baomidou</groupId>
        <artifactId>mybatis-plus-boot-starter</artifactId>
        <version>${mybatis-plus.version}</version>
    </dependency>
    <dependency>
        <groupId>mysql</groupId>
        <artifactId>mysql-connector-java</artifactId>
    </dependency>

    <!-- Redis -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-data-redis</artifactId>
    </dependency>

    <!-- Swagger -->
    <dependency>
        <groupId>org.springdoc</groupId>
        <artifactId>springdoc-openapi-starter-webmvc-ui</artifactId>
        <version>2.3.0</version>
    </dependency>

    <!-- Lombok -->
    <dependency>
        <groupId>org.projectlombok</groupId>
        <artifactId>lombok</artifactId>
        <scope>provided</scope>
    </dependency>

    <!-- 工具 -->
    <dependency>
        <groupId>org.apache.commons</groupId>
        <artifactId>commons-lang3</artifactId>
    </dependency>

    <!-- OpenTelemetry Agent -->
    <dependency>
        <groupId>net.qihoo.qilin</groupId>
        <artifactId>opentelemetry-javaagent</artifactId>
        <version>1.0</version>
    </dependency>

    <!-- 测试 -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-test</artifactId>
        <scope>test</scope>
    </dependency>
</dependencies>
```

> **注意**：以上为常用依赖示例,实际项目需根据需求添加其他依赖,并在 `<dependencyManagement>` 中统一管理版本。

---

## 十、新项目 Checklist

创建新项目时逐项确认:

**项目文件**:
- [ ] README.md 编写完整
- [ ] doc/sql/init.sql 建库建表脚本就绪
- [ ] .gitignore 配置
- [ ] CHANGELOG.md 创建
- [ ] Dockerfile(如需容器化)

**代码结构**:
- [ ] 包结构按第三章标准建立
- [ ] 启动类配置正确
- [ ] 统一响应 RestResult 引入
- [ ] BizException + ErrorCode 建立
- [ ] GlobalExceptionHandler 配置
- [ ] Swagger/OpenAPI 配置类就位

**基础设施**:
- [ ] MyBatis-Plus 配置 + Mapper 扫描
- [ ] logback-spring.xml 含 trace_id/span_id
- [ ] Maven profile(dev/prod)配置
- [ ] application.yml 敏感信息不入仓库

**可观测性**:
- [ ] OpenTelemetry Agent 放入 agent/ 目录
- [ ] 启动脚本包含 OTEL 环境变量
- [ ] 生产环境配置采样率
