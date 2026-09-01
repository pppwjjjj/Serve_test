"""models/base.py —— 资源模型基类。

所有资源模型（User / Product / Cart）都继承本类，
统一对外暴露两个转换接口：
- from_dict()：JSON 字典 → 模型对象
- to_dict()：模型对象 → JSON 字典
"""

from __future__ import annotations

from typing import ClassVar, TypeVar

# 泛型变量：用于标注 from_dict() 的返回类型为"当前子类自身的实例"
T = TypeVar("T", bound="BaseModel")


class BaseModel:
    """资源模型基类：承载统一的字段映射表与双向转换逻辑。"""

    # 字段映射表（子类必须覆盖）：JSON 字典中的 API 字段名 → 模型属性名。
    # from_dict() 与 to_dict() 都以这张表为唯一转换依据，保证两个方向一一对应。
    _FIELD_MAP: ClassVar[dict[str, str]] = {}

    @classmethod
    def from_dict(cls: type[T], data: dict) -> T:
        """把 core 层返回的 JSON 字典映射成模型对象。

        转换约定：
        - 只取映射表中声明过的字段，字典中多余的字段一律忽略（前向兼容）；
        - 字段缺失或为空时统一给默认值 None，None 的后续语义由 service 层处理。
        """
        # 第 1 步：遍历映射表，从 JSON 字典中取出每个 API 字段的值。
        # data.get() 在字段缺失时返回 None，正好满足"空字段默认 None"的约定。
        values = {attr: data.get(api_field) for api_field, attr in cls._FIELD_MAP.items()}
        # 第 2 步：以属性名为关键字参数调用构造器，实例化模型对象。
        return cls(**values)

    def to_dict(self) -> dict:
        """把模型对象反向转换成 JSON 字典。

        转换约定：
        - 以映射表的反方向（属性名 → API 字段名）重建字典，结构与原字典一致；
        - 属性值为 None 时原样保留，不在本层过滤，由 service 层按需处理；
        - 生成的是全新字典，与构造时的原始字典没有任何引用关系。
        """
        # 第 1 步：遍历映射表，用 getattr() 读取每个属性当前的值（可能已被 service 修改）。
        # 第 2 步：以 API 字段名为键组装新字典，还原成与原字典相同格式的结构。
        return {api_field: getattr(self, attr) for api_field, attr in self._FIELD_MAP.items()}
