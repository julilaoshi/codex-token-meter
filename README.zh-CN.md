# Codex Token Meter｜Token 计量表

**看清每个任务的 Token 消耗。**

[一键安装](#一键安装) · [English](README.md) · [给项目点 Star](https://github.com/julilaoshi/codex-token-meter)

公开版 v1.0.0 · macOS 本地工具 · Python 3.9+ · 无第三方 Python 依赖 · 运行不调用 AI

![Token 计量表演示，名称和数值均为虚构](docs/demo.png)

*截图里的任务、名称和用量全部是演示数据。*

## 一个小面板，看清正在发生的消耗

- 上方：正在工作的任务，动态转圈、任务累计、上一轮对话用量。
- 下方：其他已结束任务的本周期用量前五名。
- 每个任务：本周期 token 占比与小饼图。
- 每三秒自动更新，直角长条、大数字、小标签。

独立社区工具，非 OpenAI 官方产品。不注册 Skill、MCP 或插件。

## 一键安装

需要 macOS、Python 3.9+ 和本地 Codex 会话记录。无需 sudo、订阅账号密码或 API key。运行前可先查看 [安装脚本](install.sh)。

```sh
curl -fsSL https://raw.githubusercontent.com/julilaoshi/codex-token-meter/v1.0.0/install.sh | sh
```

安装程序下载固定版本、核验 SHA-256、安装到用户自己的工具目录并启动服务。点击它输出的本机地址即可查看，也可以让 Codex 在右侧浏览器打开。右侧网页属于当前任务的浏览器标签页，并非 Codex 全局内嵌组件。

**也可以把这段话直接交给 Codex：**

```text
帮我安装 https://github.com/julilaoshi/codex-token-meter 。
先读 README 并检查 install.sh，安装带标签的发行版，验证本地服务，
然后在右侧浏览器打开它输出的地址。不要上传我的本地记录，不要注册 Skill。
```

手动方式：下载并解压 Release ZIP，在目录里执行 `python3 meter.py install`。

## 启动、停止、更新和卸载

```sh
python3 ~/.local/share/codex-token-meter/meter.py status
python3 ~/.local/share/codex-token-meter/meter.py start
python3 ~/.local/share/codex-token-meter/meter.py stop
python3 ~/.local/share/codex-token-meter/meter.py uninstall
```

更新时重新运行新发行版安装器。不会设置开机自启或自动升级；重启电脑后需再次启动。默认从 8793 起寻找空闲端口，以输出地址为准。关闭网页即停止轮询，后台服务仍可供下次打开。

## 占比是什么

**本任务在当前周期已用 token ÷ 本机可读取任务在当前周期已用 token。**

这不是订阅额度百分比，不是费用，也不是上下文占用。不能通过选择 Pro 20× 换算出固定 token 上限。

周期来自本地最新的 Codex 七天额度记录：重置时间往前七天到重置时间，日期按北京时间展示。周期缺失或过期时暂不显示占比和排行，不编造新周期。累计值转增量统计，相同时间和累计量的重复事件只归属一次；上一轮对话是最近一个结束或取消的用户轮次，不是最后一次模型请求。

## 隐私与适用范围

- 正常监控不联网、不调用模型；安装时从 GitHub 下载程序。
- 只读本机任务元数据和用量记录，不修改 Codex 数据，不向页面返回聊天正文或凭证。
- 服务仅监听本机；同机有访问能力的程序仍可能读取页面中的任务标题，不能视为应用间的安全隔离。
- 可通过 `CODEX_HOME` 指定数据目录；可在启动前设置 `TOKEN_METER_EXCLUDE`，用冒号分隔要排除的私密目录。
- 只统计本机可读数据，排除子 Agent；归档任务可以进入排行。云端独有任务及其他电脑数据不在范围内。
- “进行中”包含等待工具与确认。日志静默超过 30 分钟时暂时隐藏；真正长时间无日志的任务也会受到影响。
- 扫描最近八天更新的任务元数据；缺失记录、分叉会话和日志格式变化可能影响归属。这不是官方账单审计。

## 演示与贡献

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -p 'test_*.py'
python3 meter.py start --demo --home /tmp/token-meter-demo --port 8893
python3 meter.py stop --home /tmp/token-meter-demo
```

演示模式不读取 Codex 数据。提交问题时请用合成数据，不要上传真实会话或用量截图。见 [贡献指南](CONTRIBUTING.zh-CN.md)。

## 分享这个工具

觉得有用，可以[点 Star](https://github.com/julilaoshi/codex-token-meter)、分享仓库链接，或使用[中英文宣传文案](docs/launch-copy.md)。[关注 GitHub 作者](https://github.com/julilaoshi)获取更新。

## 许可

代码采用 [MIT](LICENSE)，身份及商标说明见 [BRAND_NOTICE](BRAND_NOTICE.md)。
