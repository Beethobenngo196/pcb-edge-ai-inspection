"""
scripts/test_dataset_accuracy.py
Kiểm tra tự động toàn bộ ảnh trong dataset (không cần bấm GUI):
- Quét từng ảnh bo mạch và so với nhãn Ground Truth.
- Thống kê xem có bao nhiêu bo mạch phát hiện được 100% lỗi.
- Liệt kê danh sách các bo mạch bị sót lỗi (để biết chính xác model yếu ở ảnh nào).

Cách chạy:
    python scripts/test_dataset_accuracy.py
"""

import os
import cv2
import yaml
from ultralytics import YOLO

CONFIG_PATH = "app/configs/settings.yaml"


def compute_iou(box1, box2):
    ix1, iy1 = max(box1[0], box2[0]), max(box1[1], box2[1])
    ix2, iy2 = min(box1[2], box2[2]), min(box1[3], box2[3])
    inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    if inter == 0:
        return 0.0
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    return inter / (area1 + area2 - inter)


def main():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    weights_path = cfg["ai_model"]["weights_path"]
    conf_thresh = cfg["ai_model"]["confidence_threshold"]
    imgsz = cfg["ai_model"].get("imgsz", 960)
    img_dir = cfg["camera"].get("source", "dataset/images/val")

    if not os.path.isdir(img_dir):
        img_dir = "dataset/images/val"

    label_dir = img_dir.replace("images", "labels")

    print("=" * 68)
    print(f"  KIEM TRA TY LE PHAT HIEN 100% TREN TAP ANH: {img_dir}")
    print(f"  Model: {weights_path} | imgsz={imgsz} | conf={conf_thresh}")
    print("=" * 68)

    model = YOLO(weights_path)
    class_names = model.names

    images = sorted([f for f in os.listdir(img_dir) if f.lower().endswith((".jpg", ".png", ".jpeg"))])
    total_images = len(images)
    print(f"[INFO] Tim thay tong cong {total_images} anh bo mach PCB.\n")

    perfect_count = 0        # Số bo mạch phát hiện đủ 100% không sót lỗi
    imperfect_list = []      # Danh sách bo mạch bị sót lỗi hoặc dư
    total_real_defects = 0
    total_detected = 0
    total_tp = 0
    total_fp = 0
    total_fn = 0

    for idx, fname in enumerate(images, start=1):
        img_path = os.path.join(img_dir, fname)
        lbl_path = os.path.join(label_dir, os.path.splitext(fname)[0] + ".txt")

        img = cv2.imread(img_path)
        if img is None:
            continue
        h, w = img.shape[:2]

        # Đọc nhãn Ground Truth
        gt_boxes = []
        if os.path.exists(lbl_path):
            with open(lbl_path) as f:
                for line in f:
                    p = line.strip().split()
                    if len(p) >= 5:
                        cid = int(p[0])
                        xc, yc, bw, bh = map(float, p[1:5])
                        x1 = int((xc - bw / 2) * w)
                        y1 = int((yc - bh / 2) * h)
                        x2 = int((xc + bw / 2) * w)
                        y2 = int((yc + bh / 2) * h)
                        gt_boxes.append({"class": cid, "bbox": [x1, y1, x2, y2], "matched": False})

        # Model suy luận
        results = model(img, conf=conf_thresh, imgsz=imgsz, verbose=False)
        boxes = results[0].boxes

        det_boxes = []
        for b in boxes:
            cid = int(b.cls[0].item())
            conf = float(b.conf[0].item())
            x1, y1, x2, y2 = map(int, b.xyxy[0].tolist())
            det_boxes.append({"class": cid, "conf": conf, "bbox": [x1, y1, x2, y2], "matched": False})

        # Match IoU
        tp = fp = 0
        det_sorted = sorted(det_boxes, key=lambda d: d["conf"], reverse=True)
        for d in det_sorted:
            best_gt = None
            best_iou = 0.40
            for g in gt_boxes:
                if g["matched"] or g["class"] != d["class"]:
                    continue
                iou = compute_iou(d["bbox"], g["bbox"])
                if iou >= best_iou:
                    best_gt = g
                    best_iou = iou
            if best_gt:
                best_gt["matched"] = True
                tp += 1
            else:
                fp += 1

        fn = sum(1 for g in gt_boxes if not g["matched"])

        total_real_defects += len(gt_boxes)
        total_detected += len(det_boxes)
        total_tp += tp
        total_fp += fp
        total_fn += fn

        # Kiểm tra điều kiện đạt 100% (bắt đủ toàn bộ lỗi thật của bo mạch này)
        is_100_percent = (fn == 0 and len(gt_boxes) > 0)
        if is_100_percent:
            perfect_count += 1
        else:
            imperfect_list.append({
                "file": fname,
                "real": len(gt_boxes),
                "tp": tp,
                "fn": fn,
                "fp": fp,
                "missed_classes": [class_names.get(g["class"], str(g["class"])) for g in gt_boxes if not g["matched"]]
            })

    # In kết quả tổng hợp
    perfect_rate = (perfect_count / total_images) * 100 if total_images else 0
    defect_recall = (total_tp / total_real_defects) * 100 if total_real_defects else 0
    precision = (total_tp / (total_tp + total_fp)) * 100 if (total_tp + total_fp) else 0

    print("=" * 68)
    print("                KẾT QUẢ ĐÁNH GIÁ TRÊN TẬP ẢNH")
    print("=" * 68)
    print(f"  * Tổng số bo mạch kiểm tra           : {total_images}")
    print(f"  * Số bo mạch BẮT ĐỦ 100% LỖI          : {perfect_count}/{total_images} ({perfect_rate:.1f}%)")
    print(f"  * Số bo mạch bị sót lỗi (chưa đủ 100%): {len(imperfect_list)}/{total_images} ({100 - perfect_rate:.1f}%)")
    print("-" * 68)
    print(f"  * Tổng số lỗi thực tế trong toàn bộ ảnh : {total_real_defects} lỗi")
    print(f"  * Số lỗi model bắt được chính xác (TP)  : {total_tp} lỗi ({defect_recall:.1f}%)")
    print(f"  * Số lỗi model bị sót (FN)              : {total_fn} lỗi")
    print(f"  * Số lần model báo nhầm (FP)            : {total_fp} lần (Độ chính xác Precision = {precision:.1f}%)")
    print("=" * 68)

    if imperfect_list:
        print("\n[CHI TIẾT] Các bo mạch bị sót lỗi cần lưu ý (Top 10):")
        for item in imperfect_list[:10]:
            print(f"  - {item['file']:<25} | Thật: {item['real']} | Bắt: {item['tp']} | SÓT: {item['fn']} ({item['missed_classes']})")
        if len(imperfect_list) > 10:
            print(f"  ... và còn {len(imperfect_list) - 10} bo mạch khác.")


if __name__ == "__main__":
    main()

