"""models/user.py —— 用户模型。

映射 ServeRest /usuarios 接口响应中的用户字段（葡萄牙语 → 英语），
供 service 层进行用户相关的业务操作。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from models.base import BaseModel


@dataclass
class User(BaseModel):
    """用户数据模型：一个对象对应一条用户记录。"""

    # 字段说明（API 字段名 → 属性名）：
    # _id           主键
    # nome          姓名
    # email         邮箱
    # password      密码（ServeRest 的查询响应中也会返回该字段）
    # administrador 是否管理员，值为字符串 "true"/"false"，类型保持原样不转换
    id: str | None = None
    name: str | None = None
    email: str | None = None
    password: str | None = None
    administrator: str | None = None

    # 字段映射表：from_dict() / to_dict() 的转换依据
    _FIELD_MAP: ClassVar[dict[str, str]] = {
        "_id": "id",
        "nome": "name",
        "email": "email",
        "password": "password",
        "administrador": "administrator",
    }
