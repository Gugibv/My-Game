#!/usr/bin/env python3
# coding: utf-8
"""
parse_library_tactics.py - Library Tactics Popup Parser

Specialized parser for game library tactics screenshots (战法库详情弹窗):
- Tactic Name (y ~ 0.826, x ~ 0.66)
- Quality (S / A / B)
- Distance (有效距离 1~5 / --)
- Trigger Rate (发动率, e.g. 35%, 100%)
- Target Type (目标类型, e.g. 敌军群体/我军单体)
- Verbatim Description (bounded, filtered of right-side scrollbar artifacts)
"""

import re
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from parse_game_cards import clean_ocr_text, get_ocr_boxes

TITLE_ALIAS = {
    '无心恋': '无心恋战',
    '战火断金': '战必断金',
    '知己知波': '知己知彼',
    '乌云山兵': '乌云山兵',
    '鸟云山兵': '乌云山兵',
    '一骑当干': '一骑当千',
    '三米奇谋': '三术奇谋',
    '兼弱攻味': '兼弱攻昧',
    '铁戟金女': '铁戟金戈',
    '蓄盈诗竭': '蓄盈待竭',
    '増援': '增援',
    '车是': '车悬',
    '垒实迎击': '垒石迎击',
    '是权而动': '量权而动',
    '深谋远處': '深谋远虑',
    '胜负先证': '胜负先征',
    '百战无': '百战无怯'
}


def clean_tactic_desc(text: str) -> str:
    text = clean_ocr_text(text)
    text = text.replace('政击', '攻击').replace('课略', '谋略').replace('故军', '敌军')
    text = text.replace('»>', '»').replace('》', '»').replace('>', '»')
    text = text.replace('品出', '').replace('出三', '').replace('出皿', '')
    if text.endswith('出') or text.endswith('三') or text.endswith('品') or text.endswith('皿'):
        text = text[:-1]
    if text.endswith('持续1'):
        text += '回合'
    return text.strip()


def parse_tactic_popup(boxes):
    """Parse tactic details from OCR boxes."""
    # 1. Title at y ~ 0.82
    title_box = [b[4] for b in boxes if 0.80 <= b[1] <= 0.85 and 0.60 <= b[0] <= 0.85]
    raw_name = ""
    if title_box:
        t_raw = title_box[0]
        m = re.search(r'([^\s:：]+?)\s*L[vV]', t_raw)
        raw_name = m.group(1) if m else t_raw.split()[0]
    tname = TITLE_ALIAS.get(raw_name, raw_name)

    # 2. Quality
    q_box = [b[4] for b in boxes if 0.78 <= b[1] <= 0.85 and 0.15 <= b[0] <= 0.22]
    quality = q_box[0].strip() if q_box else "S"
    if quality not in ['S', 'A', 'B']:
        quality = "S"

    # 3. Distance
    dist_box = [b[4] for b in boxes if 0.75 <= b[1] <= 0.79 and 0.65 <= b[0] <= 0.78]
    d_text = ''.join(dist_box).replace('ll', '--').replace('11', '--')
    m_dist = re.search(r'([1-5]|--) ', d_text + ' ')
    sdist = m_dist.group(1).strip() if m_dist else "-"

    # 4. Trigger rate
    rate_box = [b[4] for b in boxes if 0.75 <= b[1] <= 0.79 and 0.78 <= b[0] <= 0.96]
    r_text = ''.join(rate_box).replace('发动率', '').strip()
    m_rate = re.search(r'([0-9]+%?(?:\s*[»>》]\s*[0-9]+%?)?)', r_text)
    if m_rate:
        rate = m_rate.group(1).replace(' ', '').replace('>', '»').replace('》', '»')
        if not rate.endswith('%') and not rate.endswith('-'):
            rate += '%'
    else:
        rate = "-"

    # 5. Target type
    target_box = [b[4] for b in boxes if 0.65 <= b[1] <= 0.70 and 0.65 <= b[0] <= 0.96]
    t_text = ''.join(target_box).replace('目标类型', '').replace('类型', '').replace('故军', '敌军').strip()
    target = t_text if t_text else "-"

    # 6. Description (exclude scrollbar at x > 0.96)
    d_boxes = [b for b in boxes if 0.28 <= b[1] <= 0.59 and 0.65 <= b[0] <= 0.96]
    d_boxes.sort(key=lambda b: -b[1])
    lines = []
    for b in d_boxes:
        txt = b[4].strip()
        if txt in ['战法描述', '简', '详', '简详', '简 详']:
            continue
        if any(k in txt for k in ['查看详情', '攻略', '拆解战法', 'X', '132/300']):
            continue
        lines.append(txt)
    desc = clean_tactic_desc(''.join(lines))

    return {
        'name': tname,
        'quality': quality,
        'distance': sdist,
        'rate': rate,
        'target': target,
        'description': desc
    }
