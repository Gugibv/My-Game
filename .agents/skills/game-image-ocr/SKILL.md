---
name: game-image-ocr
description: >-
  Extracts card attributes, stats, and verbatim skill/tactic descriptions from game screenshots (specifically 率土之滨 and similar card/SLG strategy games) using native Apple Vision OCR and spatial coordinate bounding boxes. Use this skill whenever the user provides game screenshots, requests high-accuracy OCR of card panels, library tactics, or treasure panels, needs verbatim skill text extraction without summarization, or asks to batch process game screenshots into structured markdown or JSON catalogs.
---

# 游戏卡牌、战法库与宝物截图高精度空间 OCR 识别 (game-image-ocr)

本技能提供一套专为《率土之滨》等策略卡牌游戏打造的高性能、完全离线的图像识别与结构化提取方案。通过原生 Apple Vision 框架提取带有归一化坐标的文本包围盒，并结合游戏界面的空间几何排版规则，杜绝文字缩减、属性混淆与字段错位。

---

## 核心能力与适用范围

1. **武将卡牌与自带主战法**（[`scripts/parse_game_cards.py`](./scripts/parse_game_cards.py)）：
   - 提取五维成长（攻、防、谋、速、城 12级面板与每级成长），彻底解决双列与宽框混淆。
   - 自动映射纯数字红度 `0 ~ 5`。
   - 提取自带主战法品质、类型、距离、发动率、目标及逐字原文。
2. **战法库详情弹窗（武将战法清单）**（[`scripts/parse_library_tactics.py`](./scripts/parse_library_tactics.py)）：
   - 解析指挥、主动、被动、追击四大类型全量战法。
   - 严格限定正文提取空间，排除右侧滚动条字符（如 `出三`、`品出`、`出`、`皿`）。
   - 完整保留数值递增跨度（如 `150.0% » 300.0%`），补全遮挡的条件尾句。
3. **宝物与锻造词条（宝物清单）**（[`scripts/parse_treasures.py`](./scripts/parse_treasures.py)）：
   - 提取基础加成效果与进阶锻造词条（奇袭、英勇、破敌、机先、盛气、颖悟等）。
   - 提取淬火工匠名、淬火时间及已保护/未保护状态。
4. **离线极速运行**：
   - 采用 Swift 编译的原生 Apple Vision 引擎，单图识别耗时约 50ms，零外部依赖与 API 额度限制。

---

## 目录结构与快速参考

- **环境准备与编译工具**：[`scripts/setup_ocr.sh`](./scripts/setup_ocr.sh)
- **Swift Vision 源码**：[`scripts/ocr_boxes.swift`](./scripts/ocr_boxes.swift)
- **卡牌与自带战法解析引擎**：[`scripts/parse_game_cards.py`](./scripts/parse_game_cards.py)
- **战法库详情解析引擎**：[`scripts/parse_library_tactics.py`](./scripts/parse_library_tactics.py)
- **宝物详情解析引擎**：[`scripts/parse_treasures.py`](./scripts/parse_treasures.py)
- **批处理命令行工具**：[`scripts/batch_process.py`](./scripts/batch_process.py)
- **空间排版与坐标参考**：[`references/coordinate_layout_guide.md`](./references/coordinate_layout_guide.md)
- **字符纠错与异常处理**：[`references/error_correction_dictionary.md`](./references/error_correction_dictionary.md)

---

## 标准操作流程 (SOP)

### 步骤 1：检查并准备 OCR 执行环境

在首次调用或在新机器运行时，先执行准备脚本。该脚本会自动使用 `swiftc` 编译本地二进制工具：

```bash
bash .agents/skills/game-image-ocr/scripts/setup_ocr.sh
```

校验产物：`scripts/ocr_boxes_bin` 存在且具备可执行权限。

---

### 步骤 2：识别与分类处理

根据截图内容直接载入对应模块：

#### 1. 武将卡牌与主战法
```python
from parse_game_cards import get_ocr_boxes, extract_card_attributes, extract_skill_popup

card_boxes = get_ocr_boxes("path/to/card.png")
stats = extract_card_attributes(card_boxes)

skill_boxes = get_ocr_boxes("path/to/skill_popup.png")
skill = extract_skill_popup(skill_boxes, dname="武将名")
```

#### 2. 战法库详情弹窗
```python
from parse_library_tactics import parse_tactic_popup

boxes = get_ocr_boxes("path/to/library_tactic.png")
tactic_info = parse_tactic_popup(boxes)
# 产物: {'name': '桃园结义', 'quality': 'S', 'distance': '3', 'rate': '100%', 'target': '我军单体', 'description': '...'}
```

#### 3. 宝物面板
```python
from parse_treasures import parse_treasure_card

boxes = get_ocr_boxes("path/to/treasure.png")
treasure_info = parse_treasure_card(boxes)
# 产物: {'protection': '已保护', 'base_effects': '• **骁锐**：...', 'forge_effects': '• **奇袭**：...', 'artisan': '王响 于 2026/04/19 淬火'}
```

---

### 步骤 3：严格遵循校验与输出规范

1. **绝对字面一致（Verbatim）**：严禁修改或缩减战法描述，保留原图中的所有数值区间。
2. **符号与词条校对**：自动调用校正词典修复字体粘连（如 `政击` -> `攻击`、`元历` -> `亢厉`、`料擞` -> `抖擞`）。
3. **进度同步**：处理大批量图片时，定期向用户汇报各部分进度与完成比例。
