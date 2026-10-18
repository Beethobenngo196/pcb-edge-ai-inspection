# -*- coding: utf-8 -*-
"""Generate ground‑truth CSV from YOLO label files.
The script scans all *.txt files under `dataset/labels` (including subfolders),
converts normalized bbox centers to pixel coordinates using the camera size
from `pcb_edge_vision/configs/settings.yaml`, and writes a CSV with columns:
    frame, class, x, y
"""
import os, csv, yaml, math

# Load config to get camera resolution (fallback to 1280x720)
cfg_path = "pcb_edge_vision/configs/settings.yaml"
with open(cfg_path, "r", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)
frame_w = 1280
frame_h = 720  # Video resolution used by main.py

# Class name mapping – must match the model's ordering
class_names = ["missing_hole", "mouse_bite", "open_circuit", "short", "spur", "spurious_copper"]

label_root = r"d:\\pcb-edge-ai-inspection\\dataset\\labels"
out_path = r"d:\\pcb-edge-ai-inspection\\ground_truth.csv"

with open(out_path, "w", newline="", encoding="utf-8") as fout:
    writer = csv.writer(fout)
    writer.writerow(["frame", "class", "x", "y"])
    for root, _, files in os.walk(label_root):
        for fname in files:
            if not fname.lower().endswith('.txt'):
                continue
            frame_id = os.path.splitext(fname)[0]
            txt_path = os.path.join(root, fname)
            with open(txt_path, "r", encoding="utf-8") as fin:
                for line in fin:
                    parts = line.strip().split()
                    if len(parts) < 5:
                        continue
                    cid = int(parts[0])
                    xc, yc, w, h = map(float, parts[1:5])
                    # Convert normalized centre to pixel coordinates
                    x = int(xc * frame_w)
                    y = int(yc * frame_h)
                    writer.writerow([frame_id, class_names[cid], x, y])
print("Ground‑truth CSV saved to:", out_path)

