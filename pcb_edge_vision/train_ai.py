from ultralytics import YOLO


def main():
    # Fine-tune TIEP tu model da train (khong train lai tu dau) -> giu lai
    # kien thuc cu, thich nghi them voi augmentation moi, nhanh hon nhieu
    # so voi train lai tu yolov8n.pt.
    model = YOLO('pcb_edge_vision/models/pcb_defect_model.pt')

    print("[*] Fine-tune voi augmentation manh ve mau/anh sang (domain randomization)...")
    print("[*] Muc tieu: giam phu thuoc vao mau nen cua DUNG loai mach trong dataset,")
    print("[*] ep model hoc theo HINH DANG loi thay vi mau sac.")

    results = model.train(
        data='dataset/data.yaml',
        epochs=50,
        imgsz=640,
        batch=8,
        device=0,
        workers=0,
        project='Smart_AOI_Runs',
        name='yolov8_pcb_model_v2_augmented',

        # --- Augmentation MAU SAC / ANH SANG (quan trong nhat cho van de nay) ---
        hsv_h=0.5,      # Xoay tong mau (hue) manh: gia lap mach xanh -> do -> vang...
                        # Mac dinh chi 0.015 (rat nhe), ta tang len 0.5 de "gia lap"
                        # nhieu mau solder mask khac nhau tu DUNG anh dataset hien co.
        hsv_s=0.7,      # Do bao hoa mau (saturation) dao dong manh
        hsv_v=0.4,      # Do sang (value/brightness) dao dong, gia lap dieu kien
                        # anh sang khac nhau (den xuong, den LED, anh sang tu nhien...)

        # --- Augmentation HINH HOC (giu muc mac dinh hop ly, khong doi manh) ---
        degrees=10,     # Xoay nhe, mach thuc te co the dat hoi lech
        translate=0.1,
        scale=0.3,
        fliplr=0.5,     # Lat ngang - mach PCB doi xung ve mat hinh hoc nen an toan
        flipud=0.0,     # KHONG lat doc: lo dieu huong (via) co the co huong nhat dinh,
                         # lat doc de gay nham lan khong thuc te

        # --- Mosaic/mixup: ghep nhieu anh lam 1, tang da dang bo cuc ---
        mosaic=1.0,
        mixup=0.1,

        patience=20,    # Dung som neu 20 epoch lien tiep khong cai thien (tranh overfit)
    )
    print("[*] Fine-tune hoan tat! Model moi nam trong Smart_AOI_Runs/yolov8_pcb_model_v2_augmented/weights/best.pt")
    print("[*] SO SANH mAP50 cua ban nay voi ban cu (~0.876) de xem co cai thien khong.")
    print("[*] QUAN TRONG HON: dem thu tren video/anh MACH KHAC (ngoai dataset)")
    print("[*] de danh gia kha nang tong quat hoa thuc te, vi mAP tren tap val")
    print("[*] van la cung phan phoi voi tap train, khong phan anh mach khac.")


if __name__ == '__main__':
    from multiprocessing import freeze_support
    freeze_support()

    main()