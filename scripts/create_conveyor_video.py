"""
Tao video gia lap bang chuyen PCB tu anh trong dataset.
Moi anh se "di chuyen" ngang qua khung hinh nhu PCB tren bang chuyen that.

Chay: python pcb_edge_vision/create_conveyor_video.py
Output: dataset/pcb_conveyor_simulation_v2.mp4
"""

import cv2
import numpy as np
import os
import random
import glob

# ==========================================
# CAU HINH
# ==========================================
IMAGE_DIR    = "dataset/images/train"     # Chạy từ thư mục gốc project
OUTPUT_VIDEO = "dataset/pcb_conveyor_simulation_v2.mp4"
VIDEO_W, VIDEO_H = 1280, 720             # Do phan giai video xuat ra
FPS          = 30
BELT_COLOR   = (30, 30, 30)             # Mau nen bang chuyen (xam dam)
BELT_SPEED   = 8                         # Pixel/frame PCB di chuyen sang phai
PCB_SCALE    = 0.5                       # Ti le thu nho anh PCB vao khung hinh
GAP_FRAMES   = 60                        # So frame trong giua 2 PCB (khong co gi)
NOISE_LEVEL  = 8                         # Muc nhieu nen (0 = khong nhieu)


def add_belt_texture(frame):
    """Them van bang chuyen: duong ke ngang nhu bang tai cao su."""
    h, w = frame.shape[:2]
    for y in range(0, h, 30):
        cv2.line(frame, (0, y), (w, y), (40, 40, 40), 1)
    return frame


def add_noise(frame, level=8):
    """Them nhieu Gaussian nhe de gia lap cam bien camera."""
    if level == 0:
        return frame
    noise = np.random.randint(-level, level, frame.shape, dtype=np.int16)
    noisy = np.clip(frame.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    return noisy


def resize_pcb(img, target_h):
    """Thu nho anh PCB sao cho chieu cao = target_h, giu ty le."""
    h, w = img.shape[:2]
    ratio = target_h / h
    new_w = int(w * ratio)
    return cv2.resize(img, (new_w, target_h))


def main():
    # 1. Lay danh sach anh
    patterns = [
        os.path.join(IMAGE_DIR, "*.jpg"),
        os.path.join(IMAGE_DIR, "*.jpeg"),
        os.path.join(IMAGE_DIR, "*.png"),
    ]
    image_paths = []
    for p in patterns:
        image_paths.extend(glob.glob(p))

    if not image_paths:
        print(f"[LOI] Khong tim thay anh trong '{IMAGE_DIR}'")
        print("      Hay sua IMAGE_DIR cho dung voi thu muc dataset cua ban.")
        return

    random.shuffle(image_paths)
    print(f"[INFO] Tim thay {len(image_paths)} anh -> bat dau tao video...")

    # 2. Khoi tao VideoWriter
    os.makedirs(os.path.dirname(OUTPUT_VIDEO), exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(OUTPUT_VIDEO, fourcc, FPS, (VIDEO_W, VIDEO_H))

    pcb_h = int(VIDEO_H * PCB_SCALE)     # Chieu cao PCB tren video

    total_frames = 0

    for idx, img_path in enumerate(image_paths):
        img = cv2.imread(img_path)
        if img is None:
            continue

        # Thu nho PCB
        pcb = resize_pcb(img, pcb_h)
        pcb_w = pcb.shape[1]

        # Vi tri Y de can giua theo chieu doc
        y_offset = (VIDEO_H - pcb_h) // 2

        # PCB bat dau tu ben phai, di chuyen sang trai (giong bang chuyen that)
        # x_start: PCB o ngoai man hinh ben phai
        # x_end:   PCB ra khoi man hinh ben trai
        x_start = VIDEO_W + 10
        x_end   = -pcb_w - 10

        x = x_start
        while x > x_end:
            # --- Tao khung nen bang chuyen ---
            frame = np.full((VIDEO_H, VIDEO_W, 3), BELT_COLOR, dtype=np.uint8)
            add_belt_texture(frame)

            # --- Dan PCB len bang chuyen ---
            # Clip vung hien thi (PCB co the bi cat khi o ria man hinh)
            src_x1 = max(0, -x)
            src_x2 = min(pcb_w, VIDEO_W - x)
            dst_x1 = max(0, x)
            dst_x2 = min(VIDEO_W, x + pcb_w)

            if src_x1 < src_x2 and dst_x1 < dst_x2:
                frame[y_offset:y_offset+pcb_h, dst_x1:dst_x2] = pcb[:, src_x1:src_x2]

            # --- Them nhieu ---
            frame = add_noise(frame, NOISE_LEVEL)

            writer.write(frame)
            total_frames += 1
            x -= BELT_SPEED

        # --- Khung trong giua 2 PCB ---
        for _ in range(GAP_FRAMES):
            frame = np.full((VIDEO_H, VIDEO_W, 3), BELT_COLOR, dtype=np.uint8)
            add_belt_texture(frame)
            frame = add_noise(frame, NOISE_LEVEL)
            writer.write(frame)
            total_frames += 1

        print(f"  [{idx+1}/{len(image_paths)}] {os.path.basename(img_path)}")

    writer.release()
    duration = total_frames / FPS
    print(f"\n[XONG] Video da luu: {OUTPUT_VIDEO}")
    print(f"       {total_frames} frames | {duration:.1f} giay | {FPS} FPS")
    print(f"       Cap nhat settings.yaml -> source: \"{OUTPUT_VIDEO}\"")


if __name__ == "__main__":
    main()

