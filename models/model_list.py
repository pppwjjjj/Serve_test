"""models/model_list.py —— 通用包裹模型。

映射 ServeRest 中"数量 + 资源数组"这类嵌套列表响应，
例如 GET /usuarios 返回的 {"quantidade": N, "usuarios": [...]}。
把嵌套结构的处理集中到 models 层，service 层无需关心映射细节。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

from models.base import BaseModel

# 泛型参数：元素必须是资源模型（User / Product / Cart）的子类
T = TypeVar("T", bound=BaseModel)


@dataclass
class ModelList(Generic[T]):
    """通用包裹模型：一个对象对应一个"数量 + 资源数组"的列表响应。"""

    # count：对应响应外层的 quantidade 字段，记录列表元素总数
    count: int | None = None
    # key：构造时记住本列表在响应字典中的字段名（如 "usuarios"），
    # 用于 to_dict() 时把列表还原回原来的字段位置，而不是回头查原始字典
    key: str | None = None
    # items：元素对象列表，由 from_dict() 逐条映射生成；字段缺失时保持 None
    items: list[T] | None = None

    @classmethod
    def from_dict(cls, data: dict, key: str, item_cls: type[T]) -> ModelList[T]:
        """从列表响应字典构造包裹模型。

        参数说明：
        - data：core 返回的整个响应字典（例如 GET /usuarios 的完整响应）；
        - key：本列表在响应字典中的字段名（例如 "usuarios"）；
        - item_cls：元素模型类（例如 User），用于逐条映射列表中的每条记录。
        """
        # 第 1 步：从响应外层读取数量字段 quantidade，字段缺失时默认 None。
        count = data.get("quantidade")
        # 第 2 步：按 key 取出原始元素列表，字段缺失时保持 None。
        raw_items = data.get(key)
        # 第 3 步：对列表逐条调用元素模型的 from_dict() 映射成对象列表；
        # raw_items 为 None 时不做转换、保持 None，None 的语义由 service 层处理。
        items = None if raw_items is None else [item_cls.from_dict(item) for item in raw_items]
        # 第 4 步：把 key 一并存入对象，保证 to_dict() 能还原出同样的包裹结构。
        return cls(count=count, key=key, items=items)

    def to_dict(self) -> dict:
        """把包裹模型反向转换成列表响应字典。

        注意：生成的是全新字典，key 只用于决定列表还原到哪个字段名，
        与构造时的原始字典之间没有任何引用关系。
        """
        # 防御性检查：key 只在 from_dict() 构造时写入；
        # 若为空说明对象不是按标准流程构造，无法还原字段位置，直接报错避免生成畸形字典。
        if self.key is None:
            raise ValueError("ModelList 缺少 key，无法还原列表字段位置，请通过 from_dict() 构造")
        # 第 1 步：把每个元素对象逐一转回字典，items 为 None 时原样保留。
        raw_items = None if self.items is None else [item.to_dict() for item in self.items]
        # 第 2 步：按记住的 key 组装包裹结构，把数量与列表放回对应的字段位置。
        return {"quantidade": self.count, self.key: raw_items}
