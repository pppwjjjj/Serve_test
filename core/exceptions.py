"""core 层异常体系。

根据 ServeRest 官方 Swagger 文档（本地 /swagger.json）记录的 HTTP 状态码，
将错误响应映射为语义化异常，
service / 测试用例层通过捕获具体异常类型即可判断错误种类，无需判断状态码。

文档记录的错误状态码：
- 400 Bad Request  请求参数不合法：邮箱已注册、商品名已存在、用户/商品/购物车不存在等
- 401 Unauthorized token 缺失、无效或过期；登录时邮箱或密码错误（E-mail e/ou senha inválidos）
- 403 Forbidden    非管理员访问管理员专属路由（文档中仅 /produtos 的写操作）

成功状态码 200 / 201 不抛异常，原样返回响应对象。
其余未文档化的 4xx / 5xx 统一抛 APIError 基类兜底。
"""

from __future__ import annotations

import requests

##异常标签，通过将状态码映射成相应的异常标签，方便测试用例进行断言使用
class APIError(Exception):
    """所有 API 异常的统一基类，携带响应对象与状态码。"""

    status_code: int | None = None

    def __init__(self, response: requests.Response) -> None:
        self.response = response
        self.status_code = self.__class__.status_code or response.status_code
        # 优先取响应体的 message 字段，取不到时用原始文本兜底
        try:
            data = response.json()
        except ValueError:
            self.message = response.text or response.reason or ""
        else:
            self.message = data.get("message") or response.text or response.reason or ""
        super().__init__(f"[{self.status_code}] {self.message}")


class BadRequestError(APIError):
    """400 Bad Request：请求参数不合法。"""

    status_code = 400


class UnauthorizedError(APIError):
    """401 Unauthorized：token 缺失、无效或过期。"""

    status_code = 401


class ForbiddenError(APIError):
    """403 Forbidden：非管理员访问管理员专属路由。"""

    status_code = 403


STATUS_CODE_TO_ERROR: dict[int, type[APIError]] = {
    error.status_code: error
    for error in (BadRequestError, UnauthorizedError, ForbiddenError)
}


def raise_for_api_error(response: requests.Response) -> requests.Response:
    """响应状态码 >= 400 时抛出对应异常，否则原样返回响应。"""
    if response.status_code >= 400:
        error_cls = STATUS_CODE_TO_ERROR.get(response.status_code, APIError)
        raise error_cls(response)
    return response
