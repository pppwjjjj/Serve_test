"""登录/鉴权主题 · 反向用例。

被测对象：LoginService.login。
设计约定（见 test_example/README.md）：
- 反向用例断言 core 层按状态码贴好的异常标签（BadRequestError / UnauthorizedError），
  不直接断言 HTTP 状态码；
- 错误凭据（密码错误 / 邮箱不存在）统一返回 401，对应 UnauthorizedError；
- 缺少必填字段返回 400，对应 BadRequestError。
"""

from __future__ import annotations

import pytest

from config import settings
from core.exceptions import BadRequestError, UnauthorizedError
from service import LoginService


@pytest.mark.reverse
def test_login_with_wrong_password_raises_unauthorized(guest_client):
    """反向：预置管理员密码错误 → 401（UnauthorizedError 标签）。"""
    login_service = LoginService(guest_client)

    with pytest.raises(UnauthorizedError):
        login_service.login(settings.admin_email, "wrong-password")


@pytest.mark.reverse
def test_login_with_nonexistent_email_raises_unauthorized(guest_client, nonexistent_id):
    """反向：不存在的邮箱登录 → 401（UnauthorizedError 标签）。"""
    login_service = LoginService(guest_client)

    with pytest.raises(UnauthorizedError):
        login_service.login(f"{nonexistent_id}@example.com", "any-password")


@pytest.mark.reverse
def test_login_missing_password_raises_bad_request(guest_client):
    """反向：缺少密码字段 → 400（BadRequestError 标签）。"""
    login_service = LoginService(guest_client)

    # 传空字符串：service 层仍会下发 password 键，服务端按"必填为空"拒绝
    with pytest.raises(BadRequestError):
        login_service.login(settings.admin_email, "")
