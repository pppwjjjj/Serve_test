"""service/login_service.py —— 登录服务。

原子操作：POST /login，换取登录响应（含 Bearer token）。
"""

from __future__ import annotations

from models import Login
from service.base import BaseService


class LoginService(BaseService):
    """登录服务：一个方法对应一次 POST /login 原子操作。"""

    def login(self, email: str, password: str) -> Login:
        """用邮箱 + 密码换取登录响应。

        返回的 Login.token 保留响应里的原始值（形如 "Bearer eyJ..."），
        注入客户端时由调用方执行 client.set_token(login.token)，本方法不做注入，
        这样"无 token"场景依然可以复用本服务。
        """
        response = self._client.post("/login", json={"email": email, "password": password})
        return Login.from_dict(response.json())
