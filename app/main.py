"""
app/main.py — Hệ thống kiểm tra PCB (Hỗ trợ Dataset Ảnh tĩnh & Camera thật).

Chế độ hoạt động (cấu hình trong app/configs/settings.yaml):
  1. Chế độ Duyệt ảnh Dataset (camera.source = 'dataset/images/val' hoặc 'train'):
     - Nạp ảnh bo mạch trực tiếp từ dataset để kiểm tra tỷ lệ phát hiện 100%.
     - So sánh tức thì với Ground Truth (.txt nhãn gốc).
     - Điều hướng phím:
         [SPACE] hoặc [D] hoặc [->] : Sang bo mạch tiếp theo & soi lỗi
         [A] hoặc [<-]               : Quay lại bo mạch trước
         [R]                         : Chọn ngẫu nhiên 1 bo mạch để thử thách
         [S]                         : Lưu ảnh kết quả vào logs/inspections/
         [Q] hoặc [ESC]              : Thoát an toàn
  2. Chế độ Camera thật (camera.source = 0):
     - Xem trực tiếp camera, nhấn [SPACE] để chụp và kiểm định bo mạch tĩnh tại trạm.
"""

import os
import sys
import time

import cv2
import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.camera_stream import CameraStream
from core.serial_comm import SerialCommunicator
from core.yolo_engine import PCBDefectDetector
from utils.logger import DefectLogger


# Bảng màu đại diện cho 6 lớp khuyết tật (BGR)
CLASS_COLORS = {
    0: (0, 165, 255),   # missing_hole    - Cam đậm
    1: (255, 0, 255),   # mouse_bite      - Hồng tím
    2: (0, 255, 255),   # open_circuit    - Vàng
    3: (0, 0, 255),     # short           - Đỏ
    4: (255, 255, 0),   # spur            - Xanh lơ (cyan)
    5: (255, 140, 0),   # spurious_copper - Xanh da trời đậm
}


def load_ground_truth(label_path, frame_w, frame_h):
    """Đọc file nhãn YOLO ground-truth .txt (nếu có)"""
    gt_boxes = []
    if not label_path or not os.path.exists(label_path):
        return gt_boxes

    with open(label_path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 5:
                continue
            cid = int(parts[0])
            xc, yc, w, h = map(float, parts[1:5])
            x1 = int((xc - w / 2) * frame_w)
            y1 = int((yc - h / 2) * frame_h)
            x2 = int((xc + w / 2) * frame_w)
            y2 = int((yc + h / 2) * frame_h)
            gt_boxes.append({
                "class": cid,
                "bbox": [x1, y1, x2, y2],
                "matched": False,
            })
    return gt_boxes


def compute_iou(box1, box2):
    """Tính Intersection over Union giữa 2 bounding box [x1, y1, x2, y2]"""
    ix1 = max(box1[0], box2[0])
    iy1 = max(box1[1], box2[1])
    ix2 = min(box1[2], box2[2])
    iy2 = min(box1[3], box2[3])

    inter_w = max(0, ix2 - ix1)
    inter_h = max(0, iy2 - iy1)
    inter_area = inter_w * inter_h

    if inter_area == 0:
        return 0.0

    area1 = max(0, box1[2] - box1[0]) * max(0, box1[3] - box1[1])
    area2 = max(0, box2[2] - box2[0]) * max(0, box2[3] - box2[1])
    union = area1 + area2 - inter_area
    return inter_area / union if union > 0 else 0.0


def inspect_pcb(frame, detector, uart, logger, config, label_path=None, filename=""):
    """
    Thực hiện soi lỗi toàn diện cho 1 ảnh PCB:
    1. AI YOLOv8 suy luận tìm kiếm tất cả các lỗi.
    2. Đọc nhãn Ground Truth (nếu có) để đối chiếu xem đạt 100% hay không.
    3. Gửi UART cho vi điều khiển (hoặc mô phỏng gửi).
    4. Vẽ trực quan Ground Truth và Detections lên ảnh.
    """
    default_conf = float(config["ai_model"].get("confidence_threshold", 0.15))
    class_threshs = config["ai_model"].get("class_thresholds", {})
    min_conf = min([default_conf] + [float(v) for v in class_threshs.values()]) if class_threshs else default_conf
    min_conf = max(0.05, min_conf)

    imgsz = config["ai_model"].get("imgsz", 960)
    frame_h, frame_w = frame.shape[:2]

    # --- 1. Suy luận AI ---
    t0 = time.perf_counter()
    results = detector.detect_frame(frame, verbose=False, conf=min_conf, imgsz=imgsz)
    ai_ms = (time.perf_counter() - t0) * 1000

    boxes = results[0].boxes
    class_names = results[0].names  # {0: 'missing_hole', 1: 'mouse_bite', ...}

    det_list = []
    for b in boxes:
        conf = float(b.conf[0].item())
        cid = int(b.cls[0].item())
        cname = class_names.get(cid, f"class_{cid}")

        # Lọc theo ngưỡng riêng của từng lớp (Per-Class Thresholding)
        required_conf = float(class_threshs.get(cname, class_threshs.get(str(cid), default_conf)))
        if conf < required_conf:
            continue

        x1, y1, x2, y2 = map(int, b.xyxy[0].tolist())
        cx = (x1 + x2) / 2.0
        cy = (y1 + y2) / 2.0

        # Tọa độ 0-255 gửi UART
        x_uart = int(min(max(cx / frame_w * 255, 0), 255))
        y_uart = int(min(max(cy / frame_h * 255, 0), 255))

        det_list.append({
            "class": cid,
            "name": cname,
            "conf": conf,
            "bbox": [x1, y1, x2, y2],
            "cx": cx,
            "cy": cy,
            "x_uart": x_uart,
            "y_uart": y_uart,
            "matched": False,
        })

    # --- 2. Đối chiếu với Ground Truth ---
    gt_boxes = load_ground_truth(label_path, frame_w, frame_h) if label_path else []
    tp = fp = fn = 0

    if gt_boxes:
        # Match detections với GT (ưu tiên confidence cao trước)
        det_sorted = sorted(det_list, key=lambda d: d["conf"], reverse=True)
        for det in det_sorted:
            best_gt = None
            best_iou = 0.40  # Ngưỡng IoU coi là khớp đúng
            for gt in gt_boxes:
                if gt["matched"] or gt["class"] != det["class"]:
                    continue
                iou = compute_iou(det["bbox"], gt["bbox"])
                if iou >= best_iou:
                    best_gt = gt
                    best_iou = iou

            if best_gt:
                det["matched"] = True
                best_gt["matched"] = True
                tp += 1
            else:
                fp += 1

        fn = sum(1 for g in gt_boxes if not g["matched"])
        total_gt = len(gt_boxes)
        is_100_percent = (fn == 0 and total_gt > 0 and fp == 0)
        detected_all_real = (fn == 0 and total_gt > 0)
    else:
        total_gt = None
        is_100_percent = False
        detected_all_real = False

    # --- 3. In kết quả ra Console & Gửi UART ---
    print("\n" + "=" * 65)
    print(f"  [KIEM TRA PCB] {filename or 'Khung hinh hien tai'}")
    print(f"  Thoi gian AI xu ly: {ai_ms:.1f} ms")
    print("-" * 65)

    if total_gt is not None:
        print(f"  * Loi thuc te (Ground Truth) : {total_gt} loi")
        print(f"  * AI phat hien               : {len(det_list)} loi (TP={tp}, FP={fp}, FN={fn})")
        if is_100_percent:
            print("  >>> DANH GIA: [HOAN HAO 100%] Phat hien dung du 100% tat ca loi, khong sai sot! <<<")
        elif detected_all_real:
            print(f"  >>> DANH GIA: [DAT 100% THUC TE] Bat du {tp}/{total_gt} loi thuc (co {fp} bao nham). <<<")
        else:
            print(f"  >>> DANH GIA: [CHUA DU 100%] Bat {tp}/{total_gt} loi, SOT {fn} LOI! <<<")
    else:
        print(f"  * AI phat hien: {len(det_list)} loi")

    # Gửi UART & ghi log cho từng lỗi
    for i, d in enumerate(det_list, start=1):
        match_str = " [KHOP DUNG]" if d["matched"] else (" [BAO NHAM]" if gt_boxes else "")
        print(f"    [{i}] {d['name']:<16} conf={d['conf']:.2f} | px=({int(d['cx'])},{int(d['cy'])}) | UART=({d['x_uart']},{d['y_uart']}){match_str}")
        uart.send_defect_data(d["class"], d["x_uart"], d["y_uart"])
        logger.log_defect(d["class"], d["name"], d["cx"], d["cy"], d["x_uart"], d["y_uart"], d["conf"])

    if not det_list:
        print("  * Khong phat hien loi nao -> BO MACH DAT CHUAN (PASS).")

    print("=" * 65)

    # --- 4. Vẽ trực quan lên ảnh ---
    canvas = frame.copy()

    # (A) Vẽ viền Ground Truth bằng nét đứt màu xanh lá cây để đối chiếu
    for g in gt_boxes:
        gx1, gy1, gx2, gy2 = g["bbox"]
        cname = class_names.get(g["class"], str(g["class"]))
        cv2.rectangle(canvas, (gx1 - 3, gy1 - 3), (gx2 + 3, gy2 + 3), (0, 255, 0), 2)
        cv2.putText(canvas, f"[GT] {cname}", (gx1, max(gy1 - 8, 15)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1, cv2.LINE_AA)

    # (B) Vẽ Bounding Box của Model AI
    for d in det_list:
        bx1, by1, bx2, by2 = d["bbox"]
        color = CLASS_COLORS.get(d["class"], (0, 0, 255))
        cv2.rectangle(canvas, (bx1, by1), (bx2, by2), color, 2)

        label = f"{d['name']} {d['conf']:.2f}"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(canvas, (bx1, by1 - th - 6), (bx1 + tw + 6, by1), color, -1)
        cv2.putText(canvas, label, (bx1 + 3, by1 - 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)

    # (C) Vẽ thanh Banner trạng thái trên cùng
    cv2.rectangle(canvas, (0, 0), (frame_w, 60), (20, 20, 20), -1)

    if total_gt is not None:
        if is_100_percent or detected_all_real:
            status_text = f"[{filename}] DAT 100% | Phat hien: {tp}/{total_gt} loi | AI={len(det_list)}"
            status_color = (0, 255, 0)   # Xanh lá sáng
        else:
            status_text = f"[{filename}] CHUA DAT 100% | SOT {fn} LOI ({tp}/{total_gt}) | AI={len(det_list)}"
            status_color = (0, 69, 255)   # Đỏ cam
    else:
        status_text = f"[{filename or 'Camera'}] Phat hien: {len(det_list)} loi"
        status_color = (0, 255, 255) if det_list else (0, 255, 0)

    cv2.putText(canvas, status_text, (15, 38),
                cv2.FONT_HERSHEY_SIMPLEX, 0.75, status_color, 2, cv2.LINE_AA)

    # (D) Vẽ thanh Banner điều khiển ở dưới cùng
    cv2.rectangle(canvas, (0, frame_h - 40), (frame_w, frame_h), (25, 25, 25), -1)
    hint_text = "[SPACE / D]: Tiep theo  |  [A]: Bo mach truoc  |  [R]: Ngau nhien  |  [S]: Luu anh  |  [Q]: Thoat"
    cv2.putText(canvas, hint_text, (15, frame_h - 14),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1, cv2.LINE_AA)

    return canvas, det_list, is_100_percent or detected_all_real


def main():
    print("=" * 65)
    print("   HE THONG EDGE AI KIEM TRA LOI BO MACH PCB (SMART AOI)")
    print("=" * 65)

    # Đọc cấu hình
    cfg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "configs", "settings.yaml")
    with open(cfg_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Khởi tạo modules
    detector = PCBDefectDetector(config["ai_model"]["weights_path"])
    uart     = SerialCommunicator(config["serial"]["port"], config["serial"]["baudrate"])
    logger   = DefectLogger()
    camera   = CameraStream(config["camera"]["source"])

    # Thư mục lưu kết quả ảnh
    inspection_dir = config.get("output", {}).get("inspection_dir", "logs/inspections")
    os.makedirs(inspection_dir, exist_ok=True)

    window_name = "Edge AI PCB Inspection - Smart AOI Station"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    win_w = config.get("display", {}).get("window_width", 1280)
    win_h = config.get("display", {}).get("window_height", 720)
    cv2.resizeWindow(window_name, win_w, win_h)

    # Thống kê tích lũy phiên làm việc
    inspected_total = 0
    passed_100_count = 0

    # Chạy lần kiểm tra đầu tiên
    current_frame = camera.get_frame()
    if current_frame is None:
        print("[LOI] Khong the tai hinh anh tu nguon da chi dinh. Kiem tra lai settings.yaml!")
        return

    curr_num, total_num = camera.get_progress_info()
    filename = camera.get_current_filename()
    title_str = f"#{curr_num}/{total_num} {filename}" if total_num > 0 else filename
    label_path = camera.get_current_label_path()

    annotated_display, last_dets, is_perfect = inspect_pcb(
        current_frame, detector, uart, logger, config, label_path=label_path, filename=title_str
    )
    inspected_total += 1
    if is_perfect:
        passed_100_count += 1

    print("\n[HUONG DAN] Nhan [SPACE] hoac [D] tren cua so de chuyen sang bo mach tiep theo!")

    while True:
        cv2.imshow(window_name, annotated_display)
        key = cv2.waitKey(50) & 0xFF

        # Phím SPACE (32) hoặc D / d: Chuyển sang ảnh tiếp theo và soi lỗi
        if key in (ord(" "), ord("d"), ord("D")):
            if camera.is_dataset_mode():
                next_f = camera.next_image()
                if next_f is not None:
                    curr_num, total_num = camera.get_progress_info()
                    filename = camera.get_current_filename()
                    title_str = f"#{curr_num}/{total_num} {filename}"
                    label_path = camera.get_current_label_path()
                    annotated_display, last_dets, is_perfect = inspect_pcb(
                        next_f, detector, uart, logger, config, label_path=label_path, filename=title_str
                    )
                    inspected_total += 1
                    if is_perfect:
                        passed_100_count += 1
            else:
                # Camera live stream -> lấy frame mới nhất và soi
                live_f = camera.get_frame()
                if live_f is not None:
                    annotated_display, last_dets, is_perfect = inspect_pcb(
                        live_f, detector, uart, logger, config, filename=f"Live_#{inspected_total + 1}"
                    )
                    inspected_total += 1

        # Phím A / a: Quay lại ảnh trước
        elif key in (ord("a"), ord("A")):
            if camera.is_dataset_mode():
                prev_f = camera.prev_image()
                if prev_f is not None:
                    curr_num, total_num = camera.get_progress_info()
                    filename = camera.get_current_filename()
                    title_str = f"#{curr_num}/{total_num} {filename}"
                    label_path = camera.get_current_label_path()
                    annotated_display, last_dets, is_perfect = inspect_pcb(
                        prev_f, detector, uart, logger, config, label_path=label_path, filename=title_str
                    )
                    inspected_total += 1
                    if is_perfect:
                        passed_100_count += 1

        # Phím R / r: Chọn ngẫu nhiên 1 bo mạch bất kỳ
        elif key in (ord("r"), ord("R")):
            if camera.is_dataset_mode():
                rand_f = camera.random_image()
                if rand_f is not None:
                    curr_num, total_num = camera.get_progress_info()
                    filename = camera.get_current_filename()
                    title_str = f"#{curr_num}/{total_num} {filename}"
                    label_path = camera.get_current_label_path()
                    annotated_display, last_dets, is_perfect = inspect_pcb(
                        rand_f, detector, uart, logger, config, label_path=label_path, filename=title_str
                    )
                    inspected_total += 1
                    if is_perfect:
                        passed_100_count += 1

        # Phím S / s: Lưu ảnh kết quả
        elif key in (ord("s"), ord("S")):
            save_name = f"inspect_{camera.get_current_filename() or time.strftime('%H%M%S')}.jpg"
            save_path = os.path.join(inspection_dir, save_name)
            cv2.imwrite(save_path, annotated_display)
            print(f"[DA LUU] Anh ket qua da luu vao: {save_path}")

        # Phím Q / ESC: Thoát
        elif key in (ord("q"), ord("Q"), 27):
            break

    # Dọn dẹp
    camera.release()
    uart.close()
    cv2.destroyAllWindows()

    print("\n" + "=" * 65)
    print("  [TONG KET PHIEN LAM VIEC]")
    print(f"  - So bo mach da kiem tra        : {inspected_total}")
    if camera.is_dataset_mode() and inspected_total > 0:
        ratio = (passed_100_count / inspected_total) * 100
        print(f"  - So bo mach dat 100% phat hien : {passed_100_count}/{inspected_total} ({ratio:.1f}%)")
    print("  Hệ thống tắt an toàn.")
    print("=" * 65)


if __name__ == "__main__":
    main()
