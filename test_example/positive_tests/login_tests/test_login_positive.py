"""登录/鉴权主题 · 正向用例。

被测对象：LoginService.login（原子操作）与 register_and_login（业务拼接）。
设计约定（见 test_example/README.md）：
- 正向用例只断言业务结果（token、message、模型字段），不直接断言 HTTP 状态码；
- 错误凭据返回 401 等反向场景归 reverse_tests/login_tests，不在此文件编写。
"""

from __future__ import annotations

import pytest

from config import settings
from core.client import Client
from service import CartService, LoginService, UserService, register_and_login


@pytest.mark.positive
def test_admin_login_returns_token(guest_client):
    """预置管理员登录成功：返回 "Bearer ..." 形式的 token 与成功 message。

    验证点：
    - token 非空且带 "Bearer " 前缀（core 的 set_token 会统一剥离该前缀存储）；
    - message 为 ServeRest 登录成功固定文案。
    """
    login = LoginService(guest_client).login(settings.admin_email, settings.admin_password)

    assert login.token is not None
    assert login.token.startswith("Bearer ")
    assert login.message == "Login realizado com sucesso"


@pytest.mark.positive
def test_register_and_login_builds_usable_identity(user_payload):
    """业务拼接 register_and_login：注册 → 登录一步完成，token 可正常使用。

    验证点：
    - 返回的 User 已回填服务端生成的 _id；
    - Login.token 形如 "Bearer ..."；
    - token 注入 client 后调用受保护接口不抛异常——无 token 访问时
      core 会贴 401 异常标签，能正常返回即证明身份建立成功。
    """
    client = Client()
    user_id: str | None = None
    try:
        user, login = register_and_login(client, user_payload)
        user_id = user.id
        client.set_token(login.token)

        assert user.id is not None
        assert login.token.startswith("Bearer ")

        # 购物车相关操作要求登录 token；cancel 对无购物车用户返回 200，
        # 用它验证身份可用，同时不产生业务副作用。
        cancel_result = CartService(client).cancel()
        assert cancel_result["message"]
    finally:
        # 清理：当前用户没有购物车，直接删除；随后关闭连接池。
        if user_id is not None:
            UserService(client).delete(user_id)
        client.close()
