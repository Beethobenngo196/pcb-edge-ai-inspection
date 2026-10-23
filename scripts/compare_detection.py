# -*- coding: utf-8 -*-
"""
scripts/compare_detection.py
So sánh kết quả detection (log) với ground-truth CSV.

Cách dùng (chạy từ thư mục gốc project):
    python scripts/compare_detection.py

Sinh ra:
    evaluation/comparison_stats.csv   — TP, FP, FN, precision, recall, f1
    evaluation/detailed_match.csv     — chi tiết từng detection
"""

import csv
import math
import os
import re

# --- Cấu hình ---
GT_PATH      = "evaluation/ground_truth.csv"
LOG_DIR      = "logs"
STATS_PATH   = "evaluation/comparison_stats.csv"
DETAIL_PATH  = "evaluation/detailed_match.csv"
DIST_THRESH  = 30   # Pixel — tolerance khoảng cách để coi là match


# ── Tìm log mới nhất ──────────────────────────────────────────────────────────
def find_latest_log(log_dir):
    logs = sorted(
        [f for f in os.listdir(log_dir) if f.startswith("log_") and f.endswith(".txt")],
        reverse=True,
    )
    if not logs:
        raise FileNotFoundError(f"Không tìm thấy file log nào trong '{log_dir}'")
    return os.path.join(log_dir, logs[0])


# ── Load ground-truth ─────────────────────────────────────────────────────────
def load_ground_truth(path):
    gt = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            gt.append({
                "frame":   row["frame"],
                "class":   row["class"],
                "x":       int(row["x"]),
                "y":       int(row["y"]),
                "matched": False,
            })
    return gt


# ── Load detection log ────────────────────────────────────────────────────────
# Định dạng mới: ... | cx_px=<int> cy_px=<int> | X=<int> Y=<int> | ...
PATTERN = re.compile(
    r"\[(?P<time>[^\]]+)\] PHAT HIEN: "
    r"ma=\d+ \| ten=(?P<class>[^|]+) \| "
    r"cx_px=(?P<cx>\d+) cy_px=(?P<cy>\d+) \| "
    r"X=\d+ Y=\d+ \| "
    r"conf=(?P<conf>[0-9.]+) \| track_id=(?P<tid>\S+)"
)

def load_log(path):
    detections = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            m = PATTERN.search(line)
            if m:
                detections.append({
                    "time":     m.group("time"),
                    "class":    m.group("class").strip(),
                    "x":        int(m.group("cx")),   # pixel gốc
                    "y":        int(m.group("cy")),   # pixel gốc
                    "conf":     float(m.group("conf")),
                    "track_id": m.group("tid"),
                })
    return detections


# ── So sánh ───────────────────────────────────────────────────────────────────
def compare(gt, detections, dist_thresh=DIST_THRESH):
    tp = fp = 0
    detailed = []

    for det in detections:
        best = None
        best_dist = None
        for g in gt:
            if g["matched"]:
                continue
            if g["class"] != det["class"]:
                continue
            d = math.hypot(det["x"] - g["x"], det["y"] - g["y"])
            if d <= dist_thresh and (best is None or d < best_dist):
                best = g
                best_dist = d

        if best:
            tp += 1
            best["matched"] = True
            match = "TP"
        else:
            fp += 1
            match = "FP"

        detailed.append({
            "time":     det["time"],
            "class":    det["class"],
            "cx_px":    det["x"],
            "cy_px":    det["y"],
            "conf":     det["conf"],
            "track_id": det["track_id"],
            "match":    match,
            "dist":     f"{best_dist:.1f}" if best_dist is not None else "",
        })

    fn        = sum(1 for g in gt if not g["matched"])
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall    = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1        = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    return {"TP": tp, "FP": fp, "FN": fn, "precision": precision, "recall": recall, "f1": f1}, detailed


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    log_path = find_latest_log(LOG_DIR)
    print(f"[INFO] Dùng log: {log_path}")

    gt         = load_ground_truth(GT_PATH)
    detections = load_log(log_path)

    if not detections:
        print("[CANH BAO] Không parse được detection nào từ log.")
        print("           Kiểm tra định dạng log có khớp PATTERN không.")
        exit(1)

    print(f"[INFO] Ground-truth: {len(gt)} điểm | Detections: {len(detections)}")

    stats, detailed = compare(gt, detections, dist_thresh=DIST_THRESH)

    os.makedirs("evaluation", exist_ok=True)

    with open(STATS_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["metric", "value"])
        for k, v in stats.items():
            w.writerow([k, v])

    with open(DETAIL_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["time", "class", "cx_px", "cy_px", "conf", "track_id", "match", "dist"])
        w.writeheader()
        w.writerows(detailed)

    print("\n========== KẾT QUẢ ĐÁNH GIÁ ==========")
    print(f"  TP  : {stats['TP']}")
    print(f"  FP  : {stats['FP']}")
    print(f"  FN  : {stats['FN']}")
    print(f"  Precision : {stats['precision']:.4f} ({stats['precision']*100:.1f}%)")
    print(f"  Recall    : {stats['recall']:.4f} ({stats['recall']*100:.1f}%)")
    print(f"  F1        : {stats['f1']:.4f} ({stats['f1']*100:.1f}%)")
    print("========================================")
    print(f"\n[OK] Stats  -> {STATS_PATH}")
    print(f"[OK] Detail -> {DETAIL_PATH}")

