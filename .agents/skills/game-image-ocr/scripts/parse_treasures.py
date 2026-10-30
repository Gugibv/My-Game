#!/usr/bin/env python3
# coding: utf-8
"""
parse_treasures.py - Game Treasure Screenshot Parser

Specialized parser for treasure screenshots (宝物详情面板):
- Treasure Name (彤素, 屈卢, 别鸣...)
- Protection Status (已保护 / 未保护)
- Weapon Type (弓, 枪/矛, 刀, 剑, 扇, 连弩...)
- Base Effects (基础效果与加成: 骁锐, 稳固, 亢厉...)
- Forging Effects (锻造词条及效果: 奇袭, 英勇, 破敌, 盛气, 避险...)
- Artisan & Quenching Info (工匠与淬火时间)
"""

import re
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from parse_game_cards import clean_ocr_text, get_ocr_boxes

KNOWN_TITLES = [
    '骁锐', '稳固', '天资', '灵动', '安贞', '强韧', '陷阵', '破敌', '先知', '不移', '亢厉', '妙算', '无畏',
    '奇袭', '英勇', '坚忍', '盛气', '英才', '机敏', '筹算', '仁心', '抖擞', '艮止', '颖悟', '谋断', '护主', '避险', '穿杨', '迸发', '不屈', '沉稳'
]


def parse_treasure_card(boxes):
    """Extract treasure structured data from OCR bounding boxes."""
    # 1. Protection Status
    prot = '已保护' if any('已保护' in b[4] for b in boxes) else '未保护'

    # 2. Artisan & Date
    artisan = '活动限定（不可交易/拆解/进阶）'
    for b in boxes:
        if '淬火而成' in b[4] or '淬火' in b[4]:
            t_str = b[4].strip()
            m = re.search(r'([^\s]+?)\s*于\s*([0-9/]+)\s*淬火', t_str)
            if m:
                artisan = f"{m.group(1)} 于 {m.group(2)} 淬火"
            else:
                artisan = t_str.replace('而成', '')
            break

    # 3. Effects panel: x between 0.60 and 0.88, y between 0.38 and 0.66
    effect_boxes = [b for b in boxes if 0.38 <= b[1] <= 0.66 and 0.60 <= b[0] <= 0.88]
    effect_boxes.sort(key=lambda b: -b[1])

    def parse_section(sec_boxes):
        entries = []
        cur_t = None
        cur_d = []
        for b in sec_boxes:
            x, y, w, h, text = b
            text = text.strip().replace('抢', '').replace('俉', '').replace('伍', '').replace('侄', '')
            text = text.replace('元历', '亢厉').replace('六厉', '亢厉').replace('无長', '无畏').replace('抖緻', '抖擞').replace('料擞', '抖擞')
            text = text.replace('政击', '攻击').replace('课略', '谋略').replace('；', '').replace('》', '')
            if not text or text in ['强化', '宝物效果', '稀世', '精品', '罕俦']:
                continue

            is_title = (x < 0.65 and len(text) <= 4) or any(text.startswith(kt) for kt in KNOWN_TITLES)
            if is_title:
                if cur_t:
                    entries.append((cur_t, ''.join(cur_d).strip()))
                matched_kt = None
                for kt in KNOWN_TITLES:
                    if text.startswith(kt):
                        matched_kt = kt
                        break
                if matched_kt:
                    cur_t = matched_kt
                    rem = text[len(matched_kt):].strip()
                    cur_d = [rem] if rem else []
                else:
                    cur_t = text
                    cur_d = []
            else:
                cur_d.append(text)

        if cur_t:
            entries.append((cur_t, ''.join(cur_d).strip()))

        formatted = []
        for t, d in entries:
            d = d.lstrip(' :：')
            formatted.append(f"• **{t}**：{d}")
        return '<br>'.join(formatted)

    base_b = [b for b in effect_boxes if b[1] >= 0.54]
    forge_b = [b for b in effect_boxes if b[1] < 0.54]

    return {
        'protection': prot,
        'base_effects': parse_section(base_b),
        'forge_effects': parse_section(forge_b),
        'artisan': artisan
    }
