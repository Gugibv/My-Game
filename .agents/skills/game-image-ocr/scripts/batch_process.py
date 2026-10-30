#!/usr/bin/env python3
# coding: utf-8
"""
batch_process.py - Batch Processor for Game Screenshots

Usage:
  python3 batch_process.py --img-dir /path/to/images --output-json /path/to/out.json
"""

import os
import sys
import argparse
import json
from concurrent.futures import ThreadPoolExecutor

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from parse_game_cards import get_ocr_boxes, extract_card_attributes, extract_skill_popup


def process_card_pair(gen_path, skill_path, dname="", camp=""):
    gen_boxes = get_ocr_boxes(gen_path)
    stats_str = extract_card_attributes(gen_boxes)

    skill_boxes = get_ocr_boxes(skill_path)
    skill_info = extract_skill_popup(skill_boxes, dname)

    return {
        'display_name': dname,
        'camp': camp,
        'stats': stats_str,
        'skill_cell': skill_info['full_cell'],
        'skill_meta': {
            'name': skill_info['skill_name'],
            'type': skill_info['type'],
            'distance': skill_info['distance'],
            'rate': skill_info['rate'],
            'target': skill_info['target'],
            'description': skill_info['description']
        }
    }


def main():
    parser = argparse.ArgumentParser(description="Batch process game screenshots.")
    parser.add_argument("--img-dir", required=True, help="Directory containing screenshot images")
    parser.add_argument("--output-json", help="Path to write JSON results")
    args = parser.parse_args()

    if not os.path.isdir(args.img_dir):
        print(f"Error: Directory not found: {args.img_dir}")
        sys.exit(1)

    print(f"Scanning images in: {args.img_dir}...")
    files = sorted([f for f in os.listdir(args.img_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
    print(f"Total images found: {len(files)}")


if __name__ == "__main__":
    main()
