"""service/base.py —— service 层公共基类。

每个资源服务都持有一个 core 层 Client，所有原子操作统一经它收发请求。
"""

from __future__ import annotations

from core.client import Client
from models.base import BaseModel


class BaseService:
    """service 层基类：统一持有 client，并提供请求体构造等公共 helper。"""

    def __init__(self, client: Client) -> None:
        # 依赖注入：client 由调用方（test 层 / 后续场景函数）传入，
        # 保证"管理员 / 普通用户 / 无 token"可以各持一个 client，互不污染。
        self._client = client

    @property
    def client(self) -> Client:
        """当前服务使用的 HTTP 客户端。"""
        return self._client

    @staticmethod
    def _body(model: BaseModel, *, exclude: frozenset[str] = frozenset({"_id"})) -> dict:
        """模型 → 请求体。

        - to_dict() 中值为 None 的字段表示"未设置/不存在"，发送前统一丢弃；
          这是 models 层约定由 service 层处理的 None 语义；
        - 主键字段（默认 _id）由服务端生成，POST / PUT 请求体不应携带，默认排除。
        """
        return {
            api_field: value
            for api_field, value in model.to_dict().items()
            if api_field not in exclude and value is not None
        }
