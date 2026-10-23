"""
training/train_ai.py — Huấn luyện mô hình mạnh nhất YOLOv8m (Medium - 25.9M tham số)
Tối ưu hóa đặc biệt cho card NVIDIA GeForce RTX 3050 Laptop GPU (4GB VRAM).

Đặc điểm:
- Dung lượng mạng gấp 10 lần bản Nano (25.9M params vs 2.6M params).
- Độ phân giải cao imgsz=960.
- Khả năng phân biệt các vi khuyết tật (mẻ mạch, đứt mạch vi mô) vượt trội.
"""

import os
import shutil
import yaml
from ultralytics import YOLO


def main():
    base_model = "models/yolov8m.pt"

    print("=" * 68)
    print("  BAT DAU HUAN LUYEN MODEL MANH NHAT: YOLOv8-MEDIUM (25.9M Tham so)")
    print(f"  Trọng số gốc : {base_model}")
    print("  Phần cứng     : NVIDIA GeForce RTX 3050 Laptop GPU (device=0)")
    print("  Cấu hình      : imgsz=960 | batch=2 | epochs=30 | AMP=True")
    print("=" * 68)

    model = YOLO(base_model)

    # Huấn luyện mô hình YOLOv8-Medium
    results = model.train(
        data="dataset/data.yaml",
        epochs=30,
        imgsz=960,
        batch=2,              # batch=2 tối ưu cho 4GB VRAM của RTX 3050 (chiếm ~2.16GB)
        device=0,             # GPU RTX 3050
        workers=0,            # Ổn định tuyệt đối trên Windows
        project="training/runs",
        name="yolov8m_pcb_model_v4",
        exist_ok=True,

        # Augmentation chuyên dụng cho bo mạch
        hsv_h=0.015,
        hsv_s=0.5,
        hsv_v=0.4,
        degrees=5.0,
        translate=0.05,
        scale=0.2,
        fliplr=0.5,
        flipud=0.0,
        mosaic=0.5,
        patience=10,          # Dừng sớm nếu không cải thiện sau 10 epoch
    )

    best_pt = "training/runs/yolov8m_pcb_model_v4/weights/best.pt"
    v4_dest = "models/pcb_defect_model_V4_medium.pt"

    if os.path.exists(best_pt):
        shutil.copy(best_pt, v4_dest)
        print("\n" + "=" * 68)
        print(f"[HOÀN TẤT] Đã tạo xong model V4 Medium đỉnh nhất tại: {v4_dest}")

        # Tự động cập nhật cấu hình settings.yaml
        cfg_path = "app/configs/settings.yaml"
        if os.path.exists(cfg_path):
            with open(cfg_path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f)
            cfg["ai_model"]["weights_path"] = v4_dest
            cfg["ai_model"]["imgsz"] = 960
            with open(cfg_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(cfg, f, default_flow_style=False, allow_unicode=True)
            print(f"[CẬP NHẬT] Đã trỏ settings.yaml sang model V4 Medium!")
        print("=" * 68)
    else:
        print(f"[CẢNH BÁO] Không tìm thấy file {best_pt}")


if __name__ == "__main__":
    from multiprocessing import freeze_support
    freeze_support()
    main()
