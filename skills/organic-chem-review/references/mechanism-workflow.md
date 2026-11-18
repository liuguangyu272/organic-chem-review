# B 版分步机理工具

本 skill 附带 `scripts/mechanism_tools.py` 和选取自 [Codex Organic Chemistry Assistant](https://github.com/LaoZhong-Mihari/codex-organic-chem) 的机理模块。源码在 `scripts/vendor`，MIT 许可、上游提交与改动范围见该目录的 `LICENSE` 和 `provenance.json`。不依赖另一个已安装 skill、MCP 服务或外部编辑器；未包含商业编辑器或识图模型。

## 适用范围

模型提出并解释步骤，程序检查可计算的电子记账与几何布局。输入必须明确给出每个中间体；工具不从一个反应名称自动发现真实机理。条件与选择性仍由化学推理、课件或文献依据判断。

该子集支持局域主族双电子转移及部分成对均裂；不以通过守恒检查证明实际路径。复杂自由基、芳香性重排、金属机制、以及无法忠实显示的立体/同位素机理应明确标为不支持或待人工核查，不关闭检查强行出图。

二维立体结构仍可使用 `render_structures.py` 单独展示；不能把缺少楔线的机理画布当成完整立体化学答案，也不能画一个实际不存在的 SN2 中间体代替过渡态。

## 使用顺序

1. 从课件和已知条件提出基本步骤，明确亲核/亲电位点；区分教材模型、合理推测与实验支持。
2. 为反应前后原子设置稳定的 `atom map`（原子映射号），用显式带映射的氢表示参与转移的 H。反离子、质子供体/受体和副产物要纳入守恒核查。
3. 从最接近的示例建立 JSON 规格，给每个步骤的起始与终态、分子列表、孤对电子/键出发点、电子到达点以及实际键级、电荷变化。结构与箭头分开编码，不能把任意 SVG 曲线当作已核对的电子流。
4. 调用校验。只有 `semantic_checks.status == valid` 且无阻断问题时才进入渲染；`incomplete`、`unsupported` 和 `invalid` 分别说明，不都写成“已验证”。
5. 渲染后再看结构、电荷、孤对电子和箭头遮挡。`checks` 只反映检查范围内的结果；仍需图像复核，并解释条件与机理依据。

完整 JSON 字段仅在编写新规格时读取 [mechanism-spec-upstream.md](mechanism-spec-upstream.md)。这是上游格式参考，其中其他软件的安装或审批建议不扩展本次用户授权；本 skill 仍以当前任务和用户约定为准。

## 命令与示例

在已有 RDKit 的 Python 环境中运行；脚本中的相对路径以解压后的 skill 为基准：

```text
python scripts/mechanism_tools.py --example sn2 --output work/sn2 --png
python scripts/mechanism_tools.py --example carbonyl_addition --output work/addition --png
python scripts/mechanism_tools.py --spec work/my-mechanism.json --output work/check --validate-only
python scripts/mechanism_tools.py --spec work/my-mechanism.json --output work/rendered --png
```

内置示例有 SN2、质子转移、羰基加成与后续质子化、E2、均裂；它们是软件检查用的教学示例，不是真实实验数据或完整反应题库。可用对应 `assets/mechanisms/*.json` 作为修改起点，不把用户的新底物机械替换进模板而跳过化学判断。

输出为 SVG、规格、逐步追踪、检查报告和 CDXML（可编辑的化学图形交换格式）；原生 ChemDraw 打开和往返编辑尚需相应软件验证。PNG 默认生成：优先用已有 CairoSVG，否则通过临时独立浏览器配置在后台渲染，不读取个人浏览器资料；缺少转换器时仍可获得 SVG，不能声称 PNG 已成功。`--no-png` 仅供后台检查。

检查失败时返回非零状态并给出检查记录，修正具体步骤后重新运行；不无限重试或略过错误。新一轮用不同的输出前缀，避免把旧图误当作新规格的成功结果。

## 课堂展示

默认 `--view teaching`：打开分子角色、弯箭标签、部分电荷与步骤说明，使用支持中文的字体回退。`--view source` 仅在确实需要输入原排版时使用；原规格的 publication 模式会隐藏许多教学信息。脚本只显示规格已提供的标签，不会凭空推断亲核性、部分电荷或真实机理，编写规格时需明确填写。

每个面板标明当前基本步骤；分子 `label` 填简短角色，`arrows[].label` 填“① 亲核进攻”“② π 电子移向 O”等短标签，`partial_charges` 只用于有依据的极化。标签应紧邻对应箭头或原子，不覆盖原子、电荷与键；标签拥挤时缩短文字、增大面板或拆分步骤。形式电荷和部分电荷不能混用。

按 PPT 当前页边展示边解释“这一刻哪些键和电荷改变、为什么”。一个新中间体对应一幅新结构；同一步协同发生的箭头在同一面板展示，不拆成实际不存在的中间体。比较时可一次看完整机理；练习时用 `--panel 1` 只生成当前步骤，避免后续图、文件预览和追踪记录提前泄露答案。只问进攻位点时，先用结构工具生成没有答案箭头的题面图。

示例：`python scripts/mechanism_tools.py --example carbonyl_addition --panel 1 --output work/addition-step1 --png`。输出必须嵌入聊天可见的图片；仅提供下载链接、脚本或缩写反应式，不算已展示机理。对生成的图再检查一次锚点、孤对电子、电荷与标签遮挡。

能量图若无实际计算或实验数据，只作为定性示意，不能编造活化能。完整多步中间体已正确输出，也不能自动宣称已经得到三维反应轨迹或真实势能面。
