"""models/cart.py —— 购物车模型。

映射 ServeRest /carrinhos 接口响应中的购物车字段（葡萄牙语 → 英语），
供 service 层进行购物车相关的业务操作。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from models.base import BaseModel


@dataclass
class Cart(BaseModel):
    """购物车数据模型：一个对象对应一条购物车记录。"""

    # 字段说明（API 字段名 → 属性名）：
    # _id          购物车主键
    # idUsuario    所属用户 ID
    # idProduto    购物车内商品 ID 数组（嵌套的字符串列表，类型原样保留）
    # quantidade   购物车内商品总数量（整数）
    # precoTotal   购物车总价（整数）
    id: str | None = None
    user_id: str | None = None
    product_ids: list[str] | None = None
    quantity: int | None = None
    total_price: int | None = None

    # 字段映射表：from_dict() / to_dict() 的转换依据
    _FIELD_MAP: ClassVar[dict[str, str]] = {
        "_id": "id",
        "idUsuario": "user_id",
        "idProduto": "product_ids",
        "quantidade": "quantity",
        "precoTotal": "total_price",
    }
