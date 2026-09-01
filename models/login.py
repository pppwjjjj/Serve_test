"""models/login.py —— 登录模型。

映射 ServeRest POST /login 接口的响应字段（葡萄牙语 → 英语），
供 service 层在登录成功后取出令牌，再注入 core 层的 Client。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from models.base import BaseModel


@dataclass
class Login(BaseModel):
    """登录响应数据模型：一个对象对应一次 POST /login 的响应。"""

    # 字段说明（API 字段名 → 属性名）：
    # message       登录结果消息（成功时类似 "Login realizado com sucesso"）
    # authorization 登录成功后返回的令牌，形如 "Bearer eyJ..."，
    #               类型保持原样；"Bearer " 前缀由 core 层 set_token() 统一剥离
    message: str | None = None
    token: str | None = None

    # 字段映射表：from_dict() / to_dict() 的转换依据
    _FIELD_MAP: ClassVar[dict[str, str]] = {
        "message": "message",
        "authorization": "token",
    }
