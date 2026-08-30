当前层级：config
该层级用于配置环境。通过__init__向外暴露当前层级的接口，使得别的层级调用时，通过from config import **即可，这样设计可以确保单向依赖，不会造成依赖混乱。

配置的加载从第一次执行 from config import settings 开始。config/__init__.py 在导入时会引入 config/settings.py，而 settings.py 在模块末尾直接调用 load_settings() 并赋值给模块级变量 settings，因此整个进程只加载一次配置，后续所有层级共享同一个不可变的 settings 对象，不会重复读取文件，也避免了不同模块各自读取配置造成的配置漂移。

load_settings() 默认把项目根目录下的 .env 作为配置来源，路径由 config/settings.py 所在位置向上推算得出，不依赖运行命令时的工作目录。它调用 python-dotenv 的 load_dotenv() 把 .env 中的键值注入进程的环境变量，同时保持 override=False 的默认行为，即进程里已有的同名环境变量不会被 .env 覆盖。

取值遵循三层优先级：真实环境变量优先于 .env 文件，.env 文件优先于代码内置的默认值 _DEFAULTS。这样本地开发只需维护 .env，未配置或缺失 .env 时仍能依靠默认值启动，而 CI 或 Jenkins 等外部环境可以直接注入环境变量覆盖本地配置，无需改动任何代码。

拿到的原始值都是字符串，需要进行类型转换与清洗：服务地址去掉末尾的斜杠，避免后续拼接请求路径时出现双斜杠；超时时间从字符串转为浮点数，重试次数转为整数，管理员邮箱与密码去除首尾空格，保证后续 core 层拿到的是干净且类型正确的数据。

转换完成后立即校验，采用 fail-fast 策略：地址必须以 http:// 或 https:// 开头，超时必须是大于 0 的数字，重试次数必须是非负整数，管理员邮箱与密码不能为空。任何一项不合法都会抛出带明确提示的 ValueError，配置在导入阶段就失败，整个测试套件不会带病运行。

校验通过后，所有字段被组装成一个 frozen=True 的 dataclass——Settings。不可变保证了全局配置在运行期间不会被任何层级意外修改。最终这个实例作为模块级单例 settings 暴露给外部。

其他层级使用时只需 from config import settings，然后读取 settings.base_url、settings.request_timeout 等字段即可，完全不需要知道 .env 的位置和加载细节。config 层因此实现了职责隔离：它只负责读取、校验和持有配置，不包含任何业务逻辑。


##
根据大体框架对该层进行总结就是，config层有一套注入参数的逻辑，即默认使用本地env，但外部参数注入优先级高于本地env，然后本地env优先级高于代码中的固定参数。这个级最终会返回一个Settings类对象，这个对象还是frozen不可中途更改的，确保每次运行时每个层级都能根据个返回的Settings对象使用同一套配置。
##