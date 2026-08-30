当前层级：core
该层级用于处理收发请求，内部基于 `requests.Session` 维护一个连接池，所有`request`请求都从这里发出，`respond`回复从这里进入测试框架供后续层级使用。这一层级的本质就是整个测试框架的核心，类似于一个平台，连接外部为内部测试用例提供服务。

服务包括：收发请求，统一`URL`，运行的动态`token`令牌注入，超时和重试，连接失败重试以及最后的日志生成(日志生成暂时跳过，后续再计划加入)。

`_request()`是整个测试框架的核心，所有的`http/https`请求的收发都从这里出去，返回的是`response`也从这里回来。

`core`层对外暴露了四个操作方法的接口：`GET`、`POST`、`PUT`、`DELETE`。这四个接口都是给`service`调用的，用来操控`client`进行请求的收发，其他的功能服务都集成在`_request`内部。


关于token注入：这里的token是指运行过程中获得的令牌，是动态的，不能通过env文件注入。内置拼接`Bearer `前缀以及保存token本体的功能
后续`service`层进行原子性的业务操作时会获取到相应的token，token使用`set_token()`进行接收，因为它是`client`这个类的方法，所以会同步到`_request()`中，这样就能无缝进行业务操作了，方便后续的业务拼接。


加入了exceptions异常标签，由`Client`中的`response`支持，`Client` 在 `_request` 中收到响应后，按状态码抛出对应异常：400/401/403 映射为`BadRequestError`/`UnauthorizedError`/`ForbiddenError`，未文档化的状态码由 `APIError` 兜底，后续`test_example`层进行断言处理时可以根据这些异常标签进行判断
