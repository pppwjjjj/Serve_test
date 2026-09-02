"""ServeRest 自动化测试 —— core 层客户端骨架。

core 层是对 requests 的封装，是 service 层与 HTTP 世界之间唯一的通道。
Client 内部持有一个 requests.Session（底层为 urllib3 连接池），
所有 HTTP/HTTPS 请求都经由这一个 Session 收发。
"""

from __future__ import annotations

import requests

from config import Settings, settings as default_settings
from core.exceptions import raise_for_api_error


class Client:
    """HTTP 客户端主体：维护连接池，统一收发请求。
    """

    def __init__(self, settings: Settings | None = None) -> None:
        # 不传时默认使用 config 层的全局单例 settings
        self._settings = settings or default_settings
        # Session 复用底层 TCP 连接（urllib3 连接池），所有请求都走它
        self._session = requests.Session()
        # 登录后由 set_token() 注入，后续步骤实现
        self._token: str | None = None

    @property
    def base_url(self) -> str:
        """服务根地址，来自 config 层。"""
        return self._settings.base_url

    @property
    def timeout(self) -> float:
        """单次请求超时（秒）。"""
        return self._settings.request_timeout

    @property
    def retries(self) -> int:
        """连接失败时的额外重试次数。"""
        return self._settings.request_retries


##这里就是整个测试框架的核心，_request()是所有请求的出入口
    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        """统一请求入口：所有 get/post/put/delete 都汇聚到这里。

        职责：
        - 拼接 base_url 与相对路径（自动处理两侧多余的斜杠）
        - 已设置 token 时自动注入 Authorization: Bearer 头
        - 注入默认超时（调用方可通过 kwargs 覆盖）
        - 连接失败时按配置重试（额外次数 = request_retries）
        - 状态码 >= 400 时按文档映射抛出 APIError 子类
        - 经由唯一的 Session 发送请求并返回响应对象
        """
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"

        # 处理 headers，自动注入 token
        headers = dict(kwargs.pop("headers", None) or {})
        if self._token:
            headers.setdefault("Authorization", f"Bearer {self._token}")

        kwargs["headers"] = headers
        kwargs.setdefault("timeout", self.timeout)

        attempts = self.retries + 1  # 首次请求 + 额外重试次数
        for attempt in range(1, attempts + 1):
            try:
                response = self._session.request(method.upper(), url, **kwargs)
            except requests.exceptions.ConnectionError:
                if attempt == attempts:
                    raise  # 已是最后一次尝试，把异常抛给上层
                continue  # 否则进入下一次尝试
            return raise_for_api_error(response)

    @property
    def token(self) -> str | None:
        """当前注入的 token 本体（只读）。

        set_token() 会把 "Bearer " 前缀剥离后保存，
        这里返回的就是剥离后的 token 本体，未注入时返回 None。
        token 只允许读取，注入与替换统一走 set_token()。
        """
        return self._token

    def set_token(self, token: str) -> None:
        """注入登录接口获取的动态 token，后续请求自动携带。

        兼容 "Bearer eyJ..." 与纯 "eyJ..." 两种输入，统一只存 token 本体，
        _request 拼接时统一加一次 "Bearer " 前缀，避免重复。
        """
        self._token = token.strip().removeprefix("Bearer ")

##这四个方法是 service 层调用的接口，最终都会调用 _request() 发送请求
    def get(self, path: str, **kwargs) -> requests.Response:
        """发送 GET 请求，供 service 层调用。"""
        return self._request("GET", path, **kwargs)

    def post(self, path: str, **kwargs) -> requests.Response:
        """发送 POST 请求，供 service 层调用。"""
        return self._request("POST", path, **kwargs)

    def put(self, path: str, **kwargs) -> requests.Response:
        """发送 PUT 请求，供 service 层调用。"""
        return self._request("PUT", path, **kwargs)

    def delete(self, path: str, **kwargs) -> requests.Response:
        """发送 DELETE 请求，供 service 层调用。"""
        return self._request("DELETE", path, **kwargs)

    def close(self) -> None:
        """释放 Session 占用的连接池。"""
        self._session.close()
