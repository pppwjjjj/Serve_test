"""ServeRest 自动化测试 —— 配置层。

职责：从 ``.env`` / 环境变量读取并校验全局配置；
不包含任何业务逻辑，其他层统一通过 :data:`settings` 单例访问。
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# config/settings.py 的上一级目录即项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

# 内置默认值：变量未设置（含 .env 中缺失）时兜底，保证没有 .env 也能启动
_DEFAULTS = {
    "SERVEREST_BASE_URL": "http://localhost:3000",
    "REQUEST_TIMEOUT": "10",
    "REQUEST_RETRIES": "1",
    "ADMIN_EMAIL": "fulano@qa.com",
    "ADMIN_PASSWORD": "teste",
}


@dataclass(frozen=True)
class Settings:
    """全局配置，字段含义与 .env.example 一一对应。"""

    base_url: str  # ServeRest 服务根地址
    request_timeout: float  # 单次请求超时（秒）
    request_retries: int  # 连接失败时的额外重试次数
    admin_email: str  # 预置管理员账号
    admin_password: str


def load_settings(env_file: Path | None = None) -> Settings:
    """读取配置并做基础校验，返回不可变 Settings。

    取值优先级：真实环境变量 > ``.env`` 文件 > 内置默认值。
    ``env_file`` 为 None 时使用项目根目录下的 ``.env``。
    """
    path = ENV_FILE if env_file is None else env_file
    load_dotenv(path)

    def _get(name: str) -> str:
        return os.getenv(name, _DEFAULTS[name])

    # --- 服务地址 ---
    base_url = _get("SERVEREST_BASE_URL").rstrip("/")
    if not base_url.startswith(("http://", "https://")):
        raise ValueError(f"SERVEREST_BASE_URL 必须以 http(s):// 开头，当前值: {base_url!r}")

    # --- 超时 ---
    try:
        request_timeout = float(_get("REQUEST_TIMEOUT"))
    except ValueError:
        raise ValueError(
            f"REQUEST_TIMEOUT 必须是数字，当前值: {_get('REQUEST_TIMEOUT')!r}"
        ) from None
    if request_timeout <= 0:
        raise ValueError(f"REQUEST_TIMEOUT 必须大于 0，当前值: {request_timeout}")

    # --- 重试 ---
    try:
        request_retries = int(_get("REQUEST_RETRIES"))
    except ValueError:
        raise ValueError(
            f"REQUEST_RETRIES 必须是整数，当前值: {_get('REQUEST_RETRIES')!r}"
        ) from None
    if request_retries < 0:
        raise ValueError(f"REQUEST_RETRIES 不能为负数，当前值: {request_retries}")

    # --- 预置管理员账号 ---
    admin_email = _get("ADMIN_EMAIL").strip()
    admin_password = _get("ADMIN_PASSWORD").strip()
    if not admin_email or not admin_password:
        raise ValueError("ADMIN_EMAIL / ADMIN_PASSWORD 不能为空")

    return Settings(
        base_url=base_url,
        request_timeout=request_timeout,
        request_retries=request_retries,
        admin_email=admin_email,
        admin_password=admin_password,
    )


# 模块级单例：各层 `from config import settings` 即可使用
settings = load_settings()
