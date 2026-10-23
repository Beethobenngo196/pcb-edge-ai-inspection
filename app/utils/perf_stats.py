import time


class PerfStats:
    """
    Do FPS va latency tung buoc (doc camera / suy luan AI / tong vong lap)
    de co so lieu BASELINE truoc khi toi uu (tach luong Producer/Consumer,
    TensorRT...). Chi in ra console dinh ky, khong ghi file, khong anh
    huong gi den logic chinh cua he thong.
    """

    def __init__(self, report_every_sec=2.0):
        self.report_every_sec = report_every_sec
        self.reset()

    def reset(self):
        self.frame_count = 0
        self.sum_camera_ms = 0.0
        self.sum_ai_ms = 0.0
        self.sum_total_ms = 0.0
        self.window_start = time.perf_counter()

    def record(self, camera_ms, ai_ms, total_ms):
        """
        Goi ham nay 1 lan moi vong lap, truyen vao thoi gian (ms) da do duoc
        cho tung buoc. Tu dong in ra bang tong ket sau moi report_every_sec giay.
        """
        self.frame_count += 1
        self.sum_camera_ms += camera_ms
        self.sum_ai_ms += ai_ms
        self.sum_total_ms += total_ms

        elapsed = time.perf_counter() - self.window_start
        if elapsed >= self.report_every_sec and self.frame_count > 0:
            fps = self.frame_count / elapsed
            avg_camera = self.sum_camera_ms / self.frame_count
            avg_ai = self.sum_ai_ms / self.frame_count
            avg_total = self.sum_total_ms / self.frame_count
            print(
                f"[PERF] FPS={fps:5.1f}  |  "
                f"camera={avg_camera:6.1f}ms  "
                f"ai={avg_ai:6.1f}ms  "
                f"tong_vong_lap={avg_total:6.1f}ms  "
                f"(muc tieu SRS: >=30 FPS, <=150ms/vong)"
            )
            self.reset()