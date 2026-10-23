"""
app/main.py — Hệ thống kiểm tra PCB theo chế độ AOI tĩnh.

Luồng hoạt động:
    1. Camera chụp 1 frame (PCB đứng yên tại trạm kiểm tra)
    2. AI phát hiện TẤT CẢ lỗi trong ảnh đó
    3. Gửi UART cho mỗi lỗi tìm được → vi điều khiển kích relay
    4. Chờ trigger tiếp theo (phím SPACE hoặc tín hiệu cảm biến)

Chạy từ thư mục gốc project:
    python app/main.py

Phím điều khiển:
    SPACE  — chụp & kiểm tra PCB hiện tại
    q      — thoát an toàn
"""

import os
import sys
import time

import cv2
import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.yolo_engine import PCBDefectDetector
from core.serial_comm import SerialCommunicator
from core.camera_stream import CameraStream
from utils.logger import DefectLogger
from utils.perf_stats import PerfStats


def inspect_frame(frame, detector, uart, logger, config):
    """
    Kiểm tra 1 frame PCB tĩnh.
    Phát hiện TẤT CẢ lỗi, gửi UART cho từng lỗi, ghi log.
    Trả về (annotated_frame, danh sách lỗi tìm được).
    """
    conf_thresh = config["ai_model"]["confidence_threshold"]
    frame_h, frame_w = frame.shape[:2]

    t0      = time.perf_counter()
    results = detector.detect_frame(frame, verbose=False, conf=conf_thresh)
    ai_ms   = (time.perf_counter() - t0) * 1000

    boxes       = results[0].boxes
    class_names = results[0].names
    defects     = []

    for b in boxes:
        conf       = b.conf[0].item()
        error_code = int(b.cls[0].item())
        error_name = class_names.get(error_code, f"class_{error_code}")

        cx_px  = b.xywh[0][0].item()
        cy_px  = b.xywh[0][1].item()
        x_uart = int(min(max(cx_px / frame_w * 255, 0), 255))
        y_uart = int(min(max(cy_px / frame_h * 255, 0), 255))

        # Gửi UART cho từng lỗi (không debounce — PCB đứng yên, mỗi lỗi = 1 gói)
        uart.send_defect_data(error_code, x_uart, y_uart)
        logger.log_defect(error_code, error_name, cx_px, cy_px, x_uart, y_uart, conf)

        defects.append({
            "name": error_name, "conf": conf,
            "cx_px": int(cx_px), "cy_px": int(cy_px),
        })
        print(f"  ✗ {error_name:<18} conf={conf:.2f}  px=({int(cx_px)},{int(cy_px)})")

    annotated = results[0].plot()
    return annotated, defects, ai_ms


def draw_status(frame, status_text, color):
    """In trạng thái lên góc trên ảnh."""
    cv2.rectangle(frame, (0, 0), (frame.shape[1], 50), (0, 0, 0), -1)
    cv2.putText(frame, status_text, (15, 35),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2, cv2.LINE_AA)
    return frame


def main():
    print("=" * 55)
    print("  HE THONG KIEM TRA PCB — CHE DO AOI TINH")
    print("  [SPACE] Chup & Kiem tra  |  [Q] Thoat")
    print("=" * 55)

    # ─── Tải cấu hình ────────────────────────────────────────
    cfg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "configs", "settings.yaml")
    with open(cfg_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # ─── Khởi tạo các module ─────────────────────────────────
    detector = PCBDefectDetector(config["ai_model"]["weights_path"])
    uart     = SerialCommunicator(config["serial"]["port"], config["serial"]["baudrate"])
    logger   = DefectLogger()
    camera   = CameraStream(config["camera"]["source"])
    perf     = PerfStats(report_every_sec=0)   # Chỉ in khi được gọi thủ công

    # ─── VideoWriter (lưu lại ảnh kết quả nếu bật) ───────────
    save_results = config.get("output", {}).get("save_video", True)
    result_dir   = "logs/inspections"
    if save_results:
        os.makedirs(result_dir, exist_ok=True)
        print(f"[INFO] Kết quả ảnh sẽ lưu vào: {result_dir}/")

    # ─── Vòng lặp chính ──────────────────────────────────────
    cv2.namedWindow("AOI - Kiem tra PCB", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("AOI - Kiem tra PCB", 1280, 720)

    board_count  = 0
    defect_count = 0
    current_view = None   # Frame hiển thị hiện tại

    print("\n[OK] San sang. Dat PCB vao vi tri roi nhan SPACE de kiem tra.\n")

    while True:
        # Luôn lấy frame mới nhất từ camera để hiển thị live preview
        live_frame = camera.get_frame()

        if live_frame is not None:
            preview = live_frame.copy()
            draw_status(preview,
                        f"Bo mach: {board_count}  Loi tong: {defect_count}  | SPACE=Kiem tra  Q=Thoat",
                        (0, 255, 255))
            display = preview
        elif current_view is not None:
            display = current_view
        else:
            display = None

        if display is not None:
            cv2.imshow("AOI - Kiem tra PCB", display)

        key = cv2.waitKey(30) & 0xFF

        # ── Nhấn SPACE: kiểm tra PCB hiện tại ────────────────
        if key == ord(" "):
            frame = camera.get_frame()
            if frame is None:
                print("[CANH BAO] Khong lay duoc frame tu camera!")
                continue

            board_count += 1
            print(f"\n[KIEM TRA #{board_count}] Dang xu ly...")

            t_start                = time.perf_counter()
            annotated, defects, ai_ms = inspect_frame(frame, detector, uart, logger, config)
            total_ms               = (time.perf_counter() - t_start) * 1000

            if defects:
                defect_count += len(defects)
                result_text  = f"#{board_count}: CO {len(defects)} LOI — LOAI BO"
                color        = (0, 0, 255)   # Đỏ
                print(f"  → KET QUA: CO LOI ({len(defects)} loi) — [{total_ms:.0f}ms]")
            else:
                result_text = f"#{board_count}: DAT — THONG QUA"
                color       = (0, 255, 0)    # Xanh lá
                print(f"  → KET QUA: DAT — [{total_ms:.0f}ms]")

            # Hiển thị ảnh kết quả
            current_view = draw_status(annotated.copy(), result_text, color)
            cv2.imshow("AOI - Kiem tra PCB", current_view)

            # Lưu ảnh kết quả
            if save_results:
                ts        = time.strftime("%H%M%S")
                out_fname = f"{result_dir}/board_{board_count:04d}_{ts}.jpg"
                cv2.imwrite(out_fname, annotated)
                print(f"  → Da luu: {out_fname}")

        # ── Nhấn Q: thoát ─────────────────────────────────────
        elif key == ord("q") or key == 27:
            break

    # ─── Dọn dẹp ─────────────────────────────────────────────
    camera.release()
    uart.close()
    cv2.destroyAllWindows()

    print("\n" + "=" * 55)
    print(f"  TONG KET: {board_count} bo mach | {defect_count} loi phat hien")
    print("  HE THONG TAT AN TOAN")
    print("=" * 55)


if __name__ == "__main__":
    main()
