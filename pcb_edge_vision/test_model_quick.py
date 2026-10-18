"""
Script test nhanh model YOLO tren 1 anh bat ky.
Chay: python pcb_edge_vision/test_model_quick.py
"""
import cv2
from ultralytics import YOLO

# --- CAU HINH ---
MODEL_PATH  = "D:/pcb-edge-ai-inspection/pcb_edge_vision/models/pcb_defect_model_V2.pt"
VIDEO_PATH  = "D:/pcb-edge-ai-inspection/dataset/pcb_conveyor_simulation.mp4"
CONF_TEST   = 0.10   # Nguong rat thap de xem model co detect gi khong
MAX_FRAMES  = 100    # Chi lay 100 frame dau de test nhanh
# ----------------

print(f"[INFO] Tai model: {MODEL_PATH}")
model = YOLO(MODEL_PATH)
print(f"[INFO] Classes: {model.names}")

cap = cv2.VideoCapture(VIDEO_PATH)
if not cap.isOpened():
    print(f"[LOI] Khong mo duoc video: {VIDEO_PATH}")
    exit()

detect_count = 0
frame_idx = 0

print(f"\n[INFO] Quet {MAX_FRAMES} frame dau, nguong conf={CONF_TEST}...")
print("-" * 60)

while frame_idx < MAX_FRAMES:
    ret, frame = cap.read()
    if not ret:
        print("[INFO] Het video.")
        break

    results = model(frame, verbose=False, conf=CONF_TEST)
    boxes = results[0].boxes

    if len(boxes) > 0:
        for b in boxes:
            cls   = int(b.cls[0].item())
            conf  = b.conf[0].item()
            name  = model.names.get(cls, f"class_{cls}")
            print(f"  Frame {frame_idx:04d}: {name} (conf={conf:.3f})")
            detect_count += 1

    frame_idx += 1

cap.release()

print("-" * 60)
print(f"\n[KET QUA] Tong detect trong {frame_idx} frames: {detect_count} lan")
if detect_count == 0:
    print("[!] Model KHONG phat hien bat ky loi nao.")
    print("    -> Nguyen nhan co the:")
    print("       1. Video khong chua anh PCB loi (chi co board tot)")
    print("       2. Model chua duoc train tot voi loai mach nay")
    print("       3. Kich thuoc/goc chup anh qua khac voi dataset")
else:
    print(f"[OK] Model hoat dong. Neu main.py khong detect -> nguong conf qua cao.")

