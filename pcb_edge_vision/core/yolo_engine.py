from ultralytics import YOLO

class PCBDefectDetector:
    def __init__(self, model_path):
        """
        Hàm khởi tạo. Giống như cấp phát bộ nhớ cho struct trong C.
        """
        print(f"[INFO] Đang tải mô hình YOLO từ: {model_path}...")
        
        self.model = YOLO(model_path) 
        
        print("[INFO] Tải mô hình thành công!")

    def detect_frame(self, frame):
        """
        Hàm quét lỗi. Truyền ảnh (frame) vào model và hứng kết quả.
        """
        # Model YOLO quét ảnh và trả về danh sách các lỗi tìm thấy
        results = self.model(frame)
        
        return results