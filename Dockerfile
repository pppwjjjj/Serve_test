# 语法声明：使用 Dockerfile 1 语法，保证 COPY --chown 等指令可用
# syntax=docker/dockerfile:1

# 测试框架镜像：只打包"运行 pytest 需要的东西"，不包含 docker-compose.yml
FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 第 1 步：只拷贝依赖清单并安装。
# 依赖层放最前面，源码改动时不会触发 pip install 重新执行（利用镜像层缓存）。
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 第 2 步：拷贝项目源码与 pytest 配置。
# 按层目录逐个 COPY，避免把 .venv/.git/.env 等无关文件带进镜像。
COPY config/ config/
COPY core/ core/
COPY models/ models/
COPY service/ service/
COPY test_example/ test_example/
COPY pytest.ini .

# 第 3 步：创建非 root 用户，测试容器以 appuser 运行。
RUN useradd --create-home --shell /usr/sbin/nologin appuser \
    && chown -R appuser:appuser /app
USER appuser

# 默认行为：python -m pytest（pytest.ini 已配置 testpaths 与 --alluredir）。
# 通过 docker compose run --rm tests -m smoke 追加参数即可选择分组。
ENTRYPOINT ["python", "-m", "pytest"]
CMD ["-q"]
