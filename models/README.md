当前层级：models
该层级用于数据转换。core层的`_request`返回的response被service层使用`get()`调用之后，通过`response.json()`获得返回的json字典。
根据暴露的操作接口`from_dict()`完成对json字典抽象，根据json字典的字段实例化创建对象，以字段为属性供后续层级操作
转换是双向的。既有json向数据模型的转换，也有根据操作数据模型后反向转换成json。

service 拿到这些模型对象后，业务编排（注册、登录、加购、取消）都建立在模型的属性读写之上。根据暴露的操作接口`to_dict()`将修改过的数据模型重新转换成json字典，以操作的数据模型的属性为字段反向转换，最后service层把`to_dict()`的结果作为请求体参数在core层发送出去。`to_dict()`和原来的json字典没有关系了，是根据现有的数据模型重新生成一个和原来传进来的那个json字典一样类型格式的新的json字典，其中的字段根据数据模型操作已经改变，模型的属性就是字段的`values`

关于返回的json字典中空字段的处理：json字典中有可能会返回空的字段，models层统一设置`None`作为默认值，因为models层只是个转换的中间层，没有业务逻辑代码，所以关于空字段或者缺失字段的处理能做的就只是在json字典转数据模型的`from_dict()`时设置默认值`None`。
```对于空字段或者缺失字段的`None`的处理是在service层，models层不作处理```

最后关于json字典的嵌套字典的处理：在models层中设置一个通用的字典模型`ModelList[T]`。
这么做可以把嵌套的json字典抽离出来单独做成一个通用的模板类型的字典数据模型，同样可以使用`from_dict()`处理。
而与原json字典的关系，根据`from_dict()`的参数进行识别，参数里有一个`key`使得抽离出来的这个字典能在最后生成新字典时能找到原来字典中它所在的那个位置，不会丢失。
用数据流表示为：响应字典（母字典）→ `ModelList.from_dict(母字典, key, 元素类)` → 它只读取母字典里`key`对应那一块（比如 usuarios），逐条喂给`User.from_dict()`，产出`ModelList(count=2, items=[User, User])`。
`from_dict`构造时把`key`存成模型的一个属性，`to_dict()`内部直接用，这样能保证接口的统一性。
产生新的`ModelList`数据模型对象一样供后续service层操作。`from_dict(母字典, key, 元素类)`时把`key`记住，`to_dict()`就能无参还原出完整的包裹字典，元素对象各自`to_dict()`递归重建。这样models层的三个资源模型、登录模型和通用包裹模型接口完全一致，`service`层不需要知道映射细节。

## 对外接口一览

models 层对外暴露以下模型类，统一由 `BaseModel` 基类提供双向转换接口：
- `User`：用户，映射 /usuarios 的响应
- `Product`：商品，映射 /produtos 的响应
- `Cart`：购物车，映射 /carrinhos 的响应
- `Login`：登录响应，映射 POST /login 的响应，承载 `authorization` 令牌
- `ModelList[T]`：通用包裹模型，处理"数量 + 资源数组"的嵌套列表响应

每个资源/登录模型统一提供两个转换接口：
- `from_dict(json字典)` → 模型对象：字段映射，缺失字段默认 `None`
- `to_dict()` → json字典：属性反向转换，`None` 原样保留

`ModelList[T]` 的接口带额外参数：
- `from_dict(响应字典, key, 元素类)` → 包裹模型对象：按 `key` 定位列表字段，逐条调用元素类的 `from_dict()`
- `to_dict()` → json字典：按构造时记住的 `key` 无参还原包裹结构

字段的葡萄牙语 → 英语重命名映射、每个字段的类型说明，以及"Bearer "前缀由 core 层 `set_token()` 剥离等细节，都写在各模型源码的注释里；本 README 只描述层级职责、数据流与工作流，不重复维护函数级文档，避免签名变更时两处维护。
