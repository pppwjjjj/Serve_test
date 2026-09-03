"""购物车主题 · 正向用例。

被测对象：CartService 原子操作（create / get / cancel / complete）与
业务拼接 buy_then_cancel / buy_then_complete。

购物车依赖"真实用户 + 真实商品"，因此每个用例：
- 用 normal_user fixture 建立普通用户身份；
- 用管理员创建唯一商品并登记清理；
- 在用例内完成对购物车的处置（取消/完成），teardown 时商品已不再被引用，
  商品清理与用户清理的顺序因此不再互相制约。
"""

from __future__ import annotations

import pytest

from models import CartItem
from service import CartService, ProductService, buy_then_cancel, buy_then_complete


@pytest.mark.positive
def test_create_cart_and_cancel_restores_stock(
    normal_user, admin_client, product_payload, product_cleanup, request
):
    """原子操作链路：创建购物车 → 按 id 查询 → 取消，库存恢复原值。

    断言购物车落库后的业务结果：
    - 归属用户、条目数量与单价、总数量、总价都由服务端计算返回；
    - 取消购物车后商品库存回到创建前数量。
    """
    user, user_client = normal_user
    cart_service = CartService(user_client)
    product_service = ProductService(admin_client)

    # 前置数据：管理员建商品（库存 10），登记 teardown 删除
    product = product_service.create(product_payload)
    product_cleanup(request, admin_client, [product.id])

    # 1. 创建购物车：购买 2 件
    created = cart_service.create([CartItem(product_id=product.id, quantity=2)])
    assert created["message"] == "Cadastro realizado com sucesso"
    cart_id = created["_id"]
    assert cart_id

    # 2. 按 id 查询：核对购物车内容与合计
    cart = cart_service.get(cart_id)
    assert cart.user_id == user.id
    assert cart.total_quantity == 2
    assert cart.total_price == 2 * product.price
    assert cart.products is not None
    assert cart.products[0].product_id == product.id
    assert cart.products[0].quantity == 2

    # 3. 取消购物车：库存恢复
    cancel_result = cart_service.cancel()
    assert (
        cancel_result["message"]
        == "Registro excluído com sucesso. Estoque dos produtos reabastecido"
    )

    assert product_service.get(product.id).quantity == product.quantity


@pytest.mark.positive
def test_buy_then_cancel_scenario_restores_stock(
    normal_user, admin_client, product_payload, product_cleanup, request
):
    """业务拼接 buy_then_cancel：加购 → 取消一步完成，库存恢复。"""
    user, user_client = normal_user
    product_service = ProductService(admin_client)

    product = product_service.create(product_payload)
    product_cleanup(request, admin_client, [product.id])

    cart = buy_then_cancel(user_client, [CartItem(product_id=product.id, quantity=2)])

    # 返回的是"取消前"创建的购物车，校验其业务结果
    assert cart.id is not None
    assert cart.user_id == user.id
    assert cart.total_quantity == 2
    assert cart.total_price == 2 * product.price

    # 取消购物车应恢复商品库存
    assert product_service.get(product.id).quantity == product.quantity


@pytest.mark.positive
def test_buy_then_complete_scenario_deducts_stock(
    normal_user, admin_client, product_payload, product_cleanup, request
):
    """业务拼接 buy_then_complete：加购 → 完成购买，库存扣减。"""
    user, user_client = normal_user
    product_service = ProductService(admin_client)

    product = product_service.create(product_payload)
    product_cleanup(request, admin_client, [product.id])

    cart = buy_then_complete(user_client, [CartItem(product_id=product.id, quantity=2)])

    # 返回的是"完成前"创建的购物车，校验其业务结果
    assert cart.id is not None
    assert cart.user_id == user.id
    assert cart.total_quantity == 2
    assert cart.total_price == 2 * product.price

    # 完成购买是真实扣减库存：初始库存 10，购买 2 件后剩 8
    assert product_service.get(product.id).quantity == product.quantity - 2
