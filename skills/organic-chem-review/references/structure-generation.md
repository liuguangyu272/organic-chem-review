# 代码生成化学结构式

本参考用于选方法、生成结构和检查正确性，不是全部工具的安装手册。优先使用当前环境已有工具；API 或依赖版本变化时核查下面的官方资料。

## 常见表示法和生成方式

“表示法”记录分子是什么，“渲染工具”决定如何显示，“识图模型”从图片提取候选结构；三者职责不同。复习通常不需要生成新分子的机器学习模型。

| 方法 | 适用任务 | 使用边界 |
| --- | --- | --- |
| SMILES / isomeric SMILES（含立体信息的分子线性编码） | 二维骨架、带电分子、明确的立体异构体；作为默认结构输入 | 字符顺序不等于画面顺序；`@/@@` 不直接等于 R/S，`/` 和 `\` 不可脱离邻接顺序机械对应 E/Z |
| MOL / SDF（原子、键、坐标和属性文件） | 已有结构文件、保留坐标、批量分子交换 | 导入后核对版本、立体信息及缺失属性；普通分子文件不能完整记录机理弯箭 |
| RDKit（Python 化学信息学工具包） | 验证结构、自动二维排布、SVG/PNG、网格比较图 | 不会自动解答反应题；普通二维排布不能替代指定椅式或 Newman 投影 |
| RDKit.js（RDKit 的 JavaScript/WebAssembly 分发） | 浏览器内结构卡片与交互高亮 | 使用当前真实可用的 JS/可视化环境，处理异步加载与对象释放；不假设普通 Markdown 能执行 JS |
| Open Babel（分子格式转换工具） | 转换 SMILES、MOL、SDF，生成二维坐标作为替代 | 转换前后核对连接关系、总电荷和立体信息；格式转换不是结构正确性的证明 |
| Chemfig + TikZ（LaTeX 结构与矢量排版） | 明确布局的反应机理、弯箭、Newman 投影和教学图 | 有编译工具才输出已渲染结果；不把原始 `\chemfig{...}` 当成 Work 原生可显示内容；自身不提供化学有效性校验 |
| ChemDraw 的 MOL/CDXML 交换 | 用户需要可编辑的 ChemDraw 结构或机理文件 | 使用确实支持的转换器/接口，不能仅改扩展名；无对应软件时只标明生成文件，不能声称已在 ChemDraw 验证 |
| MolScribe / DECIMER（化学结构图像识别模型） | 扫描讲义或截图提取为分子图/SMILES 的候选 | 不是普通结构渲染器。清晰的小结构可直接核对转录，不必装模型；模型输出必须与原图逐项核对，尤其是稠环、电荷、缩写与楔线 |

`mhchem` 用于化学式和反应方程排版；它不是通用的二维有机骨架式生成工具。InChI/InChIKey 可用于标识或检索，不能把 InChIKey 当成能直接恢复结构的可逆编码。

## 默认生成流程

1. **建立结构输入。** 从题目得到 SMILES 或现有 MOL/SDF；确认连接方式、形式电荷、同位素和指定的立体信息。题目未指定的构型保持未指定，不用随机楔线补全。缩写基团先确认含义；R、Ar 等泛指基团不能擅自替换成某个具体分子。
2. **化学校验。** 用默认启用检查的 `Chem.MolFromSmiles` 解析；失败时修正输入或说明该表示法不适合该物种，不能通过关闭 sanitize（价态等有效性检查）掩盖错误。解析后与题目对照分子式、碳骨架、总电荷和立体标签。芳香环小写原子与普通脂肪碳区别处理。
3. **生成与展示。** 调用本 skill 的 `scripts/render_structures.py`；默认生成 SVG 矢量图、PNG 展示图和 JSON 校验记录。优先嵌入客户端能显示的 PNG，需编辑或放大时再提供 SVG。不要把源码或长 SMILES 倾倒给只想复习化学的用户。
4. **核对输出。** 可视检查关键双键、楔线、形式电荷、文字重叠与边缘裁切。必要时提高尺寸或拆分结构。题面与答案分开渲染，防止预览、标签或校验记录泄露答案。

附带脚本需要 Python 和 RDKit；有可用环境才运行。调用示例（路径根据实际工作区调整）：

```text
python scripts/render_structures.py --smiles "CC(=O)O" --label "A" --output work/structure-a
python scripts/render_structures.py --smiles "C[C@H](O)C(=O)O" --smiles "C[C@@H](O)C(=O)O" --label "A" --label "B" --output work/pair
python scripts/render_structures.py --input work/molecules.json --output work/grid --atom-indices
```

`--input` 接受 UTF-8 JSON 数组，元素如 `{"smiles":"CC(=O)O","label":"A"}`；与 `--smiles` 二选一。默认最多三列，`--columns` 可调。`--atom-indices` 显示 RDKit 的零起始原子索引，只是当前输入的讲解标记，不是 IUPAC 命名编号；跨反应步骤应用稳定的原子映射而非依赖索引恰好不变。图中用 A/B 等短标签，中文名称放在图外以避免字体缺字。

脚本的 JSON 记录含规范异构 SMILES、分子式、总电荷、手性中心及指定双键信息，便于助手核查；不代表已经自动核对题意。它只生成分子结构，不自动预测产物、添加反应条件或画机理弯箭。

## 反应机理与空间表示

- 普通反应图：以分别核验的反应物、产物和已知条件构成方案；Reaction SMILES 可用于结构间交换或排布，但不包含完整电子流。含原子映射的反应输入先核对同号原子对应关系。
- 弯箭：用 RDKit 的分子坐标定位原子/键，再用 SVG 路径，或 Chemfig/TikZ 的锚点添加弧线。起点是孤对电子、单电子或具体键，终点是接收原子或将形成的键；指向键时不能随意指到邻近原子。双电子和单电子箭头区分。图中缺省不显示孤对电子时，必要处显式补出。
- Newman、Fischer、椅式：从明确的立体结构和观察方向构造专门布局，用程序坐标或 Chemfig 输出，标明前后碳、上下/轴赤道关系。不能把普通 RDKit 平面六边形称为椅式构象，或从二维布局推断实际二面角。
- 三维模型：只在构象、位阻和空间关系需要时使用；先有正确的带立体信息分子图，再生成构象。计算得到的构象不是实验测量结构，也不自动代表唯一或全局最低能构象。

## 编码教学的最小顺序

只有用户想学结构编码时，才按“原子与键 → 支链 → 环闭合 → 芳香性与电荷 → 手性与双键立体”展开。每次解释一个符号并立即渲染对照，不一次教完整语法。示例可以从 `CCO`（乙醇）、`CC(=O)O`（乙酸）、`c1ccccc1`（苯）开始；不能从相同分子式推出唯一 SMILES。

## 官方依据

- [RDKit：读取、验证与绘制分子](https://www.rdkit.org/docs/GettingStartedInPython.html)
- [RDKit：二维渲染 API](https://www.rdkit.org/docs/source/rdkit.Chem.Draw.rdMolDraw2D.html)
- [Daylight：SMILES 语法与立体化学](https://daylight.com/dayhtml_tutorials/languages/smiles/index.html)
- [RDKit.js：官方文档](https://www.rdkitjs.com/)
- [Open Babel：格式转换](https://openbabel.org/docs/Command-line_tools/babel.html)
- [Chemfig：结构图排版](https://ctan.org/pkg/chemfig)；[mhchem：化学式与方程](https://ctan.org/pkg/mhchem)
- [ChemDraw：CDXML 与 MDL 文本交换](https://support.revvitysignals.com/hc/en-us/articles/54009539308052-Release-Announcement-ChemDraw-Desktop-26-1)
- [MolScribe：原项目](https://github.com/thomas0809/MolScribe)；[DECIMER：原项目](https://github.com/Kohulan/DECIMER-Image_Transformer)
