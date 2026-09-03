# ServeRest API 自动化测试（规划）

基于 **Python + pytest + requests**，对本地 Docker 部署的 ServeRest（`paulogoncalvesbh/serverest:latest`）进行接口自动化测试。

当前阶段：**规划与工程配置**（env、docker-compose 已就绪），代码按层逐步实现。

## 一、分层架构（5 层）

| 层级 | 职责 | 设计约定 |
| --- | --- | --- |
| config | 读取 `.env`，集中管理环境配置 | 服务地址、超时、重试、预置管理员账号；不写业务逻辑 |

| core | 封装 requests | 基于 `requests.Session`（连接池由 urllib3 自动维护，不重复实现）；统一 base_url、超时、Bearer token 注入、日志、连接失败重试 |

| models | 把响应字段映射为对象 | dataclass 承载字段映射（`from_dict` / `to_dict`）；只做数据，不做业务操作 |

| service | 原子操作 + 业务串联 | 每个资源一个服务（login / user / product / cart），端点级方法原子化；再提供场景拼接（如 注册 → 登录 → 加购 → 取消） |

| test_example | 测试用例层 | 调用 service 并断言；公共 fixture（token、随机数据、清理）集中在 conftest.py |

### 关键设计决策

- **认证**：测试会话开始时用预置管理员登录一次拿 token，session 级复用；需要"无 token / 普通用户 token"的用例单独创建客户端，不污染共享客户端。
- **数据清理**：用例只创建自己需要的数据，测后按依赖顺序清理：先取消/完成购物车 → 再删产品 → 最后删用户。彻底重置数据：重建容器。
- **依赖管理**：requirements.txt 锁定核心依赖（pytest、requests、python-dotenv，后续加 allure-pytest）。
- **pytest 工程**：根目录 pytest.ini（testpaths、pythonpath），conftest.py 提供 fixture；VSCode 通过 `python.envFile` 加载 `.env`。

## 二、环境与配置（已就绪）

- `.env` / `.env.example`：环境变量实际配置与模板（服务地址、超时、重试、预置管理员账号）。
- `docker-compose.yml`：编排 serverest 容器。镜像自带 MongoDB 与预置数据，单服务即可。
- `.gitignore`：忽略 `.env`、虚拟环境、测试报告与缓存（保留 `.env.example`）。

快速启动：

- 启动服务：`docker compose up -d --wait`（需已安装 Docker Desktop / Docker Compose v2；`--wait` 会等服务健康后再返回）
- 运行测试：在项目根目录、且已执行 `pip install -r requirements.txt` 的环境下，运行 `pytest --alluredir=allure-results`，产出 Allure 原始报告数据
- 查看报告：`allure serve allure-results`（需另装 Allure CLI；未安装也可正常跑测试）

注意：若 3000 端口已被手动 `docker run` 的容器占用（如 `sad_kepler`），先执行 `docker stop <容器名>` 再启动 compose。

## 三、ServeRest 已验证行为（编写代码时参考）

- 预置管理员：`fulano@qa.com / teste`（administrador=true）；`POST /login` 返回 Bearer token。
- `/usuarios`：POST 201 返回 `{message, _id}`；重复 email 返回 400；GET 不存在的用户返回 400 "Usuário não encontrado"；DELETE 不存在的用户返回 200 "Nenhum registro excluído"。
- `/produtos`：必须管理员 token；无 token 返回 401，非管理员返回 403；`preco` 必须是整数。
- `/carrinhos`：POST 201 返回 `{message, _id}`；取消购物车是 `DELETE /carrinhos/cancelar-compra`（不是 `DELETE /carrinhos`）；完整购物车对象通过 `GET /carrinhos` 或 `GET /carrinhos/:id` 获取。
- 依赖约束：购物车未处理时不能删除其产品和用户，清理必须按依赖顺序。

## 四、实施路线（按层推进）

1. config：实现 `.env` 读取并验证取值。
2. core：封装 Session 客户端（token、超时、日志），先跑通登录联通性。
3. models：按 `/usuarios`、`/produtos`、`/carrinhos` 的响应结构定义字段映射。
4. service：先 login / user，再 product / cart，随后补场景拼接。
5. test_example：conftest 公共 fixture + 第一个登录用例跑通，再逐步扩充 CRUD、权限、购物车用例。
6. 工程收尾：requirements.txt、pytest.ini、VSCode 配置。

## 五、后续规划

- `git init` + 版本管理。
- 为test_example层引入正向测试和反向测试
- 引入 Allure 生成测试报告图表（allure-pytest + Allure CLI）。
- 引入 Jenkins 持续集成（准备依赖 → 启动 compose → 执行 pytest → 生成报告 → 清理环境）。
