"""models/product.py —— 商品模型。

映射 ServeRest /produtos 接口响应中的商品字段（葡萄牙语 → 英语），
供 service 层进行商品相关的业务操作。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from models.base import BaseModel


@dataclass
class Product(BaseModel):
    """商品数据模型：一个对象对应一条商品记录。"""

    # 字段说明（API 字段名 → 属性名）：
    # _id        主键
    # nome       商品名称
    # preco      单价（ServeRest 要求为整数）
    # descricao  商品描述
    # quantidade 库存数量（整数）
    id: str | None = None
    name: str | None = None
    price: int | None = None
    description: str | None = None
    quantity: int | None = None

    # 字段映射表：from_dict() / to_dict() 的转换依据
    _FIELD_MAP: ClassVar[dict[str, str]] = {
        "_id": "id",
        "nome": "name",
        "preco": "price",
        "descricao": "description",
        "quantidade": "quantity",
    }
