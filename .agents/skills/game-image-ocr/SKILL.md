---
name: game-image-ocr
description: >-
  Extracts card attributes, stats, and verbatim skill/tactic descriptions from game screenshots (specifically 率土之滨 and similar card/SLG strategy games) using native Apple Vision OCR and spatial coordinate bounding boxes. Use this skill whenever the user provides game screenshots, requests high-accuracy OCR of card panels or skill popups, needs verbatim skill text extraction without summarization, or asks to batch process game screenshots into structured markdown or JSON catalogs.
---

# 游戏卡牌与战法截图高精度空间 OCR 识别 (game-image-ocr)

本技能提供一套专为《率土之滨》等策略卡牌游戏打造的高性能、完全离线的图像识别与结构化提取方案。通过原生 Apple Vision 框架提取带有归一化坐标的文本包围盒，并结合游戏界面的空间几何排版规则，杜绝文字缩减、属性混淆与字段错位。

---

## 核心能力与优势

1. **绝对字面一致（Verbatim）**：完整提取战法详情弹窗中的技能效果原文，保留数值成长标记（如 `150.0% » 300.0%`），严禁任何人工概括与删减。
2. **五维空间几何对齐**：使用双列空间锚定，解决攻城与速度成长交换、宽文本框跨列合并等疑难问题。
3. **红度规范化**：自动将卡牌进阶红星识别并映射为纯数字 `0 ~ 5`（0 为白板，1~4 为进阶红度，5 为满红）。
4. **离线极速处理**：基于 macOS 原生 Vision 框架（Swift 编译），单图解析仅需 ~50ms，零网络依赖与额度消耗。

---

## 目录结构与快速参考

- **环境准备与编译工具**：[`scripts/setup_ocr.sh`](./scripts/setup_ocr.sh)
- **Swift Vision 源码**：[`scripts/ocr_boxes.swift`](./scripts/ocr_boxes.swift)
- **卡牌与战法解析引擎**：[`scripts/parse_game_cards.py`](./scripts/parse_game_cards.py)
- **批处理命令行工具**：[`scripts/batch_process.py`](./scripts/batch_process.py)
- **空间排版与坐标参考**：[`references/coordinate_layout_guide.md`](./references/coordinate_layout_guide.md)
- **字符纠错与异常处理**：[`references/error_correction_dictionary.md`](./references/error_correction_dictionary.md)
- **标准输出样例**：[`examples/sample_output.json`](./examples/sample_output.json)

---

## 标准操作流程 (SOP)

### 步骤 1：检查并准备 OCR 执行环境

在首次调用或在新机器运行时，先执行准备脚本。该脚本会自动使用 `swiftc` 编译本地二进制工具：

```bash
bash .agents/skills/game-image-ocr/scripts/setup_ocr.sh
```

校验产物：`scripts/ocr_boxes_bin` 存在且具备可执行权限。

---

### 步骤 2：对截图进行分类与配对

1. **卡牌属性图**：包含武将立绘、等级、攻击/防御/谋略/速度/攻城基础属性及成长。
2. **战法详情弹窗图**：点击自带战法后弹出的半透明黑底弹窗，包含战法类型、距离、发动率、目标群体及满级效果。
3. 按照图片时间戳或武将名成对匹配（1 张卡牌图 + 1 张对应战法弹窗图）。

---

### 步骤 3：调用解析引擎提取结构化数据

在 Python 中引入解析模块：

```python
import sys
sys.path.append(".agents/skills/game-image-ocr/scripts")
from parse_game_cards import get_ocr_boxes, extract_card_attributes, extract_skill_popup

# 1. 提取卡牌面板五维属性
card_boxes = get_ocr_boxes("path/to/card_screenshot.png")
stats_str = extract_card_attributes(card_boxes)
# 产物格式: 攻 121 (+2.16) 防 111 (+1.87) 谋 72 (+0.65) 速 114 (+1.68) 城 10 (+0.42)

# 2. 提取自带主战法详情
skill_boxes = get_ocr_boxes("path/to/skill_popup.png")
skill_data = extract_skill_popup(skill_boxes, dname="武将名")
# 产物格式: 【战法名】（类型 · 距离X · 发动率XX% · 目标类型：XXX）战法描述完全一致的原文...
```

---

### 步骤 4：严格遵循字段校验与排版规则

在写入 Markdown 清单或文档时，必须执行以下核查：
1. **红度列**：必须为纯数字 `0`, `1`, `2`, `3`, `4`, `5`，不得包含汉字或星号符号。
2. **五维属性**：确保每项属性均包含 `(12级基础 / 每级成长)` 且无一遗漏（`攻 / 防 / 谋 / 速 / 城`）。
3. **战法正文**：
   - 包含数值成长跨度（使用 `»` 连接，如 `150.0% » 300.0%`）。
   - 禁止添加评语（如“菜刀队核心”、“开荒神将”等）。
   - 若遇到字符识别偏差，严格对照 [`references/error_correction_dictionary.md`](./references/error_correction_dictionary.md) 执行修正。

---

### 步骤 5：批量处理与进度同步

当处理数十或上百张大批量图片时：
- 采用多线程或按批次处理，并定期向用户同步处理进度（例如每完成 15~20 位武将输出一次进度百分比与当前处理阵营）。
- 处理完成后进行全量 `-` 占位符排查，确保零空缺、零混淆后提交或写入文档。
