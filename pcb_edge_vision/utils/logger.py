import datetime
import os

class DefectLogger:
    def __init__(self, log_dir="logs"):
        """Khởi tạo sổ ghi chép"""
        # 1. Nếu chưa có thư mục 'logs', tự động tạo mới
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 2. Đặt tên file nhật ký theo ngày hôm nay (VD: log_2026-08-22.txt)
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        self.log_file = f"{log_dir}/log_{today}.txt"
        
    def log_defect(self, error_code, x, y):
        """Hàm này được gọi để ghi 1 dòng lỗi vào file"""
        # Lấy giờ phút giây hiện tại
        now = datetime.datetime.now().strftime("%H:%M:%S")
        
        # Soạn nội dung cần ghi
        message = f"[{now}] PHÁT HIỆN: Lỗi mã {error_code} tại tọa độ X:{x}, Y:{y}\n"
        
        # Mở file và viết chèn thêm vào cuối file (chế độ 'a' - append)
        with open(self.log_file, "a", encoding="utf-8") as file:
            file.write(message)