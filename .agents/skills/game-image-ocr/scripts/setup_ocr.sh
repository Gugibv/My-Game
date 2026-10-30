#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_PATH="${SCRIPT_DIR}/ocr_boxes_bin"
SRC_PATH="${SCRIPT_DIR}/ocr_boxes.swift"

if [ -f "${BIN_PATH}" ]; then
    echo "[setup_ocr] Found existing binary: ${BIN_PATH}"
else
    echo "[setup_ocr] Compiling ${SRC_PATH} -> ${BIN_PATH} ..."
    swiftc -O "${SRC_PATH}" -o "${BIN_PATH}"
    chmod +x "${BIN_PATH}"
    echo "[setup_ocr] Compilation successful."
fi

# Verify binary works
if "${BIN_PATH}" > /dev/null 2>&1; [ $? -eq 1 ]; then
    echo "[setup_ocr] OCR binary verified and ready to use."
else
    echo "[setup_ocr] Warning: unexpected exit code during dry-run."
fi
