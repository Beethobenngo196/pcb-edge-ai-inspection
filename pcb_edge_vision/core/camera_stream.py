import cv2

class CameraStream:
    def __init__(self, camera_source=0):
        """
        Khởi tạo kết nối với Camera.
        camera_source: 0 (webcam mặc định của laptop), hoặc đường dẫn video test (VD: 'test.mp4')
        """
        print(f"[INFO] Đang mở Camera từ nguồn: {camera_source}...")
        self.cap = cv2.VideoCapture(camera_source)
        
        if not self.cap.isOpened():
            print("❌ LỖI: Không thể kết nối với Camera!")

    def get_frame(self):
        """
        Hàm này sẽ được gọi liên tục trong vòng lặp while.
        Nhiệm vụ: Cắn 1 khung hình (frame) từ camera trả về.
        """
        # 1. Đọc khung hình từ camera
        ret, frame = self.cap.read()
        
        # 2. Kiểm tra xem có đọc thành công không (giống như check con trỏ NULL trong C)
        if ret:
            return frame
        else:
            return None

    def release(self):
        """Hàm dọn dẹp, tắt đèn camera khi không dùng nữa"""
        self.cap.release()
        print("[INFO] Đã giải phóng Camera an toàn.")