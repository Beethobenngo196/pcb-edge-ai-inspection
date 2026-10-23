import serial


class SerialCommunicator:
    def __init__(self, port_name, baudrate=115200):
        """
        Ham khoi tao. Tuong duong voi viec setup cac thanh ghi UART.

        Neu khong mo duoc cong COM (chua cam mach, chua mo Proteus, sai ten
        cong...), chuong trinh se KHONG crash nua ma tu dong chuyen sang
        "che do mo phong" (self.ser = None): van chay duoc toan bo pipeline
        camera + AI + tracking de test, chi la khong gui UART that su, va
        se in canh bao ro rang moi lan dang le phai gui.
        """
        print(f"[INFO] Dang ket noi cong {port_name} voi toc do {baudrate} bps...")

        self.port_name = port_name
        self.ser = None

        try:
            self.ser = serial.Serial(port_name, baudrate, timeout=1)
            print("[INFO] Mo cong COM thanh cong!")
        except serial.SerialException as e:
            print(
                f"[CANH BAO] Khong mo duoc cong {port_name}: {e}\n"
                f"[CANH BAO] Se chay o CHE DO MO PHONG (khong gui UART that), "
                f"kiem tra lai day cam / da mo Proteus / dung ten cong chua."
            )

    def send_defect_data(self, error_code, x, y):
        """
        Ham nay se duoc goi moi khi YOLO soi ra loi.
        Nhiem vu: Goi 5 con so thanh mang byte va gui di.
        """
        packet = bytearray([0xAA, error_code, x, y, 0x55])

        if self.ser is None:
            # Che do mo phong: khong co cong COM, chi log ra de biet pipeline
            # van dang phat hien loi dung, khong lam gian doan vong lap chinh.
            print(f"[UART-SIM] (chua ket noi) se gui loi {error_code} tai ({x}, {y})")
            return

        try:
            self.ser.write(packet)
            print(f"[UART] Da gui loi {error_code} tai toa do ({x}, {y})")
        except serial.SerialException as e:
            # Rot day/mat ket noi giua chung -> khong crash, tu dong chuyen
            # sang che do mo phong cho cac lan gui sau.
            print(f"[CANH BAO] Mat ket noi cong {self.port_name} khi dang gui: {e}")
            self.ser = None

    def close(self):
        """Ham don dep, nha cong COM ra khi tat phan mem"""
        if self.ser is not None and self.ser.is_open:
            self.ser.close()
            print("[INFO] Da dong cong COM an toan.")   