import cv2
import yaml
from core.yolo_engine import PCBDefectDetector
from core.serial_comm import SerialCommunicator
from core.camera_stream import CameraStream

# 1. Gọi "Người thư ký" vào
from utils.logger import DefectLogger

def main():
    print("--- KHỞI ĐỘNG HỆ THỐNG KIỂM TRA BĂNG CHUYỀN ---")
    
    print("[INFO] Đang tải cấu hình hệ thống...")
    with open("pcb_edge_vision/configs/settings.yaml", "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)
        
    ai_detector = PCBDefectDetector(config['ai_model']['weights_path'])
    uart = SerialCommunicator(config['serial']['port'], config['serial']['baudrate']) 
    camera = CameraStream(config['camera']['source'])
    
    # 2. Khởi tạo cuốn sổ nhật ký
    logger = DefectLogger()
    
    try:
        print("\n>>> BẮT ĐẦU CHẠY BĂNG CHUYỀN (Nhấn phím 'q' để dừng) <<<\n")
        
        while True:
            frame = camera.get_frame()
            
            if frame is None:
                print("Đã mất tín hiệu camera hoặc phát hết video!")
                break

            results = ai_detector.detect_frame(frame)
            
            boxes = results[0].boxes
            if len(boxes) > 0:
                first_box = boxes[0]
                confidence = first_box.conf[0].item()
                
                if confidence >= config['ai_model']['confidence_threshold']:
                    error_code = int(first_box.cls[0].item()) 
                    x = int(first_box.xywh[0][0].item()) % 255
                    y = int(first_box.xywh[0][1].item()) % 255
                    
                    uart.send_defect_data(error_code, x, y)
                    
                    # 3. Kêu thư ký ghi chép lại ngay lập tức!
                    logger.log_defect(error_code, x, y)

            annotated_frame = results[0].plot()
            cv2.imshow("He thong Kiem tra Bo mach", annotated_frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("Người dùng đã ra lệnh dừng hệ thống.")
                break
                
    finally:
        camera.release()
        uart.close()
        cv2.destroyAllWindows()
        print("--- HỆ THỐNG TẮT AN TOÀN ---")

if __name__ == "__main__":
    main()