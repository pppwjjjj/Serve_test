"""商品主题 · 正向用例。

被测对象：ProductService 的 create / list / update / delete 原子操作，
以及业务拼接 get_or_create_product（按名查重，命中则复用）。
设计约定：
- 商品写操作仅管理员可执行，统一使用 admin_client（session 级复用）；
- 商品名随机唯一（ServeRest 对重名商品返回 400），用例可重复执行；
- 商品清理由 product_cleanup 统一登记，删除动作按"已删除则忽略"幂等收敛。
"""

from __future__ import annotations

import pytest

from models import Product
from service import ProductService, get_or_create_product


@pytest.mark.positive
def test_create_product_and_get_by_id(
    admin_client, product_payload, product_cleanup, request
):
    """创建商品成功：_id 回填，按 id 查询字段一致。

    商品模型四个字段全部下发（nome/preco/descricao/quantidade），
    属于"全量合法参数"的正向路径。
    """
    product_service = ProductService(admin_client)
    product = product_service.create(product_payload)

    # 创建成功后登记清理（即使断言失败也会在 teardown 删除）
    product_cleanup(request, admin_client, [product.id])

    assert product.id is not None

    fetched = product_service.get(product.id)
    assert fetched.id == product.id
    assert fetched.name == product_payload.name
    assert fetched.price == product_payload.price
    assert fetched.description == product_payload.description
    assert fetched.quantity == product_payload.quantity


@pytest.mark.positive
def test_list_products_filters_by_name(
    admin_client, product_payload, product_cleanup, request
):
    """按名称精确查询商品列表：唯一命中自建商品。"""
    product_service = ProductService(admin_client)
    product = product_service.create(product_payload)
    product_cleanup(request, admin_client, [product.id])

    result = product_service.list(nome=product.name)

    assert result.count == 1
    assert result.items is not None
    assert result.items[0].id == product.id
    assert result.items[0].price == product.price


@pytest.mark.positive
def test_update_product_changes_fields(
    admin_client, product_payload, product_cleanup, request
):
    """更新商品成功：名称/价格/库存修改后，按 id 查询可见新值。"""
    product_service = ProductService(admin_client)
    product = product_service.create(product_payload)
    product_cleanup(request, admin_client, [product.id])

    update_payload = Product(
        name=f"{product.name}_updated",
        price=product.price + 50,
        description=product.description,
        quantity=product.quantity + 5,
    )
    result = product_service.update(product.id, update_payload)

    assert result["message"] == "Registro alterado com sucesso"

    fetched = product_service.get(product.id)
    assert fetched.name == update_payload.name
    assert fetched.price == update_payload.price
    assert fetched.quantity == update_payload.quantity


@pytest.mark.positive
def test_delete_product_removes_record(
    admin_client, product_payload, product_cleanup, request
):
    """删除商品成功：返回成功 message，按名称查询不再命中。

    注意：删除"格式合法但不存在"的商品与删除不存在用户一致，返回 200 no-op，
    因此 teardown 可安全重复删除；product_cleanup 的 400 兜底仅防非常规 id。
    """
    product_service = ProductService(admin_client)
    product = product_service.create(product_payload)
    product_cleanup(request, admin_client, [product.id])

    result = product_service.delete(product.id)
    assert result["message"] == "Registro excluído com sucesso"

    # 用原名称精确查询，验证记录确实已被删除
    after = product_service.list(nome=product.name)
    assert after.count == 0
    assert after.items == []


@pytest.mark.positive
def test_get_or_create_product_reuses_existing(
    admin_client, product_payload, product_cleanup, request
):
    """业务拼接 get_or_create_product：同名商品第二次调用直接复用，不重复创建。

    这是给"用例只需要一个商品"场景设计的幂等入口，正向验证它的查重语义：
    第二次传入同名商品，返回的 _id 与第一次相同，且列表里仍只有一条记录。
    """
    product_service = ProductService(admin_client)

    first = get_or_create_product(admin_client, product_payload)
    product_cleanup(request, admin_client, [first.id])

    # 构造同名的"新"商品对象，再次调用拼接函数
    second_payload = Product(
        name=first.name,
        price=first.price,
        description=first.description,
        quantity=first.quantity,
    )
    second = get_or_create_product(admin_client, second_payload)

    assert second.id == first.id

    listed = product_service.list(nome=first.name)
    assert listed.count == 1
