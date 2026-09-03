"""购物车主题 · 反向用例。

被测对象：CartService 原子操作。
设计约定：
- 断言 core 层贴好的异常标签，不直接断言 HTTP 状态码；
- 无 token 创建购物车 → 401（UnauthorizedError）；
- 商品不存在 / 库存不足 / 数量不合法 / 空条目 / 重复购物车 → 400（BadRequestError）；
- 取消/完成"不存在的购物车"是 200 no-op 特例，断言返回体 message。
"""

from __future__ import annotations

import pytest

from models import CartItem
from core.exceptions import BadRequestError, UnauthorizedError
from service import CartService, ProductService


@pytest.mark.reverse
def test_create_cart_without_token_raises_unauthorized(guest_client):
    """反向：无 token 创建购物车 → 401（UnauthorizedError 标签）。"""
    cart_service = CartService(guest_client)

    with pytest.raises(UnauthorizedError):
        cart_service.create([CartItem(product_id="x" * 16, quantity=1)])


@pytest.mark.reverse
def test_create_cart_with_nonexistent_product_raises_bad_request(
    normal_user, nonexistent_id
):
    """反向：购物车引用不存在的商品 → 400（BadRequestError 标签）。"""
    _, user_client = normal_user
    cart_service = CartService(user_client)

    with pytest.raises(BadRequestError):
        cart_service.create([CartItem(product_id=nonexistent_id, quantity=1)])


@pytest.mark.reverse
def test_create_cart_quantity_exceeds_stock_raises_bad_request(
    normal_user, admin_client, product_payload, product_cleanup, request
):
    """反向：购买数量超过库存 → 400（BadRequestError 标签）。"""
    _, user_client = normal_user
    cart_service = CartService(user_client)
    product_service = ProductService(admin_client)

    product = product_service.create(product_payload)
    product_cleanup(request, admin_client, [product.id])

    # 商品初始库存 10，一次买 11 件即超库存
    with pytest.raises(BadRequestError):
        cart_service.create([CartItem(product_id=product.id, quantity=product.quantity + 1)])


@pytest.mark.reverse
@pytest.mark.parametrize("quantity", [0, -1])
def test_create_cart_with_invalid_quantity_raises_bad_request(
    normal_user, admin_client, product_payload, product_cleanup, request, quantity
):
    """反向：购买数量为 0 或负数 → 400（BadRequestError 标签）。"""
    _, user_client = normal_user
    cart_service = CartService(user_client)
    product_service = ProductService(admin_client)

    product = product_service.create(product_payload)
    product_cleanup(request, admin_client, [product.id])

    with pytest.raises(BadRequestError):
        cart_service.create([CartItem(product_id=product.id, quantity=quantity)])


@pytest.mark.reverse
def test_create_cart_with_empty_items_raises_bad_request(normal_user):
    """反向：produtos 为空数组 → 400（BadRequestError 标签，购物车至少 1 个条目）。"""
    _, user_client = normal_user
    cart_service = CartService(user_client)

    with pytest.raises(BadRequestError):
        cart_service.create([])


@pytest.mark.reverse
def test_create_second_cart_for_same_user_raises_bad_request(
    normal_user, admin_client, product_payload, product_cleanup, request
):
    """反向：同一用户已有购物车时再次创建 → 400（一人最多一个购物车）。"""
    _, user_client = normal_user
    cart_service = CartService(user_client)
    product_service = ProductService(admin_client)

    product = product_service.create(product_payload)
    product_cleanup(request, admin_client, [product.id])
    cart_service.create([CartItem(product_id=product.id, quantity=1)])

    with pytest.raises(BadRequestError):
        cart_service.create([CartItem(product_id=product.id, quantity=1)])

    # 用例内取消购物车，保证 teardown 清理顺序正确
    cart_service.cancel()


@pytest.mark.reverse
def test_cancel_cart_without_cart_returns_noop_message(normal_user):
    """特殊语义：无购物车时取消 → 200 + no-op 文案。

    与 README 的"成功码但无操作"特例一致：断言返回体 message，
    不适用异常标签断言。
    """
    _, user_client = normal_user
    cart_service = CartService(user_client)

    result = cart_service.cancel()
    assert result["message"] == "Não foi encontrado carrinho para esse usuário"


@pytest.mark.reverse
def test_complete_cart_without_cart_returns_noop_message(normal_user):
    """特殊语义：无购物车时完成购买 → 200 + no-op 文案。"""
    _, user_client = normal_user
    cart_service = CartService(user_client)

    result = cart_service.complete()
    assert result["message"] == "Não foi encontrado carrinho para esse usuário"
