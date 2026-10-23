import datetime
import os


class DefectLogger:
    def __init__(self, log_dir="logs"):
        """Khởi tạo logger, tạo thư mục nếu chưa có."""
        os.makedirs(log_dir, exist_ok=True)
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        self.log_file = f"{log_dir}/log_{today}.txt"

    def log_defect(self, error_code, error_name, cx_px, cy_px, x_uart, y_uart, conf=None, track_id=None):
        """
        Ghi 1 dòng lỗi vào file log.

        Params:
            error_code  : int   – mã lỗi (0-5)
            error_name  : str   – tên lỗi
            cx_px       : float – tọa độ X tâm bounding box (pixel, hệ frame gốc)
            cy_px       : float – tọa độ Y tâm bounding box (pixel, hệ frame gốc)
            x_uart      : int   – tọa độ X chuẩn hóa 0-255 (để gửi UART)
            y_uart      : int   – tọa độ Y chuẩn hóa 0-255 (để gửi UART)
            conf        : float – độ tin cậy (0.0–1.0)
            track_id    : int|None – ID ByteTrack (None trong chế độ AOI tĩnh)
        """
        now      = datetime.datetime.now().strftime("%H:%M:%S")
        conf_str = f"{conf:.2f}" if conf is not None else "N/A"
        tid_str  = str(track_id) if track_id is not None else "N/A"

        message = (
            f"[{now}] PHAT HIEN: "
            f"ma={error_code} | ten={error_name} | "
            f"cx_px={int(cx_px)} cy_px={int(cy_px)} | "
            f"X={x_uart} Y={y_uart} | "
            f"conf={conf_str} | track_id={tid_str}\n"
        )

        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(message)

