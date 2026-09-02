"""service/scenarios.py —— 业务拼接（场景组合）。

把原子操作按业务顺序组合成一次完整的业务操作。

组合函数只接收"身份已就绪"的 client，内部实例化资源服务，靠返回值链串联：
- 身份建立类（register_and_login）：返回 Login，token 注入由 fixture 完成；
- 单一身份业务链（buy_then_cancel / buy_then_complete / get_or_create_product）：
  在已就绪的 client 上直接执行完整业务流；
- 清理链（cleanup_purchase_data）：按依赖顺序回收测试数据。

组合函数不负责 token 注入与 client 生命周期（那是 test 层 fixture 的职责），
也不捕获异常——任何一个原子步骤失败即整体失败，异常标签原样上抛。
"""

from __future__ import annotations

from core.client import Client
from models import Cart, CartItem, Login, Product, User
from service.cart_service import CartService
from service.login_service import LoginService
from service.product_service import ProductService
from service.user_service import UserService


def register_and_login(client: Client, user: User) -> tuple[User, Login]:
    """注册 → 登录：返回带 _id 的用户与登录响应。

    token 的注入（client.set_token）由调用方 fixture 完成，
    本函数只负责业务本身，不碰 client 的身份状态。
    """
    if not user.email or not user.password:
        raise ValueError("register_and_login 需要完整的 user：email 与 password 不能为空")
    user = UserService(client).create(user)
    login = LoginService(client).login(user.email, user.password)
    return user, login


def buy_then_cancel(client: Client, items: list[CartItem]) -> Cart:
    """加购 → 取消购物车：返回取消前创建的购物车（取消后库存已恢复）。"""
    cart_service = CartService(client)
    cart_id = cart_service.create(items)["_id"]
    cart = cart_service.get(cart_id)
    cart_service.cancel()
    return cart


def buy_then_complete(client: Client, items: list[CartItem]) -> Cart:
    """加购 → 完成购买：返回完成前创建的购物车（完成即结账，购物车被删除）。"""
    cart_service = CartService(client)
    cart_id = cart_service.create(items)["_id"]
    cart = cart_service.get(cart_id)
    cart_service.complete()
    return cart


def get_or_create_product(client: Client, product: Product) -> Product:
    """按名称查重建品：已存在则复用其 _id，不存在则创建，返回带 _id 的商品。

    用于用例需要"一个商品"但不在乎是否新造的幂等场景。
    """
    found = ProductService(client).list(nome=product.name)
    if found.items:
        product.id = found.items[0].id
        return product
    return ProductService(client).create(product)


def cleanup_purchase_data(
    user_client: Client,
    admin_client: Client,
    user: User,
    product_ids: list[str],
) -> None:
    """按依赖顺序清理测试数据：取消购物车 → 删除商品 → 删除用户。

    - cancel() 对无购物车用户返回 200，天然幂等，可重复执行；
    - 商品必须先于用户删除，用户有未处理购物车时服务端会拒绝删除（400）。
    """
    CartService(user_client).cancel()
    product_service = ProductService(admin_client)
    for product_id in product_ids:
        product_service.delete(product_id)
    UserService(user_client).delete(user.id)
