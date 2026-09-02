"""service/cart_service.py —— 购物车服务。

原子操作：/carrinhos 的创建、查询与两种完结方式，每个方法对应一次 HTTP 请求。
"""

from __future__ import annotations

from models import Cart, CartItem, ModelList
from service.base import BaseService


class CartService(BaseService):
    """购物车服务：/carrinhos 端点级原子操作。"""

    def create(self, items: list[CartItem]) -> dict:
        """POST /carrinhos：创建购物车，返回响应字典（message + _id）。

        请求体结构是 {"produtos": [{"idProduto", "quantidade"}]}，与 Cart 模型
        的完整字段不一致，因此按条目显式构造，而不是直接下发 Cart.to_dict()。
        """
        body = {"produtos": [self._body(item) for item in items]}
        response = self._client.post("/carrinhos", json=body)
        return response.json()

    def list(self) -> ModelList[Cart]:
        """GET /carrinhos：查询购物车列表（"数量 + 数组"包裹结构）。"""
        response = self._client.get("/carrinhos")
        return ModelList.from_dict(response.json(), "carrinhos", Cart)

    def get(self, cart_id: str) -> Cart:
        """GET /carrinhos/{id}：按主键查询单个购物车。"""
        response = self._client.get(f"/carrinhos/{cart_id}")
        return Cart.from_dict(response.json())

    def cancel(self) -> dict:
        """DELETE /carrinhos/cancelar-compra：取消当前 token 用户的购物车（商品库存恢复）。"""
        response = self._client.delete("/carrinhos/cancelar-compra")
        return response.json()

    def complete(self) -> dict:
        """DELETE /carrinhos/concluir-compra：完成当前 token 用户的购物车（购物车被删除）。"""
        response = self._client.delete("/carrinhos/concluir-compra")
        return response.json()
