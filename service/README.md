当前层级：service
该层级是对serverest的所有业务操作的模拟。
该层级通过将serverest的业务操作原子化（即拆分所有业务操作为单次操作）从而全面覆盖所有业务。
再将原子化操作根据需求进行组合，得到一次完整的业务操作

service层通过core层向serverest发送http请求，service层有一个基类`BaseService`，它是所有原子操作的基类，不同的原子操作再根据业务扩展出不同的接口。

`BaseService`实例化时传入一个core层的`client`对象，通过它收发http请求，并且在models层的空字段/缺失字段赋予的`None`默认值在这里进行处理。
service对象统一在构造时注入一个core层 `Client`，这个对象由`fixture`管理生命周期，所以service层对象获取到的永远是一个就绪的`client`对象，此时token身份已经确定了，直接就拼接原子操作组成一次完整的业务操作。

`fixture`提供身份明确、生命周期受管的`client`；service层接收后通过返回值链拼接原子操作，组成完整业务流；`test_example`层只拿最终结果断言。

原子操作接收模型或参数，然后`BaseService._body()`构造请求体，调用client向外暴露的接口进行收发操作。

关于业务拼接：
    拼接的本质是"编排 + 返回值链"，是按顺序调用原子操作，将上一个原子操作的返回值作为下一个原子操作的参数传入，就是字面意义的拼接。
    `register_and_login`是身份建立类：它返回`Login`，但token注入（`set_token`）留在组合之外，交给fixture，业务拼接里永远不出现 `set_token`。而`buy_then_cancel`、`buy_then_complete`、`get_or_create_product`是单一身份业务链：client 进来时身份已确定，直接跑完整业务流。`cleanup_purchase_data`是清理链：按服务端依赖约束逆序回收（有购物车时删商品删用户会 400）

目前一共有5条业务逻辑：
 #      拼接函数                 内部原子操作链                                     返回
  ━━━━━  ━━━━━━━━━━━━━━━━━━━━━━━  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ━━━━━━━━━━━━━━━━━━
   1      register_and_login       创建用户 → 登录                                    (User, Login)
  ─────  ───────────────────────  ─────────────────────────────────────────────────  ──────────────────
   2      buy_then_cancel          创建购物车 → 按 id 查购物车 → 取消购物车             Cart（取消前的）
  ─────  ───────────────────────  ─────────────────────────────────────────────────  ──────────────────
   3      buy_then_complete        创建购物车 → 按 id 查购物车 → 完成购买               Cart
  ─────  ───────────────────────  ─────────────────────────────────────────────────  ──────────────────
   4      get_or_create_product    按名称查商品列表 →（命中则复用 / 未命中则创建）       Product
  ─────  ───────────────────────  ─────────────────────────────────────────────────  ──────────────────
   5      cleanup_purchase_data    取消购物车 → 逐个删商品 → 删用户                     None
  ─────  ───────────────────────  ─────────────────────────────────────────────────  ──────────────────

  没有设计业务拼接的都代表能通过调用原子操作实现，没有必要加入到业务拼接里。
  service层的设计就是原子性的业务操作和拼接后的一个操作过程，具体调用是在test_example层进行。

## 对外接口一览
service 层对外暴露五个类，统一由 `__init__.py` 导出：
- `BaseService`：公共底座，构造注入 `Client`，提供 `_body()` helper，不提供原子接口
- `LoginService`：`login(email, password)` → `Login`
- `UserService`：`create(user)` / `get(id)` / `list(**params)` / `update(id, user)` / `delete(id)`
- `ProductService`：与 UserService 同构，资源为 /produtos
- `CartService`：`create(items: list[CartItem])` / `list()` / `get(id)` / `cancel()` / `complete()`

方法签名、参数与返回的细节写在各服务源码的注释里，本层 README 不重复维护，
避免签名变更时两处维护。