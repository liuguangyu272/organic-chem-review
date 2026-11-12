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

输出为 SVG、规格、逐步追踪、检查报告和 CDXML（可编辑的化学图形交换格式）；原生 ChemDraw 打开和往返编辑尚需相应软件验证。`--png` 在有本地 Edge/Chrome/Chromium 时使用临时独立配置在后台生成预览，不读取个人浏览器资料；没有浏览器仍可获得 SVG，不能声称 PNG 已成功。

检查失败时返回非零状态并给出检查记录，修正具体步骤后重新运行；不无限重试或略过错误。新一轮用不同的输出前缀，避免把旧图误当作新规格的成功结果。

## 课堂展示

按 PPT 当前页给“这一刻哪些键和电荷改变、为什么”的解释，再展示对应步骤。比较时可一次看完整机理；练习时只显示已到的步骤，后续图和追踪记录不能提前泄露答案。

能量图若无实际计算或实验数据，只作为定性示意，不能编造活化能。完整多步中间体已正确输出，也不能自动宣称已经得到三维反应轨迹或真实势能面。
