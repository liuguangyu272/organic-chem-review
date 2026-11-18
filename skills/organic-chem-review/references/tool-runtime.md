# 选择执行环境

本技能需要 Python、RDKit 及其正常依赖；不需要注册 MCP 或连接远程化学编辑器。

先检查当前 Python 能否导入 `rdkit`。若没有，按当前任务授权在工作目录创建独立环境，安装本技能的 `scripts/requirements.txt`；不把特定作者机器的目录当成可用环境。不能运行 Python 或安装依赖时，明确限制，提供缩写结构或源码，不声称已完成图像或机理校验。

Windows 使用虚拟环境的 `Scripts/python.exe`，macOS/Linux 使用 `bin/python`。将脚本路径解析为当前安装的技能目录；不要假定技能在当前工作目录。

最初实测环境为 Windows、Python 3.14、RDKit 2026.09.2；其他环境以仓库自动检查的实际结果为准，不将其扩大成全部平台、全部旧版本均已验证。机理核心是带 MIT 许可的上游源码子集，不是安装上游正式发行包；来源和改动见 `scripts/vendor/provenance.json`。

结构 PNG 由 RDKit 直接生成；机理工具默认同时生成 SVG 与用于聊天内显示的 PNG，先尝试已有 CairoSVG，再尝试 Edge/Chrome/Chromium 的独立临时配置，不读取个人浏览器资料、不抢占焦点。没有可用转换器时如实报告缺少 PNG，不把 SVG 代码或下载链接当成已显示图片。`--no-png` 仅用于后台批量检查；复习讲解应展示实际图片，并查看文字、弯箭、电荷与边缘是否完整。
