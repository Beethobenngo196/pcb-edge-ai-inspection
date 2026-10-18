// ==========================================
// GHI CHU: Fosc = 20MHz (lay tu file project .mcppi cua ban).
// Neu ban doi thach anh, PHAI tinh lai TMR0_RELOAD trong Timer0_Init().
// ==========================================

// ==========================================
// BIEN TOAN CUC (GLOBAL VARIABLES)
// ==========================================
int buoc_nhan = 0;
unsigned short ma_loi, toa_do_x, toa_do_y;
int co_du_lieu_moi = 0;      // Co bao hieu da nhan du 1 khung UART hop le

// --- Dieu khien relay khong chan CPU (non-blocking) ---
#define RELAY_ON_TIME_MS 300   // Thoi gian giu relay bat (ms)
int relay_dang_bat = 0;         // Co: relay dang trong chu ky day
unsigned long relay_moc_thoi_gian = 0;  // Moc milli_giay luc bat relay

// --- Bo dem milli-giay toan cuc, duoc Timer0 cap nhat trong ISR ---
volatile unsigned long milli_giay = 0;

// Gia tri nap lai cho TMR0 de tao tick ~1ms voi Fosc=20MHz, prescaler 1:32
// Fosc/4 = 5MHz => 1 chu ky = 0.2us; voi prescaler 32 => 6.4us/tick
// Can 1ms / 6.4us = ~156 tick => TMR0 nap lai = 256 - 156 = 100
#define TMR0_RELOAD 100

// ==========================================
// HAM DOC THOI GIAN AN TOAN (ATOMIC READ)
// ==========================================
unsigned long get_milli_giay_safe() {
    unsigned long safe_value;
    GIE_bit = 0;              // Khoa ngat toan cuc de tranh doc sai byte
    safe_value = milli_giay;  // Chep toan ven 4 byte
    GIE_bit = 1;              // Mo khoa ngat ngay lap tuc
    return safe_value;
}

// ==========================================
// HAM NGAT (INTERRUPT SERVICE ROUTINE)
// ==========================================
void interrupt() {

    // --- 1. Ngat nhan UART (RX): may trang thai loc khung 5 byte ---
    if (RCIF_bit) {
        unsigned short incoming_byte = UART1_Read();

        switch (buoc_nhan) {
            case 0:
                if (incoming_byte == 0xAA) buoc_nhan = 1;
                break;
            case 1:
                ma_loi = incoming_byte;
                buoc_nhan = 2;
                break;
            case 2:
                toa_do_x = incoming_byte;
                buoc_nhan = 3;
                break;
            case 3:
                toa_do_y = incoming_byte;
                buoc_nhan = 4;
                break;
            case 4:
                if (incoming_byte == 0x55) {
                    co_du_lieu_moi = 1;   // Nhan du khung hop le -> bao cho main()
                }
                buoc_nhan = 0;   // Dung hay sai deu quay ve trang thai cho START_BYTE
                break;
            default:
                buoc_nhan = 0;
                break;
        }
    }

    // --- 2. Ngat Timer0: dem milli-giay, KHONG lam gian doan UART ---
    if (TMR0IF_bit) {
        TMR0IF_bit = 0;
        TMR0 = TMR0_RELOAD;
        milli_giay++;
    }
}

// ==========================================
// KHOI TAO TIMER0 (tick ~1ms, dung de dinh thoi khong chan CPU)
// ==========================================
void Timer0_Init() {
    // T0CS=0 (dung xung noi Fosc/4), PSA=0 (gan prescaler cho Timer0),
    // PS<2:0>=100 (prescaler 1:32)
    OPTION_REG = 0x04;
    TMR0 = TMR0_RELOAD;
    TMR0IE_bit = 1;
    TMR0IF_bit = 0;
}

// ==========================================
// CHUONG TRINH CHINH (MAIN LOOP)
// ==========================================
void main() {
    // 1. Cau hinh phan cung
    ANSEL  = 0;   // Tat chuc nang Analog
    ANSELH = 0;   // Cau hinh toan bo chan thanh Digital (So)

    TRISD = 0x00; // Dat PORTD lam cong xuat (Output) de dk ro-le
    PORTD = 0x00; // Ban dau tat het ro-le

    // 2. Khoi tao UART
    UART1_Init(115200);
    Delay_ms(100);        // Doi 100ms cho UART on dinh (chi chay 1 lan luc khoi dong)

    // 3. Khoi tao Timer0 de dem milli-giay khong chan CPU
    Timer0_Init();

    // 4. Kich hoat ngat
    RCIE_bit = 1;   // Bat ngat UART RX
    PEIE_bit = 1;   // Bat ngat ngoai vi
    GIE_bit  = 1;   // Bat ngat toan cuc

    // 5. Vong lap Real-time
    while (1) {

        // --- (A) Co khung UART moi hop le -> kich hoat co cau chap hanh ---
        if (co_du_lieu_moi == 1) {
            co_du_lieu_moi = 0;   // Ha co ngay. KHONG tat RCIE nua (khac ban cu),
                                   // nen van nhan duoc khung tiep theo binh thuong.

            // Model AI hien tai co 6 lop: missing_hole(0), mouse_bite(1),
            // open_circuit(2), short(3), spur(4), spurious_copper(5).
            // Khong co lop "tot", nen MOI ma loi hop le (0..5) deu la 1 loi
            // that su va can day board ra khoi bang chuyen.
            switch (ma_loi) {
                case 0:  // missing_hole
                case 1:  // mouse_bite
                case 2:  // open_circuit
                case 3:  // short
                case 4:  // spur
                case 5:  // spurious_copper
                    PORTD.F0 = 1;                  // Bat relay day board loi ra
                    relay_dang_bat = 1;
                    relay_moc_thoi_gian = get_milli_giay_safe(); // [UPDATE] Doc thoi gian an toan
                    break;
                default:
                    // Ma loi la / nhieu duong truyen -> bo qua, khong kich relay
                    break;
            }
        }

        // --- (B) Tu tat relay sau dung RELAY_ON_TIME_MS, KHONG dung Delay_ms
        //         (Delay_ms chan toan bo CPU va co the lam mat du lieu UART den) ---
        if (relay_dang_bat) {
            if ((get_milli_giay_safe() - relay_moc_thoi_gian) >= RELAY_ON_TIME_MS) { // [UPDATE] Doc thoi gian an toan
                PORTD.F0 = 0;
                relay_dang_bat = 0;
            }
        }
    }
}