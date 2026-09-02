"""models/cart.py —— 购物车模型。

映射 ServeRest /carrinhos 接口响应中的购物车字段（葡萄牙语 → 英语），
供 service 层进行购物车相关的业务操作。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from models.base import BaseModel


@dataclass
class CartItem(BaseModel):
    """购物车商品条目：一个对象对应购物车内的一件商品。"""

    # 字段说明（API 字段名 → 属性名）：
    # idProduto     商品 ID
    # quantidade    该商品的购买数量（整数）
    # precoUnitario 商品单价（整数，仅响应返回；创建购物车的请求体不需要下发）
    product_id: str | None = None
    quantity: int | None = None
    unit_price: int | None = None

    # 字段映射表：from_dict() / to_dict() 的转换依据
    _FIELD_MAP: ClassVar[dict[str, str]] = {
        "idProduto": "product_id",
        "quantidade": "quantity",
        "precoUnitario": "unit_price",
    }


@dataclass
class Cart(BaseModel):
    """购物车数据模型：一个对象对应一条购物车记录。"""

    # 字段说明（API 字段名 → 属性名）：
    # _id              购物车主键
    # idUsuario        所属用户 ID
    # produtos         购物车内商品条目数组（CartItem 列表，嵌套结构）
    # precoTotal       购物车总价（整数）
    # quantidadeTotal  购物车内商品总数量（整数）
    id: str | None = None
    user_id: str | None = None
    products: list[CartItem] | None = None
    total_price: int | None = None
    total_quantity: int | None = None

    # 字段映射表：from_dict() / to_dict() 的转换依据
    _FIELD_MAP: ClassVar[dict[str, str]] = {
        "_id": "id",
        "idUsuario": "user_id",
        "produtos": "products",
        "precoTotal": "total_price",
        "quantidadeTotal": "total_quantity",
    }

    @classmethod
    def from_dict(cls, data: dict) -> Cart:
        """从响应字典构造购物车，并把 produtos 数组逐条映射成 CartItem 对象。"""
        cart = super().from_dict(data)
        if cart.products is not None:
            cart.products = [CartItem.from_dict(item) for item in cart.products]
        return cart

    def to_dict(self) -> dict:
        """反向转换成响应字典，produtos 由各 CartItem 递归重建。"""
        result = super().to_dict()
        if self.products is not None:
            result["produtos"] = [item.to_dict() for item in self.products]
        return result
