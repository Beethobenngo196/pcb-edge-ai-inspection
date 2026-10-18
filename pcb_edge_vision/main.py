import time

import cv2
import yaml

from core.yolo_engine import PCBDefectDetector
from core.serial_comm import SerialCommunicator
from core.frame_grabber import FrameGrabber
from utils.logger import DefectLogger
from utils.perf_stats import PerfStats

# --- Fallback debounce (chi dung khi tracker CHUA gan duoc track ID cho box,
# vi du vai frame dau tien) ---
DEBOUNCE_DISTANCE_PX = 40
DEBOUNCE_COOLDOWN_SEC = 1.5


def main():
    print("--- KHOI DONG HE THONG KIEM TRA BANG CHUYEN ---")

    print("[INFO] Dang tai cau hinh he thong...")
    with open("pcb_edge_vision/configs/settings.yaml", "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    ai_detector = PCBDefectDetector(config["ai_model"]["weights_path"])
    uart = SerialCommunicator(config["serial"]["port"], config["serial"]["baudrate"])
    logger = DefectLogger()

    # --- Producer: chay o luong rieng, chi lo doc camera lien tuc ---
    frame_grabber = FrameGrabber(config["camera"]["source"]).start()

    perf = PerfStats(report_every_sec=2.0)

    # Track ID da gui UART roi -> KHONG gui lai cho cung 1 vat the (bo mach)
    # dang duoc theo doi xuyen suot nhieu frame lien tiep boi ByteTrack.
    # Tap nay se tang dan trong 1 phien chay, chi chua so nguyen nen chiem
    # rat it bo nho, khong can don dep cho pham vi 1 ca chay he thong.
    sent_track_ids = set()

    # Fallback debounce theo khoang cach: (ma_loi, x_pixel, y_pixel, thoi_diem_gui)
    # chi dung khi track_id la None (tracker chua kip gan ID).
    last_sent = None
    last_frame_id = -1

    # Tao cua so hien thi video, co the resize tu dong theo kich thuoc cua khung hinh
    cv2.namedWindow("He thong Kiem tra Bo mach", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("He thong Kiem tra Bo mach", 1917, 988)

    # --- Khoi tao VideoWriter de luu video output co annotation ---
    video_writer = None
    output_video_path = config.get("output", {}).get(
        "video_path", "logs/output_annotated.mp4"
    )
    save_video = config.get("output", {}).get("save_video", True)

    try:
        print("\n>>> BAT DAU CHAY BANG CHUYEN (Nhan phim 'q' de dung) <<<\n")
        if save_video:
            print(f"[INFO] Se luu video output ra: {output_video_path}")

        while True:
            frame, frame_id, camera_ms = frame_grabber.get_latest()

            if frame is None and not frame_grabber.is_running():
                print("Da mat tin hieu camera hoac phat het video!")
                break

            if frame is None or frame_id == last_frame_id:
                time.sleep(0.001)
                continue

            last_frame_id = frame_id
            t_loop_start = time.perf_counter()

            frame_h, frame_w = frame.shape[:2]

            # Khoi tao VideoWriter sau khi biet kich thuoc frame (lan dau tien)
            if save_video and video_writer is None:
                import os
                os.makedirs(os.path.dirname(output_video_path) or ".", exist_ok=True)
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                video_writer = cv2.VideoWriter(
                    output_video_path, fourcc, 30, (frame_w, frame_h)
                )
                print(f"[INFO] VideoWriter khoi tao: {frame_w}x{frame_h} @ 30fps")

            t2 = time.perf_counter()
            # track_frame thay cho detect_frame: co gan them track ID on dinh
            # cho tung vat the xuyen suot nhieu frame (ByteTrack, persist=True)
            results = ai_detector.track_frame(frame, verbose=False)
            t3 = time.perf_counter()
            ai_ms = (t3 - t2) * 1000

            boxes = results[0].boxes
            class_names = results[0].names  # {0: 'missing_hole', 1: 'mouse_bite', ...}

            if len(boxes) > 0:
                candidates = [
                    b for b in boxes
                    if b.conf[0].item() >= config["ai_model"]["confidence_threshold"]
                ]

                if candidates:
                    best_box = max(candidates, key=lambda b: b.conf[0].item())
                    error_code = int(best_box.cls[0].item())
                    error_name = class_names.get(error_code, f"class_{error_code}")

                    cx_px = best_box.xywh[0][0].item()
                    cy_px = best_box.xywh[0][1].item()
                    conf  = best_box.conf[0].item()

                    x = int(min(max(cx_px / frame_w * 255, 0), 255))
                    y = int(min(max(cy_px / frame_h * 255, 0), 255))

                    # best_box.id la None neu tracker chua kip gan ID cho box nay
                    # (thuong chi xay ra o vai frame dau tien khi vat the moi xuat hien)
                    track_id = int(best_box.id.item()) if best_box.id is not None else None

                    now = time.monotonic()
                    should_send = True

                    if track_id is not None:
                        if track_id in sent_track_ids:
                            should_send = False
                        else:
                            sent_track_ids.add(track_id)
                    else:
                        # Fallback: chua co ID on dinh -> dung tam debounce theo
                        # khoang cach + thoi gian nhu ban truoc de van an toan.
                        if last_sent is not None:
                            last_code, last_x, last_y, last_time = last_sent
                            same_defect = (
                                error_code == last_code
                                and abs(cx_px - last_x) < DEBOUNCE_DISTANCE_PX
                                and abs(cy_px - last_y) < DEBOUNCE_DISTANCE_PX
                            )
                            if same_defect and (now - last_time) < DEBOUNCE_COOLDOWN_SEC:
                                should_send = False

                    if should_send:
                        uart.send_defect_data(error_code, x, y)
                        logger.log_defect(error_code, error_name, x, y, conf, track_id)
                        last_sent = (error_code, cx_px, cy_px, now)
                        print(f"[DETECT] {error_name} (conf={conf:.2f}, track_id={track_id})")

            annotated_frame = results[0].plot()
            cv2.imshow("He thong Kiem tra Bo mach", annotated_frame)

            # Ghi frame vao file video output
            if save_video and video_writer is not None:
                video_writer.write(annotated_frame)

            t_loop_end = time.perf_counter()
            total_ms = (t_loop_end - t_loop_start) * 1000
            perf.record(camera_ms, ai_ms, total_ms)

            # Gioi han FPS hien thi dung bang FPS goc cua video (mac dinh 30fps)
            # de video khong chay nhanh hon toc do thuc te tren bang chuyen.
            target_frame_ms = 1000.0 / config.get("display", {}).get("fps", 30)
            wait_ms = max(1, int(target_frame_ms - total_ms))
            if cv2.waitKey(wait_ms) & 0xFF == ord("q"):
                print("Nguoi dung da ra lenh dung he thong.")
                break

    finally:
        frame_grabber.stop()
        uart.close()
        if video_writer is not None:
            video_writer.release()
            print(f"[INFO] Da luu video output: {output_video_path}")
        cv2.destroyAllWindows()
        print("--- HE THONG TAT AN TOAN ---")


if __name__ == "__main__":
    main()