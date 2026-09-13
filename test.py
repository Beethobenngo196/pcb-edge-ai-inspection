import cv2
import time
from pcb_edge_vision.core.yolo_engine import PCBDefectDetector

def test_video():
    print("--- CHẠY TEST VIDEO BĂNG CHUYỀN ---")
    
    # 1. Khởi tạo AI
    ai_detector = PCBDefectDetector("pcb_edge_vision/models/pcb_defect_model.pt")
    
    # 2. Đường dẫn tới file video của bạn
    video_path = "D:\\pcb-edge-ai-inspection\\dataset\\pcb_conveyor_simulation.mp4" 

    # Kích thước cửa sổ hiển thị video cố định (HD 720p)
    window_width = 1280
    window_height = 720
    
    # Mở video
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"❌ LỖI: Không thể mở được video tại: {video_path}")
        return

    print(">>> ĐANG PHÁT VIDEO (Nhấn phím 'q' để thoát) <<<")
    
    while True:
        ret, frame = cap.read()
        
        # Nếu hết video thì thoát vòng lặp
        if not ret:
            print("Đã phát hết video!")
            break
            
        # 3. Đưa từng khung hình (frame) vào AI quét
        results = ai_detector.detect_frame(frame)
        
        # Lấy hình ảnh gốc đã được AI vẽ khung (bounding box)
        annotated_frame = results[0].plot()
        
        # 4. SỬA LỖI Ở ĐÂY: Dùng 2 biến kích thước bạn đã tạo để thu nhỏ ảnh
        resize_frame = cv2.resize(annotated_frame, (window_width, window_height))
        
        # 5. SỬA LỖI Ở ĐÂY: Đưa khung hình ĐÃ RESIZE vào lệnh imshow (thay vì ảnh gốc)
        cv2.imshow("Test Video Bang Chuyen", resize_frame)

        # Điều chỉnh tốc độ khung hình (Delay)
        # 30ms tương đương khoảng 30 FPS. Nếu video chạy quá nhanh, tăng số 30 lên.
        if cv2.waitKey(30) & 0xFF == ord('q'):
            print("Người dùng đã dừng video.")
            break

    # Dọn dẹp sau khi chạy xong
    cap.release()
    cv2.destroyAllWindows()
    print("--- ĐÃ ĐÓNG TRÌNH PHÁT VIDEO ---")

if __name__ == "__main__":
    test_video()