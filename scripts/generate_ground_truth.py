# -*- coding: utf-8 -*-
"""
scripts/generate_ground_truth.py
Sinh ground_truth.csv từ YOLO label files trong dataset.

Cách dùng (chạy từ thư mục gốc project):
    python scripts/generate_ground_truth.py

Output:
    evaluation/ground_truth.csv — frame, class, x, y (hệ pixel 1280×720)
"""

import csv
import os

# Độ phân giải video khớp với pcb_conveyor_simulation_v2.mp4
FRAME_W = 1280
FRAME_H = 720

# Tên lớp phải khớp đúng thứ tự với model (data.yaml)
CLASS_NAMES = ["missing_hole", "mouse_bite", "open_circuit", "short", "spur", "spurious_copper"]

LABEL_ROOT = "dataset/labels"
OUT_PATH   = "evaluation/ground_truth.csv"


def main():
    os.makedirs("evaluation", exist_ok=True)
    count = 0

    with open(OUT_PATH, "w", newline="", encoding="utf-8") as fout:
        writer = csv.writer(fout)
        writer.writerow(["frame", "class", "x", "y"])

        for root, _, files in os.walk(LABEL_ROOT):
            for fname in sorted(files):
                if not fname.lower().endswith(".txt"):
                    continue
                frame_id = os.path.splitext(fname)[0]
                txt_path = os.path.join(root, fname)

                with open(txt_path, "r", encoding="utf-8") as fin:
                    for line in fin:
                        parts = line.strip().split()
                        if len(parts) < 5:
                            continue
                        cid = int(parts[0])
                        xc, yc = float(parts[1]), float(parts[2])
                        x = int(xc * FRAME_W)
                        y = int(yc * FRAME_H)
                        writer.writerow([frame_id, CLASS_NAMES[cid], x, y])
                        count += 1

    print(f"[OK] Ground-truth saved: {OUT_PATH} ({count} điểm)")


if __name__ == "__main__":
    main()

