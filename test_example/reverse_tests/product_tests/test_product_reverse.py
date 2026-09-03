"""商品主题 · 反向用例。

被测对象：ProductService 原子操作。
设计约定：
- 断言 core 层贴好的异常标签，不直接断言 HTTP 状态码；
- 无 token 写商品 → 401（UnauthorizedError）；普通用户写商品 → 403（ForbiddenError）；
- 参数/存在性/依赖类失败 → 400（BadRequestError）；
- 删除"格式合法但不存在"的商品是 200 no-op 特例，断言返回体 message。
"""

from __future__ import annotations

import pytest

from models import CartItem, Product
from core.exceptions import BadRequestError, ForbiddenError, UnauthorizedError
from service import CartService, ProductService


@pytest.mark.reverse
def test_create_product_without_token_raises_unauthorized(guest_client, product_payload):
    """反向：无 token 创建商品 → 401（UnauthorizedError 标签）。"""
    product_service = ProductService(guest_client)

    with pytest.raises(UnauthorizedError):
        product_service.create(product_payload)


@pytest.mark.reverse
def test_create_product_with_normal_user_raises_forbidden(
    normal_user, product_payload
):
    """反向：普通用户创建商品 → 403（ForbiddenError 标签，管理员专属路由）。"""
    _, user_client = normal_user
    product_service = ProductService(user_client)

    with pytest.raises(ForbiddenError):
        product_service.create(product_payload)


@pytest.mark.reverse
def test_normal_user_cannot_update_or_delete_product(
    normal_user, admin_client, product_payload, product_cleanup, request
):
    """反向：普通用户对已有商品执行更新/删除 → 403，且商品不受影响。"""
    _, user_client = normal_user
    admin_product_service = ProductService(admin_client)
    user_product_service = ProductService(user_client)

    # 前置：管理员建商品并登记清理
    product = admin_product_service.create(product_payload)
    product_cleanup(request, admin_client, [product.id])

    update_payload = Product(
        name=f"{product.name}_hacked",
        price=1,
        description="hacked",
        quantity=1,
    )
    with pytest.raises(ForbiddenError):
        user_product_service.update(product.id, update_payload)
    with pytest.raises(ForbiddenError):
        user_product_service.delete(product.id)

    # 两次越权都应被拒绝，商品保持原样
    fetched = admin_product_service.get(product.id)
    assert fetched.name == product.name
    assert fetched.price == product.price


@pytest.mark.reverse
def test_create_duplicate_product_name_raises_bad_request(
    admin_client, product_payload, product_cleanup, request
):
    """反向：重复商品名创建 → 400（BadRequestError 标签）。"""
    product_service = ProductService(admin_client)
    first = product_service.create(product_payload)
    product_cleanup(request, admin_client, [first.id])

    duplicate = Product(
        name=first.name,
        price=first.price + 1,
        description="another description",
        quantity=first.quantity + 1,
    )
    with pytest.raises(BadRequestError):
        product_service.create(duplicate)


@pytest.mark.reverse
def test_create_product_missing_required_field_raises_bad_request(
    admin_client, product_payload
):
    """反向：缺少必填字段 descricao → 400（BadRequestError 标签）。"""
    product_service = ProductService(admin_client)
    missing = Product(
        name=product_payload.name,
        price=product_payload.price,
        description=None,  # None 在 _body() 中被丢弃，请求体缺 descricao
        quantity=product_payload.quantity,
    )

    with pytest.raises(BadRequestError):
        product_service.create(missing)


@pytest.mark.reverse
def test_create_product_with_invalid_price_type_raises_bad_request(
    admin_client, product_payload
):
    """反向：preco 传非数字 → 400（BadRequestError 标签，preco 必须是数字）。"""
    product_service = ProductService(admin_client)
    invalid = Product(
        name=product_payload.name,
        price="abc",  # 类型错误：服务端要求数字
        description=product_payload.description,
        quantity=product_payload.quantity,
    )

    with pytest.raises(BadRequestError):
        product_service.create(invalid)


@pytest.mark.reverse
def test_get_nonexistent_product_raises_bad_request(admin_client, nonexistent_id):
    """反向：查询不存在的商品 → 400（BadRequestError 标签）。"""
    product_service = ProductService(admin_client)

    with pytest.raises(BadRequestError):
        product_service.get(nonexistent_id)


@pytest.mark.reverse
def test_delete_nonexistent_product_returns_noop_message(
    admin_client, nonexistent_id
):
    """特殊语义：删除不存在的商品返回 200 + "Nenhum registro excluído"。

    与用户删除一致（前提是 id 格式合法）：这是"成功码但无操作"特例，
    断言返回体 message 而非异常标签。
    """
    product_service = ProductService(admin_client)

    result = product_service.delete(nonexistent_id)
    assert result["message"] == "Nenhum registro excluído"


@pytest.mark.reverse
def test_delete_product_referenced_by_cart_raises_bad_request(
    normal_user, admin_client, product_payload, product_cleanup, request
):
    """反向：商品被购物车引用时删除 → 400（依赖约束）。

    这正是数据流里"清理必须先取消/完成购物车"对商品一侧的服务端依据；
    失败删除后商品应仍存在，随后在用例内取消购物车再交给 teardown。
    """
    _, user_client = normal_user
    product_service = ProductService(admin_client)
    cart_service = CartService(user_client)

    product = product_service.create(product_payload)
    product_cleanup(request, admin_client, [product.id])
    cart_service.create([CartItem(product_id=product.id, quantity=1)])

    with pytest.raises(BadRequestError):
        product_service.delete(product.id)

    # 断言失败删除没有副作用：商品仍可按 id 查询
    assert product_service.get(product.id).id == product.id

    # 用例内先取消购物车，teardown 的商品清理才能成功
    cart_service.cancel()
