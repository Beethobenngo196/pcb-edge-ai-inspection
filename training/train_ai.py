"""
training/train_ai.py — Fine-tune YOLOv8 model cho PCB defect detection.

Cách dùng (chạy từ thư mục gốc project):
    python training/train_ai.py
"""

from ultralytics import YOLO


def main():
    # Fine-tune TIẾP từ model đã train (không train lại từ đầu)
    model = YOLO("models/pcb_defect_model_V2.pt")

    print("[*] Fine-tune với augmentation mạnh về màu/ánh sáng (domain randomization)...")
    print("[*] Mục tiêu: giảm phụ thuộc vào màu nền, ép model học theo HÌNH DẠNG lỗi.")

    model.train(
        data="dataset/data.yaml",
        epochs=50,
        imgsz=640,
        batch=8,
        device=0,
        workers=0,
        project="training/runs",
        name="yolov8_pcb_model_v3",

        # --- Augmentation màu sắc / ánh sáng ---
        hsv_h=0.5,
        hsv_s=0.7,
        hsv_v=0.4,

        # --- Augmentation hình học ---
        degrees=10,
        translate=0.1,
        scale=0.3,
        fliplr=0.5,
        flipud=0.0,

        # --- Mosaic/mixup ---
        mosaic=1.0,
        mixup=0.1,

        patience=20,
    )
    print("[*] Fine-tune hoàn tất! Weights mới: training/runs/yolov8_pcb_model_v3/weights/best.pt")
    print("[*] Nếu mAP cải thiện, copy best.pt vào models/ và cập nhật settings.yaml.")


if __name__ == "__main__":
    from multiprocessing import freeze_support
    freeze_support()
    main()
