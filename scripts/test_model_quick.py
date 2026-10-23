"""
scripts/test_model_quick.py — Kiểm tra nhanh model YOLO trên video.

Cách dùng (chạy từ thư mục gốc project):
    python scripts/test_model_quick.py
"""

import cv2
from ultralytics import YOLO

# --- Cấu hình ---
MODEL_PATH = "models/pcb_defect_model_V2.pt"
VIDEO_PATH = "dataset/pcb_conveyor_simulation_v2.mp4"
CONF_TEST  = 0.10   # Ngưỡng rất thấp để xem model có detect gì không
MAX_FRAMES = 100    # Chỉ lấy N frame đầu để test nhanh
# ----------------

print(f"[INFO] Tải model: {MODEL_PATH}")
model = YOLO(MODEL_PATH)
print(f"[INFO] Classes: {model.names}")

cap = cv2.VideoCapture(VIDEO_PATH)
if not cap.isOpened():
    print(f"[LOI] Không mở được video: {VIDEO_PATH}")
    exit(1)

detect_count = 0
frame_idx    = 0

print(f"\n[INFO] Quét {MAX_FRAMES} frame đầu, ngưỡng conf={CONF_TEST}...")
print("-" * 60)

while frame_idx < MAX_FRAMES:
    ret, frame = cap.read()
    if not ret:
        print("[INFO] Hết video.")
        break

    results = model(frame, verbose=False, conf=CONF_TEST)
    boxes   = results[0].boxes

    for b in boxes:
        cls  = int(b.cls[0].item())
        conf = b.conf[0].item()
        name = model.names.get(cls, f"class_{cls}")
        print(f"  Frame {frame_idx:04d}: {name} (conf={conf:.3f})")
        detect_count += 1

    frame_idx += 1

cap.release()

print("-" * 60)
print(f"\n[KET QUA] Tổng detect trong {frame_idx} frames: {detect_count} lần")
if detect_count == 0:
    print("[!] Model KHÔNG phát hiện bất kỳ lỗi nào.")
    print("    → Nguyên nhân có thể:")
    print("       1. Video không chứa ảnh PCB lỗi")
    print("       2. Model chưa được train tốt với loại mạch này")
    print("       3. Kích thước/góc chụp ảnh quá khác với dataset")
else:
    print("[OK] Model hoạt động. Nếu main.py không detect → ngưỡng conf quá cao.")
