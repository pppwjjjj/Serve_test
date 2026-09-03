"""test_example/conftest.py —— 测试用例层公共 fixture。

职责（对应 test_example/README.md 的身份与数据流约定）：
- 身份体系：管理员 session 级复用；普通用户每个用例独立注册；游客为不注入 token 的裸 client；
- 数据模板：随机唯一字段，保证用例重跑不撞"重复 email / 重名商品"约束；
- 清理辅助：商品删除登记为 teardown，删除操作按"已删除则忽略"幂等收敛。

本文件只提供用例的前置条件，不写业务用例。
"""

from __future__ import annotations

import uuid

import pytest

from config import settings
from core.client import Client
from core.exceptions import BadRequestError, UnauthorizedError
from models import Product, User
from service import CartService, LoginService, ProductService, UserService, register_and_login


def _unique_suffix() -> str:
    """生成短随机串，拼在 email / 商品名里保证全局唯一。"""
    return uuid.uuid4().hex[:12]


@pytest.fixture(scope="session")
def admin_client() -> Client:
    """管理员 client（session 级，只登录一次）。

    ServeRest 镜像自带预置管理员 fulano@qa.com，属于环境基线数据：
    本 fixture 只负责登录拿 token，不创建、不删除该管理员。
    管理员 token 在整个测试会话内复用，用于商品等仅管理员可写的操作。
    """
    client = Client()
    login = LoginService(client).login(settings.admin_email, settings.admin_password)
    client.set_token(login.token)
    yield client
    client.close()


@pytest.fixture
def guest_client() -> Client:
    """游客 client：不注入任何 token，用于"无鉴权"场景。

    游客只做只读或注册类操作，不创建任何业务数据。
    """
    client = Client()
    yield client
    client.close()


@pytest.fixture
def user_payload() -> User:
    """普通用户数据模板：email 随机唯一，administrator 固定为 "false"。

    每个用例拿到独立实例，字段可按需覆盖后再交给 service 创建。
    """
    suffix = _unique_suffix()
    return User(
        name=f"QA_User_{suffix}",
        email=f"qa_{suffix}@example.com",
        password="Qa123456",
        administrator="false",
    )


@pytest.fixture
def normal_user(user_payload) -> tuple[User, Client]:
    """普通用户（已登录）：返回 (user, client)。

    - 通过业务拼接 register_and_login 一步完成注册 + 登录；
    - client 注入该用户的 token，后续以普通用户身份操作；
    - teardown 先 cancel 购物车（无车时返回 200，幂等）再删除用户，
      保证用例结束后数据库只保留基线数据。
    """
    client = Client()
    user, login = register_and_login(client, user_payload)
    client.set_token(login.token)
    yield user, client

    # 收尾清理：先处理购物车（幂等），再删用户，最后关闭连接池。
    # 若用例内已删除该用户（如删除用户用例），原 token 会失效并返回 401，
    # 此时该用户不可能还有购物车，把 401 视为"无需再清理"即可。
    try:
        CartService(client).cancel()
    except UnauthorizedError:
        pass
    UserService(client).delete(user.id)
    client.close()


@pytest.fixture
def product_payload() -> Product:
    """商品数据模板：名称随机唯一（ServeRest 对重名商品返回 400），字段完整。"""
    suffix = _unique_suffix()
    return Product(
        name=f"QA_Product_{suffix}",
        price=100,
        description="由 pytest 正向用例创建的商品，用例结束后自动清理",
        quantity=10,
    )


@pytest.fixture
def product_cleanup():
    """商品清理注册器：把"删除商品"登记为该用例的 teardown。

    用法：product_cleanup(request, admin_client, [product.id])

    设计说明：
    - 商品删除必须由管理员执行，因此这里要求传入 admin_client；
    - 购物车用例都保证在用例内取消/完成购物车，teardown 时商品已不被引用；
    - 删除"格式合法但不存在"的商品与用户删除一致，返回 200 no-op，
      重复删除天然幂等；catch 400 只是对非常规 id 的兜底，保证 teardown 幂等。
    """

    def _register(request, admin_client: Client, product_ids: list[str]) -> None:
        product_service = ProductService(admin_client)

        def _cleanup() -> None:
            for product_id in product_ids:
                try:
                    product_service.delete(product_id)
                except BadRequestError:
                    # 商品已不存在：删除操作幂等收敛，视为清理完成
                    pass

        request.addfinalizer(_cleanup)

    return _register


@pytest.fixture
def nonexistent_id() -> str:
    """格式合法但绝不存在的 16 位资源 id。

    ServeRest 的 _id 要求 16 位字母数字；传 UUID 等非法格式会先触发
    "id 格式错误"的 400，测不到真正的"资源不存在"语义，因此反向用例
    统一使用本 fixture 提供的假 id。
    """
    return uuid.uuid4().hex[:16]
