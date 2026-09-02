"""service/product_service.py —— 商品服务。

原子操作：/produtos 的增删改查，每个方法对应一次 HTTP 请求。
写操作需要管理员 token，缺失或越权时由 core 层抛出 401 / 403 异常。
"""

from __future__ import annotations

from models import ModelList, Product
from service.base import BaseService


class ProductService(BaseService):
    """商品服务：/produtos 端点级原子操作。"""

    def create(self, product: Product) -> Product:
        """POST /produtos：创建商品，回填服务端生成的 _id 后返回同一模型。"""
        response = self._client.post("/produtos", json=self._body(product))
        product.id = response.json()["_id"]
        return product

    def get(self, product_id: str) -> Product:
        """GET /produtos/{id}：按主键查询单个商品。"""
        response = self._client.get(f"/produtos/{product_id}")
        return Product.from_dict(response.json())

    def list(self, **params) -> ModelList[Product]:
        """GET /produtos：查询商品列表，支持按字段名传 query 参数（如 nome）。"""
        response = self._client.get("/produtos", params=params)
        return ModelList.from_dict(response.json(), "produtos", Product)

    def update(self, product_id: str, product: Product) -> dict:
        """PUT /produtos/{id}：整体更新商品，返回响应字典（message）。"""
        response = self._client.put(f"/produtos/{product_id}", json=self._body(product))
        return response.json()

    def delete(self, product_id: str) -> dict:
        """DELETE /produtos/{id}：删除商品，返回响应字典（message）。"""
        response = self._client.delete(f"/produtos/{product_id}")
        return response.json()
