---
领域: Java/Spring Boot
创建日期: 2026-03-05
状态: 已验证
---

# Java 代码规范

> 本规范用于指导 AI 代码生成和人工开发，涵盖命名、OOP、集合、并发、异常、日志、SQL、注解等全维度约束。

---

## 一、命名规范

### 1.1 包名

- 全小写，层级用 `.` 分隔，单词之间**不用**下划线或大写
- 统一格式：`{groupId}.{项目名}.{模块}`

```
✅ net.qihoo.project.workspace.service
✅ net.qihoo.project.workspace.controller
❌ net.qihoo.project.workSpace.Service
❌ net.qihoo.project.work_space.service
```

### 1.2 类名

| 类型 | 规则 | 示例 |
|------|------|------|
| 普通类 | UpperCamelCase | `WorkspaceService` |
| 抽象类 | `Abstract` 或 `Base` 开头 | `AbstractExporter`、`BaseService` |
| 异常类 | 以 `Exception` 结尾 | `WorkspaceException`、`BizException` |
| 枚举类 | UpperCamelCase，**不以** `Enum` 结尾 | `ErrorCode`、`OrderStatus` |
| 工具类 | 以 `Utils` 或 `Util` 结尾 | `DateUtils`、`StringUtil` |
| DTO/VO | 以 `Dto`、`Vo`、`Request`、`Response` 结尾 | `CreateWorkspaceDto`、`UserVo` |
| 实体类 | 与数据库表名对应，UpperCamelCase | `Workspace`、`WorkspaceMember` |
| 配置类 | 以 `Configuration` 或 `Config` 结尾 | `SwaggerConfiguration`、`RedisConfig` |
| 常量类 | UpperCamelCase | `Constants`、`RedisKeyConstants` |
| 测试类 | 被测类名 + `Test` | `WorkspaceServiceTest` |
| 接口实现类 | 接口名 + `Impl` | `WorkspaceServiceImpl` |

**领域对象命名**：

| 缩写 | 全称 | 用途 | 示例 |
|------|------|------|------|
| DO | Data Object | 与数据库表一一对应 | `WorkspaceDO` |
| BO | Business Object | 业务逻辑组合对象 | `OrderBO` |
| DTO | Data Transfer Object | 跨进程/层传输 | `CreateWorkspaceDto` |
| VO | View Object | 展示层对象 | `WorkspaceVo` |
| Query | - | 查询参数封装 | `WorkspaceQuery` |

### 1.3 方法名

- lowerCamelCase，动词或动宾短语
- 布尔返回值用 `is`/`has`/`can`/`should` 前缀

| 操作 | 前缀 | 示例 |
|------|------|------|
| 获取单个 | `get` | `getWorkspaceByCode()` |
| 获取列表 | `list`、`query` | `listWorkspaceByProduct()` |
| 获取统计 | `count` | `countMemberByWorkspace()` |
| 新增 | `create`、`add`、`insert`、`save` | `createWorkspace()` |
| 修改 | `update`、`modify` | `updateWorkspace()` |
| 删除 | `delete`、`remove` | `deleteWorkspace()` |
| 校验 | `check`、`validate`、`verify` | `checkProduct()` |
| 转换 | `convert`、`to`、`parse` | `convertToDto()` |

```java
✅ getWorkspaceInfo()
✅ listWorkspaceByProduct()
✅ countMemberByWorkspace()
❌ workspace_info()
❌ DoCreate()
❌ getdata()
```

### 1.4 变量名

- lowerCamelCase
- 常量：全大写 + 下划线分隔 `MAX_RETRY_COUNT`
- 布尔变量不加 `is` 前缀（POJO 中），避免部分框架序列化问题
- 集合变量体现复数或类型：`workspaceList`、`userMap`、`roleSet`
- 数组变量用复数：`String[] names`（不是 `nameArray`）
- 临时变量也要有意义：`for (Workspace ws : list)` 优于 `for (Workspace w : list)`
- 接口中的变量默认 `public static final`，不需要加修饰符

### 1.5 常量定义

- **禁止魔法值**（未经定义的常量直接出现在代码中），必须定义为常量或枚举
- 常量类用 `final class` + 私有构造器，禁止实例化
- 不同模块的常量分类管理，禁止一个 Constants 放几百个常量
- 长整型后缀用大写 `L`：`long a = 2L`（不是 `2l`，避免和数字 1 混淆）

```java
public final class Constants {
    private Constants() {}
    public static final String UTF_8 = "UTF-8";
    public static final int DEFAULT_PAGE_SIZE = 20;
    public static final long TOKEN_EXPIRE_MS = 3600_000L;  // 下划线增强可读性
}

// ❌ 魔法值
if (status == 3) { ... }
// ✅ 枚举
if (status == OrderStatus.COMPLETED.getCode()) { ... }
```

---

## 二、OOP 规约

### 2.1 基本规则

- 静态方法/变量用**类名**直接访问，禁止通过对象引用访问
- 所有覆写方法必须加 `@Override` 注解
- 可变参数 `Object... args` 只能用在外部接口
- 过时的接口用 `@Deprecated` 注解，并在 Javadoc 中说明替代方案
- 使用常量或确定有值的对象调用 `equals`：`"value".equals(variable)`
- **所有包装类型的比较用 `equals`**，禁止用 `==`

```java
// ❌ Integer 缓存池 -128~127 之外 == 失效
Integer a = 200; Integer b = 200;
if (a == b) { ... }  // false！

// ✅
if (Objects.equals(a, b)) { ... }
```

### 2.2 POJO 规约

- POJO 类必须覆写 `toString()`（用 Lombok `@Data` 或 `@ToString`）
- POJO 类属性使用**包装类型**（`Integer` 而非 `int`），RPC 返回值和方法参数同理
- POJO 类属性**不设默认值**（让调用方显式赋值）
- 序列化类新增属性时不要修改 `serialVersionUID`
- 构造方法禁止加业务逻辑，复杂初始化用 `init()` 方法

### 2.3 继承与设计

- 继承层次不超过 3 层
- 优先使用组合而非继承（Composition over Inheritance）
- 接口中不要定义变量（除非是真正的全局常量）
- 一个方法只做一件事，方法体不超过 80 行
- 方法参数不超过 5 个，超过封装为对象
- 方法入参禁止用 `Map`（可读性差、无法校验），用 DTO
- 不要在 `foreach` 中进行 `add/remove`，用 `Iterator` 或 `removeIf()`

```java
// ❌ 参数过多
void createUser(String name, String email, String phone,
                Integer age, String dept, Integer roleId) { ... }
// ✅ 封装
void createUser(CreateUserRequest request) { ... }
```

---

## 三、集合处理规范

### 3.1 集合判空

```java
// ✅ 工具类
if (CollectionUtils.isEmpty(list)) { ... }
if (MapUtils.isEmpty(map)) { ... }

// ❌ 手动判空
if (list != null && list.size() > 0) { ... }
```

### 3.2 集合转换陷阱

```java
// ❌ Arrays.asList 返回的 List 不支持 add/remove
List<String> list = Arrays.asList("a", "b");
list.add("c");  // UnsupportedOperationException

// ✅ 包一层
List<String> list = new ArrayList<>(Arrays.asList("a", "b"));

// ❌ subList 返回视图，原 List 修改会导致 ConcurrentModificationException
List<String> sub = originalList.subList(0, 3);
originalList.add("new");  // 崩

// ✅ 独立副本
List<String> sub = new ArrayList<>(originalList.subList(0, 3));
```

### 3.3 Map 使用

```java
// ✅ 指定初始容量
int capacity = (int) (expectedSize / 0.75F) + 1;
Map<String, Object> map = new HashMap<>(capacity);

// ✅ 遍历 entrySet（比 keySet 少一次 get）
for (Map.Entry<String, Object> entry : map.entrySet()) { ... }

// ✅ computeIfAbsent 替代 containsKey + put
map.computeIfAbsent(key, k -> new ArrayList<>()).add(value);
```

### 3.4 Stream 使用

```java
// ✅ 函数式，不修改外部状态
List<String> result = list.stream()
    .filter(StringUtils::isNotBlank)
    .map(String::trim)
    .collect(Collectors.toList());

// ✅ toMap 必须处理 key 冲突
Map<String, User> map = users.stream()
    .collect(Collectors.toMap(User::getName, Function.identity(), (k1, k2) -> k1));

// ❌ toMap 不处理冲突 → key 重复直接抛异常
Map<String, User> map = users.stream()
    .collect(Collectors.toMap(User::getName, Function.identity()));

// ❌ Stream 中修改外部可变对象（非线程安全）
List<String> external = new ArrayList<>();
list.stream().forEach(item -> external.add(item));
```

### 3.5 通用规则

- 集合泛型使用钻石运算符（JDK7+）：`List<String> list = new ArrayList<>()`
- 返回空集合用 `Collections.emptyList()` 而非 `null`
- 需要不可变集合用 `Collections.unmodifiableList()`
- 集合初始化尽量指定大小

---

## 四、并发处理规范

### 4.1 线程池

```java
// ❌ 禁止 Executors（队列无界 → OOM）
ExecutorService pool = Executors.newFixedThreadPool(10);

// ✅ 手动创建
ThreadPoolExecutor executor = new ThreadPoolExecutor(
    5, 10,                                   // core / max
    60L, TimeUnit.SECONDS,                   // keepAlive
    new LinkedBlockingQueue<>(200),           // 有界队列
    new ThreadFactoryBuilder()
        .setNameFormat("biz-worker-%d")       // 线程命名
        .build(),
    new ThreadPoolExecutor.CallerRunsPolicy() // 拒绝策略
);
```

### 4.2 ThreadLocal

```java
private static final ThreadLocal<UserContext> CONTEXT = new ThreadLocal<>();

public void process() {
    try {
        CONTEXT.set(new UserContext());
        // 业务逻辑...
    } finally {
        CONTEXT.remove();  // 必须！线程池复用会串数据
    }
}
```

### 4.3 锁与原子操作

- 加锁范围尽量小，不锁整个方法
- 多资源加锁注意顺序，避免死锁
- `volatile` 解决可见性但不解决原子性，count++ 用 `AtomicInteger` / `LongAdder`
- `ConcurrentHashMap` 的 get/put 是安全的，组合操作（check-then-act）不安全

```java
// ❌ 组合操作不安全
if (!map.containsKey(key)) { map.put(key, value); }
// ✅ 原子操作
map.putIfAbsent(key, value);
map.computeIfAbsent(key, k -> createValue());
```

### 4.4 日期线程安全

```java
// ❌ SimpleDateFormat 非线程安全
private static final SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd");

// ✅ DateTimeFormatter 线程安全
private static final DateTimeFormatter FORMATTER = DateTimeFormatter.ofPattern("yyyy-MM-dd");

// ✅ 优先使用 Java 8 时间 API
LocalDate.now();  LocalDateTime.now();  Instant.now();
```

### 4.5 高并发注意

- 高并发用 `ThreadLocalRandom` 代替 `Random`
- 定时任务/异步任务异常必须 catch，否则线程默默死掉

```java
@Scheduled(fixedDelay = 60_000)
public void scheduledTask() {
    try {
        // ...
    } catch (Exception e) {
        log.error("定时任务执行失败", e);
    }
}
```

---

## 五、异常处理规范

### 5.1 自定义异常体系

```java
public class BizException extends RuntimeException {
    private String code;
    private String message;
    private String[] msgParams;

    public BizException(ErrorCode errorCode) {
        super(errorCode.getMessage());
        this.code = errorCode.getCode();
        this.message = errorCode.getMessage();
    }

    public BizException(ErrorCode errorCode, Throwable cause) {
        super(errorCode.getMessage(), cause);
        this.code = errorCode.getCode();
        this.message = errorCode.getMessage();
    }

    public BizException(ErrorCode errorCode, String[] msgParams) {
        super(errorCode.getMessage());
        this.code = errorCode.getCode();
        this.message = errorCode.getMessage();
        this.msgParams = msgParams != null ? msgParams.clone() : null;
    }

    public BizException(String code, String message) {
        super(message);
        this.code = code;
        this.message = message;
    }
    // getter 省略
}
```

### 5.2 错误码枚举

按模块划分编码段，禁止跨模块复用，禁止重复：

```java
public enum ErrorCode {
    // 通用 1xxxxx
    PARAM_VALIDATE_ERROR("100001", "{0}"),
    PARAM_IS_NULL("100002", "参数不能为空！"),
    SERVER_INTERNAL_ERROR("500", "服务器内部错误，请联系管理员！"),
    AUTH_TOKEN_ERROR("401", "身份信息认证失败"),

    // 模块A 2xxxxx
    WORKSPACE_NOT_FOUND("200001", "项目不存在！"),
    WORKSPACE_CODE_EXISTS("200002", "项目编码已存在！"),
    WORKSPACE_CREATE_FAILED("200003", "项目创建失败！"),
    ;

    private final String code;
    private final String message;
    ErrorCode(String code, String message) { this.code = code; this.message = message; }
    public String getCode() { return code; }
    public String getMessage() { return message; }
}
```

### 5.3 基本规则

- **禁止**空 catch 块
- **禁止** catch Exception 不记日志
- **禁止**用 `return` 代替 `throw`
- 日志必须打完整堆栈：`log.error("msg", e)` 不是 `log.error(e.getMessage())`
- 事务方法中抛出的异常不要在方法内 catch（否则事务不回滚）
- `finally` 中不要 `return`（会覆盖 try 中的 return/throw）
- 异常不要用来做流程控制（性能差）
- 能 catch 具体异常就 catch 具体的，不要大而全 catch Exception

### 5.4 Service 层双层 catch 模式

```java
@Override
public WorkspaceDto getWorkspaceInfo(String code) {
    try {
        if (StringUtils.isBlank(code)) {
            throw new BizException(ErrorCode.PARAM_IS_NULL);
        }
        // 业务逻辑...
        return result;
    } catch (BizException e) {
        log.error("BizException: ", e);
        throw e;                                       // 原样抛出
    } catch (Exception e) {
        log.error("Unexpected error: ", e);
        throw new BizException(ErrorCode.WORKSPACE_NOT_FOUND);  // 包装
    }
}
```

### 5.5 全局异常处理器

Controller 层不写 try-catch，统一由 `@ControllerAdvice` 处理：

```java
@ControllerAdvice
@ResponseBody
@Slf4j
public class GlobalExceptionHandler {

    @ExceptionHandler(BizException.class)
    @ResponseStatus(HttpStatus.OK)
    public RestResult<?> handleBizException(BizException e) {
        log.error("BizException: ", e);
        return RestResult.fail(e.getMessage(), e.getCode(), e.getMsgParams());
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    @ResponseStatus(HttpStatus.OK)
    public RestResult<?> handleValidException(MethodArgumentNotValidException e) {
        log.error("Validation error: ", e);
        String msg = e.getBindingResult().getFieldErrors().stream()
            .map(FieldError::getDefaultMessage).collect(Collectors.joining("; "));
        return RestResult.fail(msg, ErrorCode.PARAM_VALIDATE_ERROR.getCode());
    }

    @ExceptionHandler(ConstraintViolationException.class)
    @ResponseStatus(HttpStatus.OK)
    public RestResult<?> handleConstraintViolation(ConstraintViolationException e) {
        log.error("Constraint violation: ", e);
        String msg = e.getConstraintViolations().stream()
            .map(v -> v.getPropertyPath() + ": " + v.getMessage())
            .collect(Collectors.joining("; "));
        return RestResult.fail(msg, ErrorCode.PARAM_VALIDATE_ERROR.getCode());
    }

    @ExceptionHandler(HttpRequestMethodNotSupportedException.class)
    @ResponseStatus(HttpStatus.METHOD_NOT_ALLOWED)
    public RestResult<?> handleMethodNotAllowed(HttpRequestMethodNotSupportedException e) {
        return RestResult.fail("请求方法不支持: " + e.getMethod(), "405");
    }

    @ExceptionHandler(Exception.class)
    @ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)
    public RestResult<?> handleException(Exception e) {
        log.error("Unhandled exception: ", e);
        return RestResult.fail(ErrorCode.SERVER_INTERNAL_ERROR.getMessage(),
                               ErrorCode.SERVER_INTERNAL_ERROR.getCode());
    }
}
```

---

## 六、接口返回结构规范

### 6.1 统一响应

```java
@Data
public class RestResult<T> {
    private boolean success;
    private String code;
    private String message;
    private String[] msgParams;
    private T data;

    public static <T> RestResult<T> success(T data) {
        RestResult<T> r = new RestResult<>();
        r.setSuccess(true); r.setCode("0"); r.setData(data);
        return r;
    }
    public static <T> RestResult<T> fail(String message, String code) {
        RestResult<T> r = new RestResult<>();
        r.setSuccess(false); r.setCode(code); r.setMessage(message);
        return r;
    }
    public static <T> RestResult<T> fail(String message, String code, String[] msgParams) {
        RestResult<T> r = fail(message, code); r.setMsgParams(msgParams); return r;
    }
}
```

### 6.2 分页响应

```java
@Data
public class PageResult<T> {
    private long total;
    private long page;
    private long pageSize;
    private List<T> records;

    public static <T> RestResult<PageResult<T>> success(IPage<T> page) {
        PageResult<T> p = new PageResult<>();
        p.setTotal(page.getTotal()); p.setPage(page.getCurrent());
        p.setPageSize(page.getSize()); p.setRecords(page.getRecords());
        return RestResult.success(p);
    }
}
```

### 6.3 Controller 规则

- 返回类型统一 `RestResult<T>`
- 成功：`RestResult.success(data)`
- 失败：由异常 + 全局处理器包装，**禁止** Controller 直接返回 `null`

---

## 七、Spring Boot 注解规范

### 7.1 Controller

```java
@Slf4j
@RestController
@RequestMapping("/api/v1/workspace")
@Tag(name = "工作空间管理", description = "工作空间增删改查接口")
public class WorkspaceController {

    @Autowired
    private WorkspaceService workspaceService;

    @Operation(summary = "创建工作空间")
    @PostMapping("/create")
    public RestResult<Integer> createWorkspace(
            @RequestBody @Valid CreateWorkspaceRequest request) {
        return RestResult.success(workspaceService.createWorkspace(request));
    }
}
```

**规则**：
- URL 全小写，单词用 `-` 分隔：`/api/v1/resource-group`
- 用 `@GetMapping` / `@PostMapping` / `@PutMapping` / `@DeleteMapping`，禁止方法级用 `@RequestMapping`
- `@RequestBody` 搭配 `@Valid` 触发校验

### 7.2 Service

```java
@Service
@Slf4j
public class WorkspaceServiceImpl implements WorkspaceService {

    @Autowired
    private WorkspaceDao workspaceDao;

    @Transactional(rollbackFor = Exception.class)
    @Override
    public Integer createWorkspace(CreateWorkspaceRequest request) { ... }
}
```

**`@Transactional` 规则**：
- **必须**指定 `rollbackFor = Exception.class`
- 只读查询加 `readOnly = true` 或不加
- 禁止在 private 方法上用（AOP 不生效）
- 禁止类内部方法互调依赖事务（同类调用不走代理）
- 事务方法中不放 RPC/耗时 I/O（占连接）

### 7.3 DAO

```java
@Repository
public interface WorkspaceDao extends BaseMapper<Workspace> {
    Workspace selectByCode(@Param("code") String code);
    Integer batchUpdateDeleteMarkById(@Param("items") List<IdDeleteMark> items);
}
```

- 加 `@Repository`，继承 `BaseMapper<T>`，参数加 `@Param`，批量方法用 `batch` 前缀

### 7.4 实体类

```java
@Data
@TableName("t_workspace")
public class Workspace {
    @TableId(value = "id", type = IdType.AUTO)
    private Long id;
    private String name;
    private String code;
    @TableField("`description`")
    private String description;
    private Long createTime;
    private Long updateTime;
}
```

- `t_` 前缀表名，`@TableId` 指定主键策略，关键字字段反引号转义，字段不设默认值

### 7.5 请求 DTO 校验

```java
@Data
@Schema(description = "创建工作空间请求")
public class CreateWorkspaceRequest {

    @NotBlank(message = "名称不能为空")
    @Size(max = 64, message = "名称不超过64字符")
    @Schema(description = "工作空间名称", example = "数据开发项目")
    private String name;

    @NotBlank(message = "编码不能为空")
    @Pattern(regexp = "^[a-zA-Z0-9_\\u4e00-\\u9fa5-]+$", message = "编码格式不符合要求")
    @Schema(description = "工作空间编码", example = "proj-data-dev")
    private String workspaceCode;

    @NotNull(message = "产品标识不能为空")
    private String product;

    @NotEmpty(message = "成员列表不能为空")
    @Valid
    private List<MemberRoleDto> members;
}
```

**校验注解速查**：

| 注解 | 类型 | 含义 |
|------|------|------|
| `@NotNull` | 任意 | 不为 null |
| `@NotBlank` | String | 非 null 且 trim 后非空 |
| `@NotEmpty` | String/Collection/Array | 非 null 且 size > 0 |
| `@Size(min,max)` | String/Collection | 长度范围 |
| `@Pattern` | String | 正则匹配 |
| `@Min` / `@Max` | 数值 | 最小/最大值 |
| `@Email` | String | 邮箱格式 |
| `@Positive` | 数值 | 正数 |
| `@Valid` | 嵌套对象 | 级联校验 |

**自定义校验器**：

```java
@Target({FIELD, PARAMETER})
@Retention(RUNTIME)
@Constraint(validatedBy = PhoneValidator.class)
public @interface Phone {
    String message() default "手机号格式不正确";
    Class<?>[] groups() default {};
    Class<? extends Payload>[] payload() default {};
}

public class PhoneValidator implements ConstraintValidator<Phone, String> {
    private static final Pattern P = Pattern.compile("^1[3-9]\\d{9}$");
    @Override
    public boolean isValid(String v, ConstraintValidatorContext ctx) {
        return v == null || P.matcher(v).matches();
    }
}
```

---

## 八、Swagger/OpenAPI 注解规范

### 8.1 版本选择

| 版本 | 依赖 | 注解包 | 推荐 |
|------|------|--------|------|
| 2.x | springfox | `io.swagger.annotations` | 存量项目 |
| 3.x | springdoc-openapi | `io.swagger.v3.oas.annotations` | **新项目** |

### 8.2 对照表

| 2.x | 3.x | 位置 |
|-----|-----|------|
| `@Api(tags)` | `@Tag(name, description)` | 类 |
| `@ApiOperation(value)` | `@Operation(summary)` | 方法 |
| `@ApiParam(value)` | `@Parameter(description)` | 参数 |
| `@ApiModel` | `@Schema(description)` | DTO 类 |
| `@ApiModelProperty` | `@Schema(description, example)` | DTO 字段 |
| `@ApiIgnore` | `@Hidden` | 隐藏接口 |

### 8.3 3.x 标准用法

```java
@Tag(name = "用户管理", description = "用户增删改查")

@Operation(summary = "根据ID查询用户")
@ApiResponses({
    @ApiResponse(responseCode = "200", description = "成功",
        content = @Content(schema = @Schema(implementation = UserDto.class))),
    @ApiResponse(responseCode = "404", description = "用户不存在")
})
@GetMapping("/{id}")
public RestResult<UserDto> getUser(
    @Parameter(description = "用户ID", required = true, example = "1001")
    @PathVariable Long id) { ... }

@Schema(description = "用户信息")
@Data
public class UserDto {
    @Schema(description = "用户ID", example = "1001")
    private Long id;
    @Schema(description = "用户名", example = "zhangsan")
    private String username;
}
```

### 8.4 2.x 标准用法（存量项目）

```java
@Api(tags = "工作空间管理")
@RestController
public class ApiController {

    @ApiOperation(value = "获取详情", notes = "根据编码获取工作空间完整信息")
    @GetMapping("/workspace/{code}")
    public RestResult<WorkspaceDto> get(
        @ApiParam(name = "code", value = "编码", required = true)
        @PathVariable String code) { ... }
}
```

### 8.5 配置类

**3.x（springdoc）**：

```java
@Configuration
public class OpenApiConfig {
    @Bean
    public OpenAPI customOpenAPI() {
        return new OpenAPI()
            .info(new Info().title("API 文档").version("v1.0.0")
                .contact(new Contact().name("开发团队").email("dev@example.com")));
    }
}
```

**2.x（springfox）**：

```java
@Configuration
@EnableSwagger2
public class SwaggerConfiguration {
    @Bean
    public Docket api() {
        return new Docket(DocumentationType.SWAGGER_2)
            .select()
            .apis(RequestHandlerSelectors.withClassAnnotation(RestController.class))
            .paths(PathSelectors.any())
            .build()
            .apiInfo(new ApiInfoBuilder().title("API 文档").version("v1.0.0").build());
    }
}
```

### 8.6 注解规则

- 每个 Controller **必须**有 `@Tag` / `@Api(tags)`
- 每个方法 **必须**有 `@Operation(summary)` / `@ApiOperation(value)`
- 路径/查询参数 **必须**有 `@Parameter` / `@ApiParam`
- DTO 字段 **必须**有 `@Schema(description)` / `@ApiModelProperty`，核心字段加 `example`
- 一个 Controller 只对应一个业务域
- 内部不对外的接口加 `@Hidden` / `@ApiIgnore`

---

## 九、日志规范

### 9.1 框架

- SLF4J + Logback，类上 `@Slf4j`
- **禁止** `System.out.println`、`e.printStackTrace()`
- **禁止**直接用 Log4j/Logback API（必须通过 SLF4J 门面）

### 9.2 级别

| 级别 | 场景 | 生产 |
|------|------|------|
| `ERROR` | 系统错误、需告警 | ✅ |
| `WARN` | 可恢复异常、降级 | ✅ |
| `INFO` | 重要业务节点 | ✅ |
| `DEBUG` | 调试、入参出参 | ❌ |
| `TRACE` | 极详细调试 | ❌ |

### 9.3 书写规则

```java
// ✅ 占位符
log.info("创建工作空间成功, code={}, name={}", code, name);
// ✅ 异常完整堆栈
log.error("失败, code={}", code, e);
// ✅ 条件判断
if (log.isDebugEnabled()) { log.debug("详情: {}", expensiveToString(obj)); }

// ❌ 字符串拼接
log.info("成功, code=" + code);
// ❌ 只打消息
log.error("失败: " + e.getMessage());
// ❌ 循环内打日志
for (Item item : bigList) { log.info("处理: {}", item); }
// ✅ 批量摘要
log.info("批量处理完成, total={}, success={}, fail={}", total, success, fail);
// ❌ 敏感信息
log.info("登录, password={}", password);
```

### 9.4 内容规范

- ERROR：操作描述 + 关键参数 + 异常对象
- INFO：谁 + 做了什么 + 结果
- 外部调用前后各一条日志（含耗时）
- 定时任务开始/结束各一条

```java
long start = System.currentTimeMillis();
log.info("调用用户服务, userId={}", userId);
UserDto user = userService.getById(userId);
log.info("用户服务返回, userId={}, cost={}ms", userId, System.currentTimeMillis() - start);
```

### 9.5 日志格式

```xml
<pattern>%d{yyyy-MM-dd HH:mm:ss.SSS} [%thread] [traceId=%X{trace_id}] [spanId=%X{span_id}] %-5level %logger{36} - %msg%n</pattern>
```

---

## 十、数据库规范

### 10.1 建表

- 表名：小写下划线，`t_` 前缀
- 字段名：小写下划线
- 主键：`id BIGINT UNSIGNED AUTO_INCREMENT`
- **必须有** `create_time`、`update_time`
- 逻辑删除：`is_deleted TINYINT DEFAULT 0`
- 禁止关键字做字段名
- 表和字段必须有 `COMMENT`
- 字符集 `utf8mb4`

```sql
CREATE TABLE `t_workspace` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
    `name` VARCHAR(64) NOT NULL COMMENT '名称',
    `code` VARCHAR(64) NOT NULL COMMENT '编码',
    `description` VARCHAR(256) DEFAULT NULL COMMENT '描述',
    `is_deleted` TINYINT NOT NULL DEFAULT 0 COMMENT '0-未删 1-已删',
    `create_time` BIGINT NOT NULL COMMENT '创建时间(ms)',
    `update_time` BIGINT NOT NULL COMMENT '更新时间(ms)',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_code` (`code`),
    KEY `idx_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工作空间表';
```

### 10.2 字段类型

| 场景 | 推荐 | 禁止 |
|------|------|------|
| 主键 | `BIGINT UNSIGNED` | `INT` |
| 字符串 | `VARCHAR(n)` | 不必要的 `TEXT` |
| 金额 | `DECIMAL(10,2)` | `FLOAT`/`DOUBLE` |
| 布尔 | `TINYINT(1)` | `BIT`、`CHAR(1)` |
| 时间 | `BIGINT` 或 `DATETIME` | `TIMESTAMP`（2038问题） |
| 枚举 | `TINYINT` + COMMENT | `ENUM` 类型 |
| JSON | `JSON`（5.7+） | `TEXT` 存 JSON |

### 10.3 索引

- 唯一字段加 `UNIQUE KEY uk_xxx`
- 查询条件加 `KEY idx_xxx`
- 联合索引：最左前缀原则，高区分度字段在前
- 单表索引 ≤ 5 个，单索引字段 ≤ 5 个
- 不在索引列上做计算/函数（索引失效）

### 10.4 SQL

- **禁止** `SELECT *`
- 批量操作分批（每批 20~100）
- `IN` 不超过 500 个值
- WHERE 索引字段禁止函数运算
- `COUNT(*)` 统计行数，`COUNT(column)` 统计非 null
- 判 null 用 `IS NULL`，不用 `= null`
- `LEFT JOIN` 不超过 3 张表
- `UPDATE`/`DELETE` 必须有 `WHERE`
- 生产优先逻辑删除
- 不用存储过程和触发器

### 10.5 ORM

- 查询结果禁止用 `HashMap` 接收，用 POJO
- 分页用 MyBatis-Plus `IPage` 或 `PageHelper`
- 更新只改变化字段
- 不需要事务的查询不加 `@Transactional`

---

## 十一、代码格式

### 11.1 基本

- 缩进：4 空格，禁 Tab
- 单行 ≤ 120 字符
- 方法体 ≤ 80 行
- 类文件 ≤ 2000 行
- import 不用 `*`，按 JDK → 第三方 → 项目分组
- 空行分隔逻辑块
- K&R 风格大括号（左不换行，右独占行）

### 11.2 空格

```java
int result = a + b;                  // 运算符两侧
if (condition) {                     // 关键字与括号之间
method(arg1, arg2);                  // 逗号后
int x = (int) longValue;            // 强转后
```

### 11.3 换行

```java
// 参数多时每参数一行，缩进 8 空格
public void create(
        String name,
        String code,
        String product) { ... }

// 链式调用
List<String> result = list.stream()
        .filter(Objects::nonNull)
        .map(String::trim)
        .collect(Collectors.toList());

// 长条件，逻辑运算符放行首
if (condition1
        && condition2
        && condition3) { ... }
```

### 11.4 控制语句

- if/else/for/while/do **必须用大括号**，即使只有一行
- 三层以上 if 嵌套 → 卫语句或策略模式重构
- 避免取反逻辑：`if (!isNotEmpty())` → `if (isEmpty())`

---

## 十二、注释规范

### 12.1 Javadoc

- 类/接口：必须有 Javadoc，注明 `@author` 和 `@date`
- public 方法：必须有 Javadoc，注明参数和返回值
- 方法内部：只注释"为什么"不注释"是什么"

```java
/**
 * 工作空间服务
 *
 * @author xubo
 * @date 2024/10/14
 */
@Service
public class WorkspaceServiceImpl implements WorkspaceService {

    /**
     * 根据编码查询工作空间详情
     *
     * @param code 工作空间编码
     * @return 工作空间信息，不存在时抛 BizException
     */
    @Override
    public WorkspaceDto getWorkspaceInfo(String code) { ... }
}
```

### 12.2 其他注释

- TODO 格式：`// TODO [作者] 描述`
- FIXME 格式：`// FIXME [作者] 描述`
- 禁止大段注释掉的代码残留（用 Git 管理历史）
- 枚举/常量每个值必须有注释说明含义

---

## 十三、安全规范

### 13.1 输入校验

- 所有外部输入（HTTP 参数、文件、MQ 消息）必须校验
- SQL 参数用 `#{}` 预编译，**禁止** `${}`（SQL 注入）
- 文件上传校验：类型、大小、文件名（防 `../` 路径穿越）

### 13.2 敏感信息

- 日志禁止打印密码、Token、身份证、完整手机号
- 如需打印用脱敏：`138****5678`
- 配置文件密码用环境变量或加密存储
- 接口返回敏感字段做脱敏

### 13.3 接口安全

- 对外接口必须鉴权
- 敏感操作（删除、改密）需权限校验
- 核心接口加限流
- 禁止返回服务器内部堆栈（全局异常处理器兜底）
