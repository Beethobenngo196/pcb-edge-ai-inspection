import serial

class SerialCommunicator:
    def __init__(self, port_name, baudrate=115200):
        """
        Hàm khởi tạo. Tương đương với việc setup các thanh ghi UART.
        """
        print(f"[INFO] Đang kết nối cổng {port_name} với tốc độ {baudrate} bps...")
        
        # Mở cổng COM và lưu vào biến con trỏ 'self.ser'
        self.ser = serial.Serial(port_name, baudrate, timeout=1)
        
        print("[INFO] Mở cổng COM thành công!")

    def send_defect_data(self, error_code, x, y):
        """
        Hàm này sẽ được gọi mỗi khi YOLO soi ra lỗi.
        Nhiệm vụ: Gói 5 con số thành mảng byte và gửi đi.
        """
        # 1. Tạo mảng 5 byte theo chuẩn giao thức của bạn
        packet = bytearray([0xAA, error_code, x, y, 0x55])
        
        # 2. Đẩy gói tin vào đường ống UART
        self.ser.write(packet)
        
        print(f"[UART] Đã gửi lỗi {error_code} tại tọa độ ({x}, {y})")

    def close(self):
        """Hàm dọn dẹp, nhả cổng COM ra khi tắt phần mềm"""
        if self.ser.is_open:
            self.ser.close()
            print("[INFO] Đã đóng cổng COM an toàn.")