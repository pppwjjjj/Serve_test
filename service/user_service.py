"""service/user_service.py —— 用户服务。

原子操作：/usuarios 的增删改查，每个方法对应一次 HTTP 请求。
"""

from __future__ import annotations

from models import ModelList, User
from service.base import BaseService


class UserService(BaseService):
    """用户服务：/usuarios 端点级原子操作。"""

    def create(self, user: User) -> User:
        """POST /usuarios：创建用户，回填服务端生成的 _id 后返回同一模型。"""
        response = self._client.post("/usuarios", json=self._body(user))
        user.id = response.json()["_id"]
        return user

    def get(self, user_id: str) -> User:
        """GET /usuarios/{id}：按主键查询单个用户。"""
        response = self._client.get(f"/usuarios/{user_id}")
        return User.from_dict(response.json())

    def list(self, **params) -> ModelList[User]:
        """GET /usuarios：查询用户列表，支持按字段名传 query 参数（如 nome、email）。"""
        response = self._client.get("/usuarios", params=params)
        return ModelList.from_dict(response.json(), "usuarios", User)

    def update(self, user_id: str, user: User) -> dict:
        """PUT /usuarios/{id}：整体更新用户，返回响应字典（message）。"""
        response = self._client.put(f"/usuarios/{user_id}", json=self._body(user))
        return response.json()

    def delete(self, user_id: str) -> dict:
        """DELETE /usuarios/{id}：删除用户，返回响应字典（message）。"""
        response = self._client.delete(f"/usuarios/{user_id}")
        return response.json()
