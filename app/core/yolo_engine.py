from ultralytics import YOLO


class PCBDefectDetector:
    def __init__(self, model_path):
        """
        Ham khoi tao. Giong nhu cap phat bo nho cho struct trong C.
        """
        print(f"[INFO] Dang tai mo hinh YOLO tu: {model_path}...")

        self.model = YOLO(model_path)

        print("[INFO] Tai mo hinh thanh cong!")
        print(f"[INFO] Danh sach lop (classes) cua model: {self.model.names}")

    def detect_frame(self, frame, **kwargs):
        """
        Ham quet loi (KHONG tracking). Truyen anh (frame) vao model va hung
        ket qua. Giu nguyen ham nay de test.py (xu ly video roi, khong can
        theo doi ID qua cac frame) khong bi anh huong.
        """
        results = self.model(frame, **kwargs)

        return results

    def track_frame(self, frame, **kwargs):
        """
        Ham quet loi CO tracking (ByteTrack). Giong detect_frame nhung moi
        box tra ve them thuoc tinh box.id: 1 so nguyen on dinh, dai dien cho
        CUNG 1 vat the (board loi) xuyen suot nhieu frame lien tiep.

        persist=True bat buoc phai co: no bao ultralytics GIU LAI trang thai
        tracker giua cac lan goi ham nay, thay vi coi moi frame la 1 video moi
        (neu thieu persist=True, moi frame se bi gan lai ID tu dau, tracking
        vo nghia).

        LUU Y: neu chay bao loi thieu package (vi du "lap"/"lapx"), can
        cai them: pip install lapx --break-system-packages
        """
        results = self.model.track(
            frame,
            persist=True,
            tracker="bytetrack.yaml",
            **kwargs,
        )

        return results