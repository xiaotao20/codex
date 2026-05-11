# Java 什么样的代码才是好的代码

很多人一提“好代码”，第一反应是：

- 代码优雅
- 设计高级
- 用了很多设计模式
- 写得很聪明

但在真实项目里，**好代码首先不是“聪明”，而是“可靠、清楚、能维护”。**

如果只用一句话概括：

**好的 Java 代码，是别人能读懂、敢修改、不容易出错、出了问题也容易定位的代码。**

---

## 1. 好代码最核心的 7 个标准

### 1. 能读懂

这是第一位的。

如果一段代码只有作者自己能看懂，那它再“高级”也很危险。

好代码通常有这些特点：

- 类名、方法名、变量名能表达真实含义
- 一个方法只做一件事
- 逻辑顺序自然，不绕
- 少让读代码的人来回跳

反例：

```java
public void handle(List<User> list) {
    for (User u : list) {
        if (u != null && u.getStatus() == 1 && u.getAge() > 18) {
            // ...
        }
    }
}
```

问题不是它不能运行，而是：

- `handle` 这个名字太空
- `status == 1` 看不出业务含义
- 条件挤在一起，读起来费劲

更好的写法：

```java
public void processActiveAdultUsers(List<User> users) {
    for (User user : users) {
        if (isActiveAdult(user)) {
            // ...
        }
    }
}

private boolean isActiveAdult(User user) {
    return user != null
            && UserStatus.ACTIVE.equals(user.getStatus())
            && user.getAge() > 18;
}
```

这里的重点不是“拆方法”本身，而是让业务意图更清楚。

### 2. 容易改

现实里的代码不是写完就不动，而是会不停改需求。

所以好代码不是“现在能跑”，而是“下个月改起来不崩”。

容易改的代码通常有这些特征：

- 改一个地方，不需要牵一大片
- 业务规则集中，不是散落 everywhere
- 公共逻辑有复用，但不过度抽象
- 模块边界清楚

坏味道：

- 一个 `Service` 文件 2000 行
- 控制器里直接写 SQL 或复杂业务
- 到处复制粘贴同一段逻辑
- 一个改动要改 7 个地方

### 3. 不容易出错

好代码不是靠“开发者小心一点”来保证质量，而是尽量通过代码结构降低犯错概率。

比如：

- 参数校验明确
- 空值处理明确
- 状态流转明确
- 边界条件明确
- 异常处理明确

反例：

```java
public BigDecimal calculateDiscount(Order order) {
    return order.getAmount().multiply(order.getDiscountRate());
}
```

这段代码的问题是默认：

- `order` 一定不为 `null`
- `amount` 一定不为 `null`
- `discountRate` 一定不为 `null`

这在真实系统里通常不成立。

更稳妥的写法：

```java
public BigDecimal calculateDiscount(Order order) {
    Objects.requireNonNull(order, "order must not be null");
    Objects.requireNonNull(order.getAmount(), "order amount must not be null");
    Objects.requireNonNull(order.getDiscountRate(), "discount rate must not be null");

    return order.getAmount().multiply(order.getDiscountRate());
}
```

如果业务允许空值，也应该把默认行为写清楚，而不是“赌不会出问题”。

### 4. 出问题时容易查

很多代码平时看起来没问题，但线上一出问题就找不到原因。

这类代码通常缺：

- 关键日志
- 明确异常信息
- 稳定的错误边界
- 关键上下文信息

比如下面这种异常处理就很差：

```java
try {
    paymentClient.pay(request);
} catch (Exception e) {
    log.error("pay failed");
}
```

问题在于：

- 把异常吞了
- 没有订单号
- 没有请求上下文
- 没有错误原因

更好的写法：

```java
try {
    paymentClient.pay(request);
} catch (Exception e) {
    log.error("payment failed, orderId={}, userId={}", request.getOrderId(), request.getUserId(), e);
    throw new PaymentException("payment failed for orderId=" + request.getOrderId(), e);
}
```

### 5. 有一致性

好代码不只是单点写得好，还要和整个项目风格一致。

比如一致的：

- 命名方式
- 分层结构
- 异常处理方式
- DTO / VO / Entity 使用方式
- 日志风格
- 返回值风格

如果一个项目里：

- 有的类叫 `UserManager`
- 有的叫 `UserService`
- 有的叫 `UserHelper`
- 有的又叫 `UserProcessor`

但职责边界全都差不多，那长期维护一定会乱。

### 6. 有测试或容易验证

好代码不一定要求测试覆盖率特别漂亮，但至少要：

- 核心逻辑能测
- 关键路径可验证
- 变更后能快速回归

如果一段代码写完后只能靠“上线看看”，那风险就很高。

Java 里常见的最低要求通常是：

- 核心 service 有单元测试
- 关键流程有集成测试
- 复杂 bug 修复有回归测试

### 7. 性能合理，而不是过度优化

好代码不是一上来就追求极限性能，而是在业务需要的前提下保持合理。

错误思路：

- 还没确认瓶颈，就先写一堆复杂缓存
- 为了少创建几个对象，把代码写得很难懂
- 把简单逻辑过早并发化

更好的原则是：

1. 先写清楚
2. 再确认瓶颈
3. 再针对性优化

---

## 2. Java 里什么样的代码通常不算好代码

下面这些情况，在真实项目里很常见。

### 1. 方法太长

如果一个方法已经长到：

- 看不出主流程
- 同时处理校验、转换、查询、计算、保存、通知

那通常就该拆了。

一个方法太长，最直接的问题不是“丑”，而是：

- 很难复用
- 很难测试
- 很难定位问题
- 很难安全修改

### 2. 类职责太多

比如一个 `OrderService` 同时负责：

- 参数校验
- 价格计算
- 库存判断
- 下单写库
- 发消息
- 写日志
- 拼返回对象

这就是典型的职责堆积。

更合理的方式是按职责拆开，让主流程可读。

### 3. 命名偷懒

这些名字都很常见，也都很危险：

- `data`
- `info`
- `obj`
- `temp`
- `doProcess`
- `handle`
- `execute`

不是说这些词永远不能用，而是大多数时候它们没有提供足够的信息。

例如：

```java
public void process(Data data)
```

读的人根本不知道：

- 处理什么
- 为什么处理
- 处理完会怎样

### 4. 滥用 `if-else`

如果业务分支很多，代码很容易变成这样：

```java
if (type == 1) {
    ...
} else if (type == 2) {
    ...
} else if (type == 3) {
    ...
} else if (type == 4) {
    ...
}
```

这种代码短期能用，长期会越来越重。

常见改进方式：

- 枚举
- 策略模式
- 工厂 + 处理器映射

但也别一看到分支就上模式。重点是：**复杂度是不是已经开始伤害维护。**

### 5. 魔法值太多

反例：

```java
if (order.getStatus() == 3) {
    // ...
}
```

问题在于没人知道 `3` 是什么。

更好的方式：

```java
if (OrderStatus.PAID.equals(order.getStatus())) {
    // ...
}
```

魔法值的问题不只是可读性差，还容易改错。

### 6. 异常处理随意

常见问题：

- 直接 `catch (Exception e)`
- 打个日志就结束
- 返回 `null` 混过去
- 向上抛但不补业务语义

好代码会区分：

- 哪些异常是业务异常
- 哪些异常是系统异常
- 哪些异常应该吞
- 哪些异常必须让调用方知道

### 7. 过度设计

这类代码表面上很“高级”，实际上很难维护。

例如一个很简单的功能，硬是拆成：

- `AbstractFactory`
- `Strategy`
- `Context`
- `Facade`
- `Builder`

如果需求本身很简单，这种抽象只会把理解成本抬上去。

好代码不是模式越多越好，而是**复杂度和问题规模匹配**。

---

## 3. Java 好代码的常见表现

### 1. 命名准确

类名看职责，方法名看动作，变量名看业务含义。

好的命名例子：

- `createOrder`
- `cancelExpiredOrders`
- `findActiveUsers`
- `calculateFinalPrice`
- `sendPaymentSuccessNotification`

这些名字有个共同点：

- 能看出动作
- 能看出对象
- 能看出范围或条件

### 2. 分层清楚

在常见 Java 后端项目里，至少要尽量做到：

- Controller 负责接收请求和返回结果
- Service 负责业务逻辑
- Repository / Mapper 负责数据访问
- Domain / Entity 负责业务对象

坏代码通常会出现分层污染：

- Controller 里做复杂计算
- Service 里拼 SQL
- Repository 里做业务判断

### 3. 方法短而稳定

一个好方法通常满足：

- 输入清楚
- 输出清楚
- 副作用可控
- 逻辑聚焦

不一定非要机械地限制 10 行、20 行，但如果一个方法已经让人读不出主线，那就该动手整理。

### 4. 注释少但关键处有帮助

好代码不靠大量废话注释撑着。

比如这种注释没有价值：

```java
// 遍历用户列表
for (User user : users) {
}
```

但这些注释是有价值的：

- 为什么这里要特殊处理
- 为什么不用更直觉的方案
- 这里的业务边界是什么
- 外部系统有什么坑

注释不是翻译代码，而是补充代码表达不了的上下文。

### 5. 边界清楚

比如一个下单流程，要清楚这些边界：

- 空请求怎么处理
- 重复提交怎么处理
- 库存不足怎么处理
- 支付失败怎么处理
- 超时怎么处理

好代码会把这些边界想清楚，而不是只写“正常情况”。

---

## 4. 一段更像好代码的 Java 示例

下面这个例子不追求“高级”，重点是展示清楚、可改、可测。

```java
public class OrderService {

    private final InventoryService inventoryService;
    private final OrderRepository orderRepository;
    private final PaymentService paymentService;

    public OrderService(
            InventoryService inventoryService,
            OrderRepository orderRepository,
            PaymentService paymentService) {
        this.inventoryService = inventoryService;
        this.orderRepository = orderRepository;
        this.paymentService = paymentService;
    }

    public Long createOrder(CreateOrderCommand command) {
        validateCommand(command);

        checkInventory(command);

        Order order = buildOrder(command);
        orderRepository.save(order);

        paymentService.createPayment(order.getId(), order.getPayableAmount());

        return order.getId();
    }

    private void validateCommand(CreateOrderCommand command) {
        Objects.requireNonNull(command, "create order command must not be null");
        if (command.getUserId() == null) {
            throw new IllegalArgumentException("userId must not be null");
        }
        if (command.getItems() == null || command.getItems().isEmpty()) {
            throw new IllegalArgumentException("items must not be empty");
        }
    }

    private void checkInventory(CreateOrderCommand command) {
        boolean enough = inventoryService.hasEnoughStock(command.getItems());
        if (!enough) {
            throw new BusinessException("inventory not enough");
        }
    }

    private Order buildOrder(CreateOrderCommand command) {
        return Order.create(command.getUserId(), command.getItems());
    }
}
```

这段代码的优点不是“功能多强”，而是：

- 主流程一眼能看懂
- 校验、库存检查、建单各有边界
- 依赖关系清楚
- 比较容易测试

---

## 5. 团队里怎么判断一段 Java 代码写得好不好

最实用的方法不是争论“优雅不优雅”，而是看下面这些问题。

### 1. 另一个同事 10 分钟内能看懂主流程吗？

如果不能，说明可读性有问题。

### 2. 改一个需求时，会不会不敢动？

如果一改就怕炸，说明耦合太重。

### 3. 出线上问题时，定位路径清楚吗？

如果只能靠猜，说明边界、日志或异常设计不够好。

### 4. 这段逻辑能不能写测试？

如果很难写测试，通常意味着结构还不够清晰。

### 5. 新人接手会不会频繁误改？

如果容易误改，说明命名、边界或抽象做得不够稳。

---

## 6. 写 Java 好代码时最值得坚持的习惯

### 1. 写之前先想职责

先问自己：

- 这个类到底负责什么？
- 这个方法到底负责什么？
- 有没有把不该放进来的逻辑也塞进来了？

### 2. 先写清楚，再谈抽象

很多人太早抽象，结果把简单问题写复杂了。

更稳的顺序是：

1. 先把业务流程写清楚
2. 看重复是不是真的存在
3. 再决定要不要抽公共逻辑

### 3. 看到重复，再考虑复用

不是两行相似代码就必须抽方法。

如果抽完以后名字很虚、上下文更难懂，那这种复用就不划算。

### 4. 写完自己再读一遍

重点看这几个问题：

- 命名是否准确
- 主流程是否顺
- 分支是否太乱
- 异常是否明确
- 别人能不能不问你就看懂

### 5. 把异常和边界当成主流程的一部分

真正稳定的代码，不是只把 happy path 写顺，而是把失败路径也设计清楚。

---

## 7. 一份很实用的 Java 代码自检清单

提交前可以快速问自己：

- 类名和方法名是不是能直接表达业务意图？
- 有没有魔法值？
- 有没有一个方法做太多事？
- 有没有分层混乱？
- 空值、异常、边界条件处理清楚了吗？
- 关键日志够不够排查问题？
- 这段代码别人改起来会不会害怕？
- 能不能为核心逻辑补测试？
- 有没有为了“高级”而引入不必要抽象？

如果这里面有 3 条以上答不上来，这段代码通常还不够好。

---

## 8. 最后一句话

**Java 里的好代码，不是最炫的代码，而是最容易让团队长期稳定协作的代码。**

它通常具备这些特点：

- 清楚
- 稳定
- 易改
- 可测
- 一致
- 边界明确

真正厉害的工程师，不是把代码写得只有自己能看懂，而是把复杂问题写得让团队都能接得住。
