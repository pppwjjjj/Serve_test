"""service 层：原子操作 + 业务拼接。

职责：把 core 层暴露的 HTTP 接口封装为资源级原子操作，
每个资源一个服务（LoginService / UserService / ProductService / CartService），
构造时注入 core 层 Client；scenarios 提供按业务顺序拼接原子操作的组合函数。
"""

from service.base import BaseService
from service.cart_service import CartService
from service.login_service import LoginService
from service.product_service import ProductService
from service.scenarios import (
    buy_then_cancel,
    buy_then_complete,
    cleanup_purchase_data,
    get_or_create_product,
    register_and_login,
)
from service.user_service import UserService

__all__ = [
    "BaseService",
    "CartService",
    "LoginService",
    "ProductService",
    "UserService",
    "buy_then_cancel",
    "buy_then_complete",
    "cleanup_purchase_data",
    "get_or_create_product",
    "register_and_login",
]
