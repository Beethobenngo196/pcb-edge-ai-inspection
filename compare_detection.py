# -*- coding: utf-8 -*-
"""Compare model detections (log) with ground‑truth CSV.
Generates:
  - comparison_stats.csv  (TP, FP, FN, precision, recall, f1)
  - detailed_match.csv    (each detection with match info)
"""
import csv, re, math, os

def load_ground_truth(path):
    gt = []
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            gt.append({
                'frame': row['frame'],
                'class': row['class'],
                'x': int(row['x']),
                'y': int(row['y']),
                'matched': False,
            })
    return gt

def load_log(path):
    detections = []
    pattern = re.compile(r"\[(?P<time>[^\]]+)\] PHAT HIEN: ma=\d+ \| ten=(?P<class>[^|]+) \| X=(?P<x>\d+) Y=(?P<y>\d+) \| conf=(?P<conf>[0-9.]+) \| track_id=(?P<track_id>[^\s]+)")
    with open(path, encoding='utf-8') as f:
        for line in f:
            m = pattern.search(line)
            if m:
                detections.append({
                    'time': m.group('time'),
                    'class': m.group('class').strip(),
                    'x': int(m.group('x')),
                    'y': int(m.group('y')),
                    'conf': float(m.group('conf')),
                    'track_id': m.group('track_id'),
                })
    return detections

def distance(a, b):
    return math.hypot(a['x'] - b['x'], a['y'] - b['y'])

def compare(gt, detections, dist_thresh=10):
    tp = fp = 0
    detailed = []
    for det in detections:
        # find nearest unmatched ground‑truth of same class within threshold
        best = None
        best_dist = None
        for g in gt:
            if g['matched']:
                continue
            if g['class'] != det['class']:
                continue
            d = distance(det, g)
            if d <= dist_thresh and (best is None or d < best_dist):
                best = g
                best_dist = d
        if best:
            tp += 1
            best['matched'] = True
            match = 'TP'
        else:
            fp += 1
            match = 'FP'
        detailed.append({
            'time': det['time'],
            'class': det['class'],
            'x': det['x'],
            'y': det['y'],
            'conf': det['conf'],
            'track_id': det['track_id'],
            'match': match,
            'dist': best_dist if best else ''
        })
    fn = sum(1 for g in gt if not g['matched'])
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    stats = {
        'TP': tp,
        'FP': fp,
        'FN': fn,
        'precision': precision,
        'recall': recall,
        'f1': f1
    }
    return stats, detailed

if __name__ == '__main__':
    gt_path = r"d:\\pcb-edge-ai-inspection\\ground_truth.csv"
    log_path = r"d:\\pcb-edge-ai-inspection\\logs\\log_2026-10-17.txt"
    gt = load_ground_truth(gt_path)
    detections = load_log(log_path)
    stats, detailed = compare(gt, detections, dist_thresh=30)  # 30px tolerance
    # write stats CSV
    stats_path = r"d:\\pcb-edge-ai-inspection\\comparison_stats.csv"
    with open(stats_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['metric','value'])
        for k, v in stats.items():
            writer.writerow([k, v])
    # write detailed match CSV
    detailed_path = r"d:\\pcb-edge-ai-inspection\\detailed_match.csv"
    with open(detailed_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['time','class','x','y','conf','track_id','match','dist']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(detailed)
    print('Comparison completed. Stats saved to', stats_path)
    print('Detailed matches saved to', detailed_path)

