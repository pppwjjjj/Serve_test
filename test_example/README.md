当前层级：test_example

当前层级是测试用例层，通过调用service层的原子操作以及业务操作并加以断言来完成测试。
测试用例层分正向用例和反向用例。
正向用例将对每个接口进行正向测试，包括输入合法参数（必填参数和全部参数）、输入边界值参数，通过断言判断是否成功通过测试。
反向用例则是反转，意思是"做不该做的事"，输入非法参数如：使用已经注册过的邮箱进行注册、缺少参数、输入不合规范形式的参数等，通过断言core层里`_request`贴好的`exceptions`异常标签进行判断是否通过测试。
反向用例的断言也是对异常标签进行断言，是预期中的失败，例如返回400状态码对应的异常标签，断言时就assert异常标签。因为是预期的错误，所以结果是true，测试用例通过。
个别接口存在"成功但无操作"的特殊语义（如删除不存在的用户返回 200 "Nenhum registro excluído"），core不会为其贴异常标签；这类用例不属于异常标签用例，直接断言返回体message。

当前测试项目为：ServeRest
该项目为开源项目，主题是:登录/鉴权-用户-商品-购物车，测试用例设计将围绕这个主题展开。

关于token鉴权，管理员用户复用session；普通用户和游客(无token鉴权)区别于管理员用户单独建立客户端。
管理员用户公用一个`client`，普通用户有独立`client`，无token鉴权的游客也是独立`client`，身份之间互不串台；MongoDB 中的数据残留污染则由随机唯一数据与逆序清理来防止（见数据流）。
表现如下：
   - 管理员 client（session 级复用）：建商品、删商品，以及执行仅管理员可用的写操作。
   - 普通用户 client：每个用例独立注册一个普通用户（随机唯一 email），再用该身份建购物车、完成/取消购物车。
   - 游客 client（无 token）：只做无鉴权探测，不创建任何数据。

项目结构如下：
 test_example/
  ├── smoke_tests/                  # 连通性冒烟
  ├── positive_tests/               #正向
  │   ├── login_tests/
  │   ├── user_tests/
  │   ├── product_tests/
  │   └── cart_tests/
  └── reverse_tests/                # 反向
      ├── login_tests/
      ├── user_tests/
      ├── product_tests/
      └── cart_tests/


数据流：
调用链只有一条：test_example → service（原子操作/业务拼接）→ core `client` → ServeRest → MongoDB。测试用例只通过service层读写数据，不直连数据库、不绕过service发请求。
   - 环境基线：容器启动自带预置管理员 `fulano@qa.com` 与种子商品，它们是环境基线；预置管理员只用于建立身份与权限前提，用例不修改、不删除基线数据。
   - 数据自建：业务用例所需的用户、商品、购物车都由用例自己创建，字段用随机唯一值（email、nome、商品名等），保证用例重跑时不撞"重复"约束，也便于用例之间互不依赖。
   - 数据生命周期：setup 自建数据 → 执行被测操作并断言（断言的是 service 返回的模型/字典，不回读数据库）→ teardown 按依赖逆序回收，即使用例失败也要清理。
   - 依赖约束：用户有未处理购物车时服务端会拒绝删除（400），商品被购物车引用时也不能先删；因此清理顺序固定为"取消/完成购物车 → 删商品 → 删用户"，该顺序已由 service 层 `cleanup_purchase_data` 固化，用例不自行实现。
   - 幂等回收：`cancel()` 对无购物车用户返回 200，天然幂等，teardown可安全重复调用。
   - 彻底重置：历史残留数据无法靠用例清理时，重建容器即可回到干净的基线状态。


测试用例工作流：
用例内部的执行流程
  1. 建立身份：管理员登录一次（session级，fixture持有）；普通用户走`register_and_login`注册并登录后注入`client`；游客直接裸`client`。
  2. 造数据：按主题需要创建商品/购物车等前置数据。
  3. 执行被测操作：调用service的原子操作或业务拼接。
  4. 断言：成功场景断言业务结果（回填`id`、字段一致、购物车/库存状态变化）；失败场景断言core贴好的异常标签（如BadRequestError），不直接断言状态码。
  5. 清理：`teardown`中按数据流约定逆序回收，确保用例结束后数据库回到“只有基线数据”的状态。

运行流程：
  1. 先跑冒烟测试（test_example/smoke_tests），确认测试框架与 ServeRest 连通后再跑正式用例。
  2. 全量执行在项目根目录运行`pytest`（已由 pytest.ini 限定收集 test_example），也可以按目录单独运行某个主题的用例。
  3. 用例相互独立、无执行顺序依赖，建议串行执行；失败时先根据断言定位是环境、service拼接还是core标签映射的问题，不盲目重试。


正向与反向用例清单（与代码目录一一对应，运行 `pytest` 共 43 条：冒烟 2 / 正向 14 / 反向 27，其中"数量不合法"为 0 与 -1 参数化两条）：

正向用例（positive_tests）：
- login_tests/test_login_positive.py
  - test_admin_login_returns_token：预置管理员登录成功，返回 "Bearer ..." token 与成功文案
  - test_register_and_login_builds_usable_identity：注册 → 登录拼接一步完成，token 可用于受保护接口
- user_tests/test_user_positive.py
  - test_create_user_and_get_by_id：创建用户回填 _id，按 id 查询字段一致
  - test_list_users_filters_by_email：按 email 精确查询唯一命中
  - test_update_user_changes_fields：修改 nome 后按 id 查询可见新值
  - test_delete_user_removes_record：删除成功，按 email 查询不再命中
- product_tests/test_product_positive.py
  - test_create_product_and_get_by_id：创建商品回填 _id，按 id 查询字段一致
  - test_list_products_filters_by_name：按名称精确查询唯一命中
  - test_update_product_changes_fields：名称/价格/库存修改后可见新值
  - test_delete_product_removes_record：删除成功，按名称查询不再命中
  - test_get_or_create_product_reuses_existing：同名商品第二次调用直接复用，不重复创建
- cart_tests/test_cart_positive.py
  - test_create_cart_and_cancel_restores_stock：建购物车 → 按 id 查询 → 取消，库存恢复
  - test_buy_then_cancel_scenario_restores_stock：拼接加购 → 取消，库存恢复
  - test_buy_then_complete_scenario_deducts_stock：拼接加购 → 完成购买，库存扣减

反向用例（reverse_tests）：
- login_tests/test_login_reverse.py
  - test_login_with_wrong_password_raises_unauthorized：密码错误 → UnauthorizedError
  - test_login_with_nonexistent_email_raises_unauthorized：邮箱不存在 → UnauthorizedError
  - test_login_missing_password_raises_bad_request：缺少密码 → BadRequestError
- user_tests/test_user_reverse.py
  - test_register_with_duplicate_email_raises_bad_request：重复 email 注册 → BadRequestError
  - test_register_missing_administrator_raises_bad_request：缺少 administrador → BadRequestError
  - test_register_with_invalid_administrator_value_raises_bad_request：administrador 传非法值 → BadRequestError
  - test_get_nonexistent_user_raises_bad_request：查询不存在用户 → BadRequestError
  - test_delete_nonexistent_user_returns_noop_message：删除不存在用户 → 200 no-op，断言 message（特例）
  - test_delete_user_with_active_cart_raises_bad_request：有购物车时删用户 → BadRequestError（依赖约束）
- product_tests/test_product_reverse.py
  - test_create_product_without_token_raises_unauthorized：无 token 建商品 → UnauthorizedError
  - test_create_product_with_normal_user_raises_forbidden：普通用户建商品 → ForbiddenError
  - test_normal_user_cannot_update_or_delete_product：普通用户更新/删除商品 → ForbiddenError，商品不受影响
  - test_create_duplicate_product_name_raises_bad_request：重名商品 → BadRequestError
  - test_create_product_missing_required_field_raises_bad_request：缺少 descricao → BadRequestError
  - test_create_product_with_invalid_price_type_raises_bad_request：preco 非数字 → BadRequestError
  - test_get_nonexistent_product_raises_bad_request：查询不存在商品 → BadRequestError
  - test_delete_nonexistent_product_returns_noop_message：删除不存在商品 → 200 no-op，断言 message（特例）
  - test_delete_product_referenced_by_cart_raises_bad_request：商品被购物车引用时删除 → BadRequestError（依赖约束）
- cart_tests/test_cart_reverse.py
  - test_create_cart_without_token_raises_unauthorized：无 token 建购物车 → UnauthorizedError
  - test_create_cart_with_nonexistent_product_raises_bad_request：购物车引用不存在商品 → BadRequestError
  - test_create_cart_quantity_exceeds_stock_raises_bad_request：购买数量超库存 → BadRequestError
  - test_create_cart_with_invalid_quantity_raises_bad_request：数量为 0 / -1 → BadRequestError（参数化）
  - test_create_cart_with_empty_items_raises_bad_request：produtos 为空数组 → BadRequestError
  - test_create_second_cart_for_same_user_raises_bad_request：同用户第二个购物车 → BadRequestError（一人一车）
  - test_cancel_cart_without_cart_returns_noop_message：无购物车时取消 → 200 no-op，断言 message（特例）
  - test_complete_cart_without_cart_returns_noop_message：无购物车时完成 → 200 no-op，断言 message（特例）
