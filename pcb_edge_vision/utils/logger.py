import datetime
import os


class DefectLogger:
    def __init__(self, log_dir="logs"):
        """Khởi tạo sổ ghi chép"""
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        today = datetime.datetime.now().strftime("%Y-%m-%d")
        self.log_file = f"{log_dir}/log_{today}.txt"

    def log_defect(self, error_code, error_name, x, y, conf=None, track_id=None):
        """Ghi 1 dòng lỗi vào file — đầy đủ thông tin để kiểm tra sau"""
        now = datetime.datetime.now().strftime("%H:%M:%S")

        conf_str = f"{conf:.2f}" if conf is not None else "N/A"
        tid_str  = str(track_id) if track_id is not None else "N/A"

        message = (
            f"[{now}] PHAT HIEN: "
            f"ma={error_code} | ten={error_name} | "
            f"X={x} Y={y} | conf={conf_str} | track_id={tid_str}\n"
        )

        with open(self.log_file, "a", encoding="utf-8") as file:
            file.write(message)