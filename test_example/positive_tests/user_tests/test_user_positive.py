"""用户主题 · 正向用例。

被测对象：UserService 的 create / list / update / delete 原子操作。
设计约定：
- 注册使用随机唯一 email，用例可重复执行，不会撞"重复 email 400"；
- 用例结束后删除自建用户——删除不存在用户返回 200，因此 teardown 幂等；
- 正向只断言业务结果（模型字段 / 返回 message），不直接断言状态码。
"""

from __future__ import annotations

import pytest

from core.client import Client
from models import User
from service import UserService


@pytest.mark.positive
def test_create_user_and_get_by_id(guest_client, user_payload, request):
    """创建用户成功：_id 被回填，按 id 查询能取回一致字段。

    不只断言创建响应的 message，而是再 GET 一次，
    证明数据真正落库且 models 层字段映射正确。
    """
    user_service = UserService(guest_client)
    user = user_service.create(user_payload)

    # 创建成功后登记清理；即使断言失败，teardown 也会删除该用户
    request.addfinalizer(lambda: user_service.delete(user.id))

    assert user.id is not None

    fetched = user_service.get(user.id)
    assert fetched.id == user.id
    assert fetched.name == user_payload.name
    assert fetched.email == user_payload.email
    assert fetched.administrator == "false"


@pytest.mark.positive
def test_list_users_filters_by_email(normal_user):
    """按 email 精确查询用户列表：唯一命中自建用户。

    GET /usuarios?email= 返回"quantidade + usuarios"包裹结构，
    这里验证 models 层 ModelList 的解析结果（count 与 items）。
    """
    user, client = normal_user
    user_service = UserService(client)

    result = user_service.list(email=user.email)

    assert result.count == 1
    assert result.items is not None
    assert len(result.items) == 1
    assert result.items[0].email == user.email


@pytest.mark.positive
def test_update_user_changes_fields(normal_user):
    """更新用户成功：修改 nome 后按 id 查询可见新值。

    说明：
    - PUT 是整体更新，请求体仍需携带其余必填字段；
    - 这里只改 nome、保持 email 不变，避免破坏用例后续的校验与清理上下文。
    """
    user, client = normal_user
    user_service = UserService(client)

    new_name = f"{user.name}_updated"
    update_payload = User(
        name=new_name,
        email=user.email,
        password=user.password,
        administrator=user.administrator,
    )
    result = user_service.update(user.id, update_payload)

    assert result["message"] == "Registro alterado com sucesso"

    fetched = user_service.get(user.id)
    assert fetched.name == new_name
    assert fetched.email == user.email


@pytest.mark.positive
def test_delete_user_removes_record(normal_user):
    """删除用户成功：返回成功 message，且按 email 查询不再命中。

    删除后 fixture teardown 会再次删除该用户 id，ServeRest 对
    不存在的用户删除返回 200（Nenhum registro excluído），因此是安全幂等的。
    """
    user, client = normal_user
    user_service = UserService(client)

    result = user_service.delete(user.id)
    assert result["message"] == "Registro excluído com sucesso"

    # 用原 email 精确查询，验证记录确实已被删除
    after = user_service.list(email=user.email)
    assert after.count == 0
    assert after.items == []
