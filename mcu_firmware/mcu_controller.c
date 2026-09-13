// ==========================================
// BI?N TOÀN C?C (GLOBAL VARIABLES)
// ==========================================
int buoc_nhan = 0;
unsigned short ma_loi, toa_do_x, toa_do_y;
int co_du_lieu_moi = 0; // C? báo hi?u (Flag)

// ==========================================
// HÀM NG?T (INTERRUPT SERVICE ROUTINE)
// ==========================================
void interrupt() {
    // Ki?m tra xem có dúng là ng?t do UART nh?n d? li?u không
    if (RCIF_bit) {
        unsigned short incoming_byte = UART1_Read(); // B?t 1 byte v?a bay t?i

        // Máy tr?ng thái l?c 5 byte
        if (buoc_nhan == 0 && incoming_byte == 0xAA) {
            buoc_nhan = 1;
        }
        else if (buoc_nhan == 1) {
            ma_loi = incoming_byte;
            buoc_nhan = 2;
        }
        else if (buoc_nhan == 2) {
            toa_do_x = incoming_byte;
            buoc_nhan = 3;
        }
        else if (buoc_nhan == 3) {
            toa_do_y = incoming_byte;
            buoc_nhan = 4;
        }
        else if (buoc_nhan == 4 && incoming_byte == 0x55) {
            co_du_lieu_moi = 1; // Nh?n d? 5 toa -> D?ng c?
            buoc_nhan = 0;
        }
        else {
            buoc_nhan = 0; // D? li?u nhi?u -> Reset
        }
    }
}

// ==========================================
// CHUONG TRÌNH CHÍNH (MAIN LOOP)
// ==========================================
void main() {
    // 1. C?u hình ph?n c?ng
    ANSEL  = 0; // T?t ch?c nang Analog
    ANSELH = 0; // C?u hình toàn b? chân thành Digital (S?)

    TRISD = 0x00; // Ð?t PORTD làm c?ng xu?t (Output) d? dk ro-le
    PORTD = 0x00; // Ban d?u t?t h?t ro-le

    // 2. Kh?i t?o UART
    UART1_Init(115200); // mikroC t? d?ng tính toán thanh ghi baudrate
    Delay_ms(100);      // Ð?i 100ms cho UART ?n d?nh

    // 3. Kích ho?t Ng?t nh?n d? li?u (RX Interrupt)
    RCIE_bit = 1; // B?t ng?t UART RX
    PEIE_bit = 1; // B?t ng?t ngo?i vi
    GIE_bit  = 1; // B?t ng?t toàn c?c

    // 4. Vòng l?p Real-time
    while(1) {
        if (co_du_lieu_moi == 1) {

            RCIE_bit = 0; // T?m t?t ng?t d? t?p trung x? lý co khí

            // --- TH?C THI CO KHÍ ---
            if (ma_loi == 1) {
                // Kích Relay d?y bo m?ch m? ra (Ví d? chân RD0)
                PORTD.F0 = 1;
                Delay_ms(300);
                PORTD.F0 = 0;
            }
            // Thêm các (ma_loi == 2, 3...) cho các lo?i l?i khác ? dây

            co_du_lieu_moi = 0; // H? c?
            RCIE_bit = 1;       // B?t ng?t l?i dón bo m?ch ti?p theo
        }
    }
}