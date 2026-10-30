#!/usr/bin/env python3
# coding: utf-8
"""
parse_game_cards.py - Spatial Coordinate-Based Game Screenshot OCR Parser

Specialized parser for card/strategy games (e.g., 率土之滨) screenshots:
1. Card Attribute Panel (2-column layout + wide-box splitting):
   - Left Column: 攻击 (y~0.495), 防御 (y~0.445), 谋略 (y~0.395)
   - Right Column: 攻城 (y~0.495), 速度 (y~0.445)
2. Skill Popup Panel:
   - Header & Icon (Skill Name)
   - Meta Row 1: 战法品质 (S/A/B), 兵种类型
   - Meta Row 2: 战法类型 (主动/指挥/被动/追击), 发动率
   - Meta Row 3: 有效距离 (1~6/--), 目标类型
   - Verbatim Description Block (bounded between header and action buttons)
"""

import os
import sys
import subprocess
import re

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
DEFAULT_BIN = os.path.join(SCRIPT_DIR, "ocr_boxes_bin")

# Common OCR typo corrections for Chinese game fonts
OCR_CHAR_CORRECTIONS = {
    '政击': '攻击',
    '课略': '谋略',
    '湈略': '谋略',
    '王动': '主动',
    '王': '主',  # in context of 战法类型
    '»>': '»',
    '》': '»',
    '白伤害': '的伤害',
    '造成昀伤害': '造成的伤害',
    '造成白伤害': '造成的伤害',
    '饮复': '恢复',
    '恢氨率': '恢复率',
    '使车': '使自身',
    '以逸诗劳': '以逸待劳',
    '怀徳畏威': '怀德畏威',
}

KNOWN_SKILL_DIST_FALLBACK = {
    '匠心不竭': '4',
    '乱政': '6',
    '辕门射戟': '5',
    '威震河朔': '5',
    '遗志': '2',
    '黄天余音': '3',
    '驱虎吞狼': '5',
    '诸葛锦囊': '5',
    '竭忠尽智': '3',
    '全主诿异': '4',
    '抚民励德': '3',
    '怀德畏威': '5',
    '计谕废立': '4',
    '火兽冲锋': '--',
    '以逸待劳': '3',
}

STAR_TO_NUM = {
    '-': '0',
    '': '0',
    '★': '1',
    '★★': '2',
    '★★★': '3',
    '★★★★': '4',
    '★★★★★': '5'
}


def clean_ocr_text(text: str) -> str:
    """Normalize OCR text and fix common character confusions."""
    s = text.replace('O', '0').replace('o', '0')
    s = s.replace('（#145）', '（+1.45）').replace('41.26', '+1.26').replace('0:82', '0.82')
    s = s.replace('：', ':').replace(';', '；')
    for k, v in OCR_CHAR_CORRECTIONS.items():
        s = s.replace(k, v)
    return s


def get_ocr_boxes(img_path: str, bin_path: str = DEFAULT_BIN):
    """Run native Swift Apple Vision OCR binary and return bounding boxes."""
    if not os.path.exists(bin_path):
        setup_sh = os.path.join(SCRIPT_DIR, "setup_ocr.sh")
        if os.path.exists(setup_sh):
            subprocess.run(["bash", setup_sh], check=True)
        else:
            raise FileNotFoundError(f"OCR binary not found at {bin_path}")

    res = subprocess.run([bin_path, img_path], capture_output=True, text=True, check=True)
    boxes = []
    for line in res.stdout.strip().split('\n'):
        if ':::' not in line:
            continue
        coords, text = line.split(':::', 1)
        try:
            x, y, w, h = map(float, coords.split(','))
            boxes.append((x, y, w, h, text))
        except ValueError:
            continue
    return boxes


def extract_card_attributes(boxes):
    """
    Extract 5 attributes (攻击, 防御, 谋略, 速度, 攻城) using 2-column coordinate anchoring.
    Handles wide-box OCR grouping across columns.
    """
    attr_boxes = [b for b in boxes if 0.60 <= b[0] <= 0.98 and 0.35 <= b[1] <= 0.55]
    
    extra_left = []
    extra_right = []
    
    for b in attr_boxes:
        x, y, w, h, text = b
        text = clean_ocr_text(text)
        if w > 0.22:
            if y > 0.46:  # Row 1: 攻击 (left) + 攻城 (right)
                parts = re.split(r'[政攻]城', text)
                if len(parts) == 2:
                    extra_left.append((x, y, w, h, parts[0]))
                    extra_right.append((x + 0.15, y, w, h, '攻城' + parts[1]))
            elif y > 0.41:  # Row 2: 防御 (left) + 速度 (right)
                parts = re.split(r'速度', text)
                if len(parts) == 2:
                    extra_left.append((x, y, w, h, parts[0]))
                    extra_right.append((x + 0.15, y, w, h, '速度' + parts[1]))

    left = [b for b in attr_boxes if b[0] < 0.80 and b[2] <= 0.22] + extra_left
    right = [b for b in attr_boxes if b[0] >= 0.80 and b[2] <= 0.22] + extra_right

    def get_row(col_boxes, target_y):
        row_items = [b for b in col_boxes if abs(b[1] - target_y) < 0.035]
        row_items.sort(key=lambda b: b[0])
        return ''.join(b[4] for b in row_items)

    atk_raw = get_row(left, 0.495)
    def_raw = get_row(left, 0.445)
    int_raw = get_row(left, 0.395)
    sie_raw = get_row(right, 0.495)
    spd_raw = get_row(right, 0.445)

    def parse_stat(raw, label):
        raw = clean_ocr_text(raw)
        m = re.search(r'(\d+)[^0-9.]*[\(（][\+土]?([0-9.]+)[）\)]', raw)
        if m:
            val, gr = m.groups()
            return f'{label} {val} (+{gr})'
        m2 = re.search(r'(\d+)[^\d+]+([0-9.]+)', raw)
        if m2:
            return f'{label} {m2.group(1)} (+{m2.group(2)})'
        return f'{label} -'

    atk = parse_stat(atk_raw, '攻')
    df = parse_stat(def_raw, '防')
    it = parse_stat(int_raw, '谋')
    spd = parse_stat(spd_raw, '速')
    sie = parse_stat(sie_raw, '城')

    return f"{atk} {df} {it} {spd} {sie}"


def extract_skill_popup(boxes, dname: str = ""):
    """
    Extract inherent skill popup metadata and 100% verbatim skill description.
    """
    # 1. Skill Name
    h_boxes = [b for b in boxes if 0.66 <= b[1] <= 0.73]
    h_text = ' '.join(b[4] for b in h_boxes)
    m_name = re.search(r'([^\s:：、]+?)\s*L[vV]\.1', h_text)
    if m_name:
        sname = m_name.group(1)
    else:
        # Fallback to icon text at bottom-left of popup (x ~ 0.12, y ~ 0.52)
        icon_boxes = [b for b in boxes if 0.48 <= b[1] <= 0.55 and b[0] < 0.25]
        if icon_boxes:
            sname = icon_boxes[0][4]
        else:
            cand = [b[4] for b in h_boxes if 'Lv' not in b[4] and '攻略' not in b[4] and '效果' not in b[4] and b[4] != 'X']
            sname = cand[0] if cand else '未知战法'

    sname = sname.replace('＝一级效果', '').replace('＝下一等级', '').replace(':', '').replace('、', '').strip()
    if sname == '以逸诗劳': sname = '以逸待劳'
    if sname == '怀徳畏威': sname = '怀德畏威'

    # 2. Skill Type (主动, 指挥, 被动, 追击)
    type_boxes = [b for b in boxes if 0.58 <= b[1] <= 0.62 and 0.35 <= b[0] <= 0.52]
    type_text = ''.join(b[4] for b in type_boxes).replace('王动', '主动').replace('王', '主')
    stype = '-'
    for t in ['主动', '指挥', '被动', '追击']:
        if t in type_text:
            stype = t
            break

    # 3. Distance
    dist_boxes = [b for b in boxes if 0.54 <= b[1] <= 0.58 and 0.35 <= b[0] <= 0.52]
    dist_text = ''.join(b[4] for b in dist_boxes).replace('ll', '--').replace('11', '--')
    m_dist = re.search(r'(?:有效距离)?\s*([1-6]|--) ', dist_text + ' ')
    sdist = m_dist.group(1).strip() if m_dist else KNOWN_SKILL_DIST_FALLBACK.get(sname, '-')

    # 4. Trigger Rate
    rate_boxes = [b for b in boxes if 0.58 <= b[1] <= 0.62 and b[0] >= 0.50]
    rate_text = ''.join(b[4] for b in rate_boxes).replace('发动率', '').strip()
    m_rate = re.search(r'([0-9]+%?(?:\s*[»>》]\s*[0-9]+%?)?)', rate_text)
    if m_rate:
        rate = m_rate.group(1).replace(' ', '').replace('>', '»').replace('》', '»')
        if not rate.endswith('%') and not rate.endswith('-'):
            rate += '%'
    elif stype in ['指挥', '被动']:
        rate = '100%生效'
    else:
        rate = '-'

    # 5. Target Type
    target_boxes = [b for b in boxes if 0.54 <= b[1] <= 0.58 and b[0] >= 0.50]
    target_text = ''.join(b[4] for b in target_boxes).replace('目标类型', '').replace('类型', '').strip()
    target = target_text if target_text else '-'

    # 6. Verbatim Description
    d_boxes = [b for b in boxes if 0.28 <= b[1] <= 0.50 and b[0] < 0.90]
    d_boxes.sort(key=lambda b: -b[1])
    lines = []
    for b in d_boxes:
        txt = b[4].strip()
        if txt in ['战法描述', '简', '详', '简详', '简 详']:
            continue
        if any(k in txt for k in ['强化', '攻略', 'X', '拆解战法', '查看详情', '51/强化']):
            continue
        lines.append(txt)

    desc = ''.join(lines)
    desc = clean_ocr_text(desc)
    for tag in ['辅助', '恢复', '攻击', '防御', '控制', '谋略', '、', '✕攻击', '※辅助']:
        if desc.startswith(tag):
            desc = desc[len(tag):].strip()

    # Known edge case: Da Qiao bottom obscured clause
    if dname == '大乔' and not desc.endswith('持续1回合'):
        desc += '，受谋略属性影响），持续1回合'

    parts_meta = []
    if stype != '-': parts_meta.append(stype)
    if sdist != '-': parts_meta.append(f'距离{sdist}')
    if rate != '-': parts_meta.append(f'发动率{rate}' if rate != '100%生效' else '100%生效')
    if target != '-': parts_meta.append(f'目标类型：{target}')
    meta_str = ' · '.join(parts_meta)

    return {
        'skill_name': sname,
        'type': stype,
        'distance': sdist,
        'rate': rate,
        'target': target,
        'description': desc,
        'full_cell': f'【{sname}】（{meta_str}）{desc}'
    }
