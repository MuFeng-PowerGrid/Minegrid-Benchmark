<!-- This README is one language at a time. Other versions are linked below. -->

[English](../../README.md) · **中文** · [Français](README.fr.md) · [Español](README.es.md) · [Русский](README.ru.md) · [العربية](README.ar.md)

<p align="center">
  <img src="../assets/logo_brand.png" width="760" alt="MINEGRID — Power System Made Simple">
</p>

# MINEGRID

### 从电力系统模型到多模态推理

MINEGRID 汇集详细的非线性设备模型说明、图像与标注配对数据，以及网络指令数据。模型库可用于构建初步规模的研究型仿真软件；多模态基准用于研究视觉语言模型如何理解控制框图与电力网络。

## 数据模块

- **[典型设备模型](../../Multimodal/Alpaca%20Data/Apparatus/index.html)** — 14 类设备 · 46 个配置 · HTML 模型说明
- **[多模态基准](../../JSON%20Index/README.md)** — 1,429 组图像与标注 · 2 类任务 · 3 个难度
- **[补充指令数据](../../Multimodal/Alpaca%20Data/README.md)** — 网络指令数据及一个通用知识示例文件

## 典型设备：建模内容

各设备页面包含状态变量、参数、输入输出、微分与代数方程、非线性限幅及建模假设。详细配置与不同控制模式分别说明。这些 HTML 是模型参考资料，不包含可直接运行的仿真软件。

| 设备 | 涵盖的建模内容 | 配置数 |
|---|---|---|
| [详细同步机](../../Multimodal/Alpaca%20Data/Apparatus/sg.html) | 六绕组电磁动态、转子运动、调速、励磁、PSS，以及对应配置的饱和与限幅。 | 3 |
| [构网 VSG](../../Multimodal/Alpaca%20Data/Apparatus/gfm_vsg.html) | 虚拟惯量与阻尼、功率/电压调节、电压电流环、LCL、直流母线、执行限幅和抗饱和。 | 4 |
| [构网 Droop](../../Multimodal/Alpaca%20Data/Apparatus/gfm_droop.html) | 功率滤波、P–f 下垂与电压/无功控制、内环、LCL 和直流母线动态，以及序分量控制变体。 | 3 |
| [构网 Matching](../../Multimodal/Alpaca%20Data/Apparatus/gfm_matching.html) | 直流电压匹配同步、能量平衡、电压电流调节、滤波及执行器动态。 | 3 |
| [构网 dVOC](../../Multimodal/Alpaca%20Data/Apparatus/gfm_dvoc.html) | 振荡器幅值与相位动态、功率调节、电气动态、内环及非线性限幅。 | 3 |
| [跟网 PQ](../../Multimodal/Alpaca%20Data/Apparatus/gfl_pq.html) | PLL 同步、有功无功外环、电流调节、LCL/直流母线、故障穿越和功率恢复。 | 4 |
| [跟网 PU](../../Multimodal/Alpaca%20Data/Apparatus/gfl_pu.html) | PLL、有功与交流电压调节、电流环、电气动态及故障支撑变体。 | 4 |
| [构网双馈风机](../../Multimodal/Alpaca%20Data/Apparatus/gfm_dfig.html) | 气动、双质量轴系、机组磁链、变流器控制、直流母线、桨距、crowbar/chopper 和故障支撑。 | 2 |
| [跟网双馈风机](../../Multimodal/Alpaca%20Data/Apparatus/gfl_dfig.html) | 风轮轴系与感应机动态、转子侧/网侧 PLL 与控制、桨距、crowbar 和故障恢复。 | 2 |
| [构网直驱永磁风机](../../Multimodal/Alpaca%20Data/Apparatus/gfm_pmsg.html) | 永磁机、机械动态、背靠背变流器与直流母线；VSG 或 Matching 控制、桨距和故障支撑。 | 4 |
| [跟网直驱永磁风机](../../Multimodal/Alpaca%20Data/Apparatus/gfl_pmsg.html) | 机侧转速电流控制、网侧 PLL 与直流电压调节、电磁动态、桨距和故障恢复。 | 2 |
| [数据中心负荷](../../Multimodal/Alpaca%20Data/Apparatus/data_center.html) | AFE–UPS–VSI–PSU 供电链、等效计算负荷、测量/执行动态及备用电池能量。 | 2 |
| [感应电机](../../Multimodal/Alpaca%20Data/Apparatus/induction_motor.html) | 定转子磁链、机械转速、负载转矩、电压测量、热状态指标及欠压保护。 | 2 |
| [交直流联络换流器](../../Multimodal/Alpaca%20Data/Apparatus/ic.html) | 交直流能量交换、PLL、滤波与直流侧动态；PQ、EQ、PU、EU 模式及序分量控制变体。 | 8 |

[设备目录](../../Multimodal/Alpaca%20Data/Apparatus/index.html) · [模型约定](../../Multimodal/Alpaca%20Data/Apparatus/model_conventions.html)

## 多模态基准统计

| 任务 | 简单 | 中等 | 困难 | 总数 | JSONL 批次 |
|---|---|---|---|---|---|
| 设备控制 | 76 | 593 | 366 | 1035 | 64 |
| 网络拓扑 | 38 | 222 | 134 | 394 | 25 |
| 合计 | 114 | 815 | 500 | 1429 | 89 |

统计来自当前版本的实际文件：1,429 条样本对应 1,429 张引用图片，分布在 89 个 JSONL 批次中。难度分类不等同于训练、验证和测试集划分。

| 补充数据 | 文件数 | 指令条数 |
|---|---|---|
| Network（JSON） | 32000 | 335517 |
| General Knowledge（JSON 示例） | 1 | 39 |

补充指令记录不计入多模态样本总数。Apparatus 当前包含 16 个 HTML 页面，包括目录和模型约定；General Knowledge 仅保留一个示例文件。

## 图片概览

每种任务、每个难度展示九张代表性图片，采用紧凑的 3 × 3 排列。设备控制占一行，网络拓扑占下一行，简单、中等、困难三个难度并排展示。点击概览图可查看高清大图；保留样本 ID，便于追溯。

### 设备控制

| 简单 | 中等 | 困难 |
|---|---|---|
| [![设备控制 · 简单](../assets/apparatus_easy.png)](../assets/apparatus_easy.png) | [![设备控制 · 中等](../assets/apparatus_medium.png)](../assets/apparatus_medium.png) | [![设备控制 · 困难](../assets/apparatus_hard.png)](../assets/apparatus_hard.png) |

### 网络拓扑

| 简单 | 中等 | 困难 |
|---|---|---|
| [![网络拓扑 · 简单](../assets/network_easy.png)](../assets/network_easy.png) | [![网络拓扑 · 中等](../assets/network_medium.png)](../assets/network_medium.png) | [![网络拓扑 · 困难](../assets/network_hard.png)](../assets/network_hard.png) |

## 构建初步规模的电力系统仿真软件

以 HTML 模型为规范，搭建初步规模的电力系统建模仿真工具：提取统一设备接口，保留单位、坐标系及限幅，将设备方程与网络约束联立，再实现初始化、时域积分和事件处理。适用于研究原型及 LLM 辅助模型实现，之后仍需独立开展工程验证。

### 与 PSCAD、PowerFactory 模型进行动态对齐

如果需要与 PSCAD、PowerFactory 等软件中的模型实现高精度动态对齐，可以将 TypicalApparatus 模型说明作为结构起点，采用 [Guo 与 Shi（2024）](https://doi.org/10.1109/CIEEC60922.2024.10583352) 和 [Shi、Guo 等（2026）](https://doi.org/10.1109/TSTE.2025.3621702) 中的方法，结合暂态数据和物理约束，通过模型辨识与符号回归获取模型方程的显式解析表达式。

辨识时应与参考模型保持单位、坐标系和边界条件一致，并在未参与辨识的运行点及扰动工况下，将暂态响应与参考软件进行比较，验证模型的泛化能力。相关实现代码可参考 [DSIPS — Dynamic Sparse Identification of Power System](https://github.com/gdg1999/DSIPS)。

## 提示词示例

### 1 · 从设备说明构建设备组件

```text
以所附 MINEGRID 构网 VSG HTML 模型为规范。先列出全部状态、代数量、输入、输出、参数、单位及坐标系，再设计 f(x,z,u;p)、g(x,z,u;p) 和端口注入电流的组件接口。保留文档中的全部限幅和抗饱和项。区分已提供数值与缺失信息，不得虚构参数。编写代码前，先给出实现计划和方程到代码的映射。
```

### 2 · 组建初步规模的动态仿真软件

```text
基于所附同步机、构网、跟网及负荷模型说明，设计三节点研究型仿真软件。定义统一基准、网络方程、设备接口和一致初值；加入小幅负荷变化事件，记录状态、电流和电压，并开展残差检查与步长收敛研究。列出文档未提供的网络参数和附加假设。明确区分已经实现的功能与尚未验证的行为。
```

## 评估 VLM 能力并研究其机制

- 能力评估：控制模块识别、反馈符号推理、状态辨识与 DAE 推导；网络图的母线支路提取、连通性识别和表格重建。
- 机制研究：开展提示词语言、分辨率、遮挡与符号位置的受控实验，区分视觉感知错误和物理推理错误；在模型内部信息可访问时分析注意力与激活。
- 评估流程：隔离参考答案，固定任务及难度分布，比较结构化输出与物理一致性，按共有论文或系统家族分组以减少来源泄漏。数学等价方程不宜仅靠文本完全匹配评分。

## 目录与标注格式

```text
JSON Index/
├── device_control_*/      # JSONL
└── network_topology_*/     # JSONL
Multimodal/
├── Alpaca Data/
│   ├── Apparatus/          # HTML
│   ├── Network/            # JSON
│   └── General Knowledge/  # JSON
├── apparatus_{easy,medium,hard}/
└── network_{easy,medium,hard}/
Scripts/
docs/
├── assets/
└── readme/
```

每条基准 JSONL 包含 id、image、conversations 和 annotations。图片路径相对于仓库根目录；助手回复的 value 需再解析一次 JSON 才得到答案对象。原始用户提示为中文，annotations 提供 en、es、ar、fr、ru 五种语言的提示。六种 README 语言不意味着有六套独立翻译的答案。补充 JSON 文件则是 instruction/input/output 记录数组。

[标注说明](../../JSON%20Index/README.md) · [评估说明](../../Scripts/LLM%20Evaluation/README.md)

## 论文引用

如果该资源支持了你的研究，请引用相关论文：

D. Guo, S. Li, X. Shi, S. Jiang, G. Konstantinou and Y. Cao, "A Large Language Model-Based Framework for Automated Dynamic Simulation of Power Systems," in *IEEE Transactions on Smart Grid*, doi: [10.1109/TSG.2026.3731592](https://doi.org/10.1109/TSG.2026.3731592).

```bibtex
@article{guo2026automated,
  author  = {Guo, D. and Li, S. and Shi, X. and Jiang, S. and Konstantinou, G. and Cao, Y.},
  title   = {A Large Language Model-Based Framework for Automated Dynamic Simulation of Power Systems},
  journal = {IEEE Transactions on Smart Grid},
  year    = {2026},
  doi     = {10.1109/TSG.2026.3731592}
}
```

暂态数据模型辨识与物理约束聚合的相关方法：

1. D. Guo and X. Shi, "Model Identification of Grid-following System for Stability Evaluation with Transient Data," *2024 IEEE 7th International Electrical and Energy Conference (CIEEC)*, Harbin, China, 2024, pp. 01–06, doi: [10.1109/CIEEC60922.2024.10583352](https://doi.org/10.1109/CIEEC60922.2024.10583352).

2. X. Shi, D. Guo *et al*., "Physical-Informed Detailed Aggregation of Wind Farm Based on Symbolic Regression: Structure, Solution and Generalizability," in *IEEE Transactions on Sustainable Energy*, vol. 17, no. 2, pp. 1511–1524, April 2026, doi: [10.1109/TSTE.2025.3621702](https://doi.org/10.1109/TSTE.2025.3621702).

```bibtex
@inproceedings{guo2024identification,
  author    = {Guo, D. and Shi, X.},
  title     = {Model Identification of Grid-following System for Stability Evaluation with Transient Data},
  booktitle = {2024 IEEE 7th International Electrical and Energy Conference (CIEEC)},
  address   = {Harbin, China},
  year      = {2024},
  pages     = {01--06},
  doi       = {10.1109/CIEEC60922.2024.10583352}
}

@article{shi2026aggregation,
  author  = {Shi, X. and Guo, D. and others},
  title   = {Physical-Informed Detailed Aggregation of Wind Farm Based on Symbolic Regression: Structure, Solution and Generalizability},
  journal = {IEEE Transactions on Sustainable Energy},
  volume  = {17},
  number  = {2},
  pages   = {1511--1524},
  month   = apr,
  year    = {2026},
  doi     = {10.1109/TSTE.2025.3621702}
}
```

## Minegrid 网页

**Minegrid 网页：正测试维护中…**
