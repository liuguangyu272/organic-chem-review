# 选择执行环境

本技能需要 Python、RDKit 及其正常依赖；不需要注册 MCP 或连接远程化学编辑器。

先检查当前 Python 能否导入 `rdkit`。若没有，按当前任务授权在工作目录创建独立环境，安装本技能的 `scripts/requirements.txt`；不把特定作者机器的目录当成可用环境。不能运行 Python 或安装依赖时，明确限制，提供缩写结构或源码，不声称已完成图像或机理校验。

Windows 使用虚拟环境的 `Scripts/python.exe`，macOS/Linux 使用 `bin/python`。将脚本路径解析为当前安装的技能目录；不要假定技能在当前工作目录。

最初实测环境为 Windows、Python 3.14、RDKit 2026.09.2；其他环境以仓库自动检查的实际结果为准，不将其扩大成全部平台、全部旧版本均已验证。机理核心是带 MIT 许可的上游源码子集，不是安装上游正式发行包；来源和改动见 `scripts/vendor/provenance.json`。

结构 PNG 由 RDKit 生成。机理的 SVG 始终是主文件；可选 PNG 预览需要本地 Edge/Chrome/Chromium，使用临时独立配置及后台进程，不读取个人浏览器资料。没有浏览器时保留 SVG，不声称 PNG 已生成。
