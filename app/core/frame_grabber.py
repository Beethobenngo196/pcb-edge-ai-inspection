import threading
import time

import cv2

from core.camera_stream import CameraStream


class FrameGrabber:
    """
    Luong Producer: chay rieng, lien tuc doc camera va giu san FRAME MOI NHAT
    trong bo nho dung chung voi luong chinh (Consumer).

    Neu luong AI (Consumer) xu ly cham hon toc do camera, cac frame cu se bi
    "de len" (drop) thay vi bi don lai trong hang doi -> Consumer luon lay
    duoc frame gan voi thoi diem hien tai nhat co the.

    Neu nguon la FILE VIDEO (co FPS co dinh trong metadata), Producer se tu
    dong "ghim" toc do doc theo DUNG FPS goc cua file - tranh tinh trang
    doc nhanh het muc CPU cho phep lam video "chay nhanh nhu tua". Viec nay
    chi anh huong toc do Producer doc frame, KHONG he lam cham Consumer (AI
    xu ly + gui UART) o main.py, vi 2 luong hoan toan doc lap voi nhau.
    """

    def __init__(self, camera_source):
        self._camera = CameraStream(camera_source)
        self._lock = threading.Lock()
        self._latest_frame = None
        self._frame_id = 0
        self._camera_ms = 0.0
        self._running = False
        self._thread = None

        self._frame_interval_sec = self._compute_frame_interval()

    def _compute_frame_interval(self):
        """
        Doc FPS goc tu metadata cua nguon (chi co y nghia voi file video;
        webcam thuong tra ve 0 hoac gia tri khong dang tin). Neu hop le
        (1-240 FPS), tra ve khoang thoi gian can giu giua 2 frame (giay).
        Neu khong xac dinh duoc, tra ve None -> Producer doc nhanh het muc
        nhu truoc (hanh vi cu, phu hop webcam/camera that).
        """
        fps = self._camera.cap.get(cv2.CAP_PROP_FPS)
        if fps and 1 <= fps <= 240:
            print(f"[INFO] Nguon bao FPS goc = {fps:.1f} -> Producer se ghim dung toc do nay")
            return 1.0 / fps

        print("[INFO] Khong xac dinh duoc FPS goc cua nguon -> Producer doc nhanh het muc CPU")
        return None

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        return self

    def _loop(self):
        while self._running:
            t0 = time.perf_counter()
            frame = self._camera.get_frame()
            t1 = time.perf_counter()

            with self._lock:
                self._latest_frame = frame
                self._frame_id += 1
                self._camera_ms = (t1 - t0) * 1000

            if frame is None:
                # Het video / mat tin hieu camera -> Producer tu dung
                self._running = False
                break

            # Ghim dung FPS goc cua video (neu xac dinh duoc) - chi delay
            # o day, trong luong Producer, KHONG dung gi den Consumer.
            if self._frame_interval_sec is not None:
                elapsed = time.perf_counter() - t0
                remaining = self._frame_interval_sec - elapsed
                if remaining > 0:
                    time.sleep(remaining)

    def get_latest(self):
        """
        Tra ve (frame, frame_id, camera_ms) moi nhat hien co.
        frame co the la None neu chua doc duoc frame dau tien, hoac camera da mat.
        """
        with self._lock:
            return self._latest_frame, self._frame_id, self._camera_ms

    def is_running(self):
        return self._running

    def stop(self):
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        self._camera.release()