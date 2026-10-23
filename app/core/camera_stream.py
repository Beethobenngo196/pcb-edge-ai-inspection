import glob
import os
import random
import cv2


class CameraStream:
    """
    Module cung cấp luồng hình ảnh:
    - Nếu source là thư mục ảnh (vd: 'dataset/images/val'):
      -> Chế độ duyệt ảnh PCB tĩnh từ dataset (mô phỏng máy AOI).
      -> Có thể chuyển ảnh tiếp theo, lùi lại, hoặc chọn ngẫu nhiên.
    - Nếu source là file ảnh đơn lẻ (.jpg, .png):
      -> Nạp ảnh đó để soi lỗi.
    - Nếu source là số (0, 1...) hoặc file video (.mp4):
      -> Mở VideoCapture (webcam / camera USB / video).
    """

    def __init__(self, camera_source=0):
        self.source = camera_source
        self.is_image_folder = False
        self.is_single_image = False
        self.image_files = []
        self.current_idx = 0
        self.current_frame = None
        self.cap = None

        # 1. Kiểm tra nếu là thư mục ảnh
        if isinstance(camera_source, str) and os.path.isdir(camera_source):
            self.is_image_folder = True
            exts = ("*.jpg", "*.jpeg", "*.png", "*.bmp")
            for ext in exts:
                self.image_files.extend(glob.glob(os.path.join(camera_source, ext)))
            self.image_files.sort()
            print(f"[INFO] Che do thu muc anh: tim thay {len(self.image_files)} anh trong '{camera_source}'")
            if self.image_files:
                self._load_current_image()
            else:
                print(f"[CANH BAO] Khong tim thay anh nao trong '{camera_source}'!")

        # 2. Kiểm tra nếu là 1 file ảnh cụ thể
        elif isinstance(camera_source, str) and os.path.isfile(camera_source) and camera_source.lower().endswith((".jpg", ".jpeg", ".png", ".bmp")):
            self.is_single_image = True
            self.image_files = [camera_source]
            print(f"[INFO] Che do anh don le: '{camera_source}'")
            self._load_current_image()

        # 3. Camera / Webcam / Video stream
        else:
            src = int(camera_source) if str(camera_source).isdigit() else camera_source
            print(f"[INFO] Dang mo Camera/Video tu nguon: {src}...")
            self.cap = cv2.VideoCapture(src)
            if not self.cap.isOpened():
                print(f"❌ LOI: Khong the ket noi voi Camera/Video tu nguon: {src}")

    def _load_current_image(self):
        if 0 <= self.current_idx < len(self.image_files):
            img_path = self.image_files[self.current_idx]
            self.current_frame = cv2.imread(img_path)
            return self.current_frame
        return None

    def get_frame(self):
        """Lấy frame / ảnh hiện tại"""
        if self.is_image_folder or self.is_single_image:
            return self.current_frame
        elif self.cap is not None:
            ret, frame = self.cap.read()
            return frame if ret else None
        return None

    def next_image(self):
        """Chuyển sang ảnh PCB kế tiếp trong thư mục"""
        if self.image_files:
            self.current_idx = (self.current_idx + 1) % len(self.image_files)
            return self._load_current_image()
        return None

    def prev_image(self):
        """Quay lại ảnh PCB trước đó"""
        if self.image_files:
            self.current_idx = (self.current_idx - 1 + len(self.image_files)) % len(self.image_files)
            return self._load_current_image()
        return None

    def random_image(self):
        """Chọn ngẫu nhiên 1 ảnh PCB bất kỳ"""
        if self.image_files:
            self.current_idx = random.randint(0, len(self.image_files) - 1)
            return self._load_current_image()
        return None

    def get_current_filename(self):
        if self.image_files and 0 <= self.current_idx < len(self.image_files):
            return os.path.basename(self.image_files[self.current_idx])
        return "live_camera"

    def get_current_image_path(self):
        if self.image_files and 0 <= self.current_idx < len(self.image_files):
            return self.image_files[self.current_idx]
        return None

    def get_current_label_path(self):
        """Tìm file nhãn Ground Truth .txt tương ứng trong dataset/labels"""
        img_path = self.get_current_image_path()
        if not img_path:
            return None

        # Thay thế thư mục 'images' thành 'labels' và đổi đuôi sang .txt
        norm_path = os.path.normpath(img_path)
        parts = norm_path.split(os.sep)
        if "images" in parts:
            idx = parts.index("images")
            parts[idx] = "labels"
            label_candidate = os.sep.join(parts)
            label_candidate = os.path.splitext(label_candidate)[0] + ".txt"
            if os.path.exists(label_candidate):
                return label_candidate
        return None

    def get_progress_info(self):
        """Trả về (chỉ số hiện tại + 1, tổng số ảnh)"""
        total = len(self.image_files)
        curr = (self.current_idx + 1) if total > 0 else 0
        return curr, total

    def is_dataset_mode(self):
        return self.is_image_folder or self.is_single_image

    def release(self):
        if self.cap is not None:
            self.cap.release()
            print("[INFO] Da giai phong Camera an toan.")
