"""用户主题 · 反向用例。

被测对象：UserService 原子操作。
设计约定：
- 断言 core 层贴好的异常标签，不直接断言 HTTP 状态码；
- "成功码但无操作"的特殊语义（如删除不存在的用户返回 200）不属于异常标签用例，
  直接断言返回体 message；
- 反向用例不做数据穷举，只覆盖文档化的关键失败语义。
"""

from __future__ import annotations

import pytest

from models import CartItem, User
from service import CartService, ProductService, UserService
from core.exceptions import BadRequestError


@pytest.mark.reverse
def test_register_with_duplicate_email_raises_bad_request(
    guest_client, user_payload, request
):
    """反向：重复 email 注册 → 400（BadRequestError 标签）。

    先注册成功并登记清理，再以同一 email 注册，服务端拒绝重复邮箱。
    """
    user_service = UserService(guest_client)
    first = user_service.create(user_payload)
    request.addfinalizer(lambda: user_service.delete(first.id))

    duplicate = User(
        name="Duplicate User",
        email=first.email,
        password="Another123",
        administrator="false",
    )
    with pytest.raises(BadRequestError):
        user_service.create(duplicate)


@pytest.mark.reverse
def test_register_missing_administrator_raises_bad_request(guest_client, user_payload):
    """反向：缺少必填字段 administrador → 400（BadRequestError 标签）。"""
    user_service = UserService(guest_client)
    missing = User(
        name=user_payload.name,
        email=user_payload.email,
        password=user_payload.password,
        administrator=None,  # models 约定：None 字段在 _body() 中被丢弃，不再下发
    )

    with pytest.raises(BadRequestError):
        user_service.create(missing)


@pytest.mark.reverse
def test_register_with_invalid_administrator_value_raises_bad_request(
    guest_client, user_payload
):
    """反向：administrador 传非法值（非 "true"/"false"）→ 400（BadRequestError 标签）。"""
    user_service = UserService(guest_client)
    invalid = User(
        name=user_payload.name,
        email=user_payload.email,
        password=user_payload.password,
        administrator="maybe",  # 服务端只接受字符串 "true" / "false"
    )

    with pytest.raises(BadRequestError):
        user_service.create(invalid)


@pytest.mark.reverse
def test_get_nonexistent_user_raises_bad_request(guest_client, nonexistent_id):
    """反向：查询不存在的用户 → 400（BadRequestError 标签）。"""
    user_service = UserService(guest_client)

    with pytest.raises(BadRequestError):
        user_service.get(nonexistent_id)


@pytest.mark.reverse
def test_delete_nonexistent_user_returns_noop_message(guest_client, nonexistent_id):
    """特殊语义：删除不存在的用户返回 200 + "Nenhum registro excluído"。

    这是 README 记录的"成功码但无操作"特例：core 不为 200 贴异常标签，
    因此断言返回体 message，而不是异常标签。
    """
    user_service = UserService(guest_client)

    result = user_service.delete(nonexistent_id)
    assert result["message"] == "Nenhum registro excluído"


@pytest.mark.reverse
def test_delete_user_with_active_cart_raises_bad_request(
    normal_user, admin_client, product_payload, product_cleanup, request
):
    """反向：用户存在未处理购物车时删除用户 → 400（依赖约束）。

    这正是数据流里"清理必须先取消/完成购物车"的服务端依据；
    失败删除后购物车与用户都应保持原样，随后在用例内取消购物车再交给 teardown。
    """
    user, user_client = normal_user
    user_service = UserService(user_client)
    cart_service = CartService(user_client)
    product_service = ProductService(admin_client)

    # 前置：管理员建商品，普通用户加购 1 件
    product = product_service.create(product_payload)
    product_cleanup(request, admin_client, [product.id])
    cart_service.create([CartItem(product_id=product.id, quantity=1)])

    with pytest.raises(BadRequestError):
        user_service.delete(user.id)

    # 断言失败删除没有副作用：用户仍存在（按 email 仍可查到）
    assert user_service.list(email=user.email).count == 1

    # 用例内先取消购物车，teardown 的商品/用户清理才能按依赖顺序成功
    cart_service.cancel()
