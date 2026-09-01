"""models 层：数据转换层。

职责：把 core 层返回的 JSON 字典映射成带类型的数据对象，供 service 层进行业务操作。
对外暴露的统一接口：
- User / Product / Cart：三个资源模型，字段由葡萄牙语重命名为英语
- Login：登录响应模型，承载 authorization 令牌
- ModelList：通用包裹模型，处理"数量 + 资源数组"的嵌套列表响应
"""

from models.base import BaseModel
from models.cart import Cart
from models.login import Login
from models.model_list import ModelList
from models.product import Product
from models.user import User

__all__ = ["BaseModel", "Cart", "Login", "ModelList", "Product", "User"]
