"""ServeRest 连通性冒烟测试（test_example/smoke_tests）。

目的：在运行正式用例之前，先验证“测试框架 -> service -> core -> ServeRest”
整条链路是否连通，避免 ServeRest 服务未启动时反复重试用例。

约定：
- 冒烟测试不做任何数据写入，全部是只读探测；
- 探测端点 /usuarios 无需登录即可访问，返回 200 + JSON；
- 服务未启动或地址不可达时，失败信息直接给出启动命令提示。
"""

from __future__ import annotations

import pytest
import requests

from config import settings
from core.client import Client
from core.exceptions import APIError
from service import LoginService

# GET /usuarios 无需 token，返回 200 + JSON，是稳定的只读连通性探针
_HEALTH_PATH = "/usuarios"

_START_HINT = (
    "请先执行 `docker compose up -d --wait` 启动 ServeRest，"
    "并确认 .env 中 SERVEREST_BASE_URL 与容器端口一致，然后重试。"
)


def _transport_error_summary(exc: requests.exceptions.RequestException) -> str:
    """只保留 requests 异常链的根因，避免把 urllib3 内部堆栈带进失败信息。"""
    cause = exc
    seen: set = set()
    while cause not in seen:
        seen.add(cause)
        next_cause = cause.__cause__ or cause.__context__
        if next_cause is None:
            break
        cause = next_cause
    return f"{type(cause).__name__}: {cause}"


@pytest.mark.smoke
def test_serverest_reachable():
    """服务可达：core 客户端能请求到 ServeRest 的业务端点。"""
    client = Client()
    transport_error: str | None = None
    try:
        response = client.get(_HEALTH_PATH)
    except requests.exceptions.RequestException as exc:
        transport_error = _transport_error_summary(exc)
    finally:
        client.close()

    if transport_error is not None:
        pytest.fail(f"无法连通 ServeRest（{settings.base_url}）：{transport_error}\n{_START_HINT}")

    assert response.status_code == 200
    payload = response.json()
    assert "usuarios" in payload and "quantidade" in payload


@pytest.mark.smoke
def test_admin_login_via_service_layer():
    """全链路登录：service -> core -> HTTP 能拿到管理员 token（只读探测）。"""
    client = Client()
    login_service = LoginService(client)
    transport_error: str | None = None
    api_error: str | None = None
    try:
        login = login_service.login(settings.admin_email, settings.admin_password)
    except requests.exceptions.RequestException as exc:
        transport_error = _transport_error_summary(exc)
    except APIError as exc:
        api_error = f"HTTP {exc.status_code}：{exc.message}"
    finally:
        client.close()

    if transport_error is not None:
        pytest.fail(f"无法连通 ServeRest（{settings.base_url}）：{transport_error}\n{_START_HINT}")
    if api_error is not None:
        pytest.fail(
            f"ServeRest 已响应，但管理员登录失败（{api_error}）\n"
            "请检查 .env 中 ADMIN_EMAIL / ADMIN_PASSWORD 是否仍是预置管理员账号。"
        )

    assert login.token, "登录响应未携带 authorization 令牌，请检查 models/login.py 字段映射"
