
_interrupt:
	MOVWF      R15+0
	SWAPF      STATUS+0, 0
	CLRF       STATUS+0
	MOVWF      ___saveSTATUS+0
	MOVF       PCLATH+0, 0
	MOVWF      ___savePCLATH+0
	CLRF       PCLATH+0

;mcu_controller.c,11 :: 		void interrupt() {
;mcu_controller.c,13 :: 		if (RCIF_bit) {
	BTFSS      RCIF_bit+0, BitPos(RCIF_bit+0)
	GOTO       L_interrupt0
;mcu_controller.c,14 :: 		unsigned short incoming_byte = UART1_Read(); // B?t 1 byte v?a bay t?i
	CALL       _UART1_Read+0
	MOVF       R0+0, 0
	MOVWF      interrupt_incoming_byte_L1+0
;mcu_controller.c,17 :: 		if (buoc_nhan == 0 && incoming_byte == 0xAA) {
	MOVLW      0
	XORWF      _buoc_nhan+1, 0
	BTFSS      STATUS+0, 2
	GOTO       L__interrupt25
	MOVLW      0
	XORWF      _buoc_nhan+0, 0
L__interrupt25:
	BTFSS      STATUS+0, 2
	GOTO       L_interrupt3
	MOVF       interrupt_incoming_byte_L1+0, 0
	XORLW      170
	BTFSS      STATUS+0, 2
	GOTO       L_interrupt3
L__interrupt22:
;mcu_controller.c,18 :: 		buoc_nhan = 1;
	MOVLW      1
	MOVWF      _buoc_nhan+0
	MOVLW      0
	MOVWF      _buoc_nhan+1
;mcu_controller.c,19 :: 		}
	GOTO       L_interrupt4
L_interrupt3:
;mcu_controller.c,20 :: 		else if (buoc_nhan == 1) {
	MOVLW      0
	XORWF      _buoc_nhan+1, 0
	BTFSS      STATUS+0, 2
	GOTO       L__interrupt26
	MOVLW      1
	XORWF      _buoc_nhan+0, 0
L__interrupt26:
	BTFSS      STATUS+0, 2
	GOTO       L_interrupt5
;mcu_controller.c,21 :: 		ma_loi = incoming_byte;
	MOVF       interrupt_incoming_byte_L1+0, 0
	MOVWF      _ma_loi+0
;mcu_controller.c,22 :: 		buoc_nhan = 2;
	MOVLW      2
	MOVWF      _buoc_nhan+0
	MOVLW      0
	MOVWF      _buoc_nhan+1
;mcu_controller.c,23 :: 		}
	GOTO       L_interrupt6
L_interrupt5:
;mcu_controller.c,24 :: 		else if (buoc_nhan == 2) {
	MOVLW      0
	XORWF      _buoc_nhan+1, 0
	BTFSS      STATUS+0, 2
	GOTO       L__interrupt27
	MOVLW      2
	XORWF      _buoc_nhan+0, 0
L__interrupt27:
	BTFSS      STATUS+0, 2
	GOTO       L_interrupt7
;mcu_controller.c,25 :: 		toa_do_x = incoming_byte;
	MOVF       interrupt_incoming_byte_L1+0, 0
	MOVWF      _toa_do_x+0
;mcu_controller.c,26 :: 		buoc_nhan = 3;
	MOVLW      3
	MOVWF      _buoc_nhan+0
	MOVLW      0
	MOVWF      _buoc_nhan+1
;mcu_controller.c,27 :: 		}
	GOTO       L_interrupt8
L_interrupt7:
;mcu_controller.c,28 :: 		else if (buoc_nhan == 3) {
	MOVLW      0
	XORWF      _buoc_nhan+1, 0
	BTFSS      STATUS+0, 2
	GOTO       L__interrupt28
	MOVLW      3
	XORWF      _buoc_nhan+0, 0
L__interrupt28:
	BTFSS      STATUS+0, 2
	GOTO       L_interrupt9
;mcu_controller.c,29 :: 		toa_do_y = incoming_byte;
	MOVF       interrupt_incoming_byte_L1+0, 0
	MOVWF      _toa_do_y+0
;mcu_controller.c,30 :: 		buoc_nhan = 4;
	MOVLW      4
	MOVWF      _buoc_nhan+0
	MOVLW      0
	MOVWF      _buoc_nhan+1
;mcu_controller.c,31 :: 		}
	GOTO       L_interrupt10
L_interrupt9:
;mcu_controller.c,32 :: 		else if (buoc_nhan == 4 && incoming_byte == 0x55) {
	MOVLW      0
	XORWF      _buoc_nhan+1, 0
	BTFSS      STATUS+0, 2
	GOTO       L__interrupt29
	MOVLW      4
	XORWF      _buoc_nhan+0, 0
L__interrupt29:
	BTFSS      STATUS+0, 2
	GOTO       L_interrupt13
	MOVF       interrupt_incoming_byte_L1+0, 0
	XORLW      85
	BTFSS      STATUS+0, 2
	GOTO       L_interrupt13
L__interrupt21:
;mcu_controller.c,33 :: 		co_du_lieu_moi = 1; // Nh?n d? 5 toa -> D?ng c?
	MOVLW      1
	MOVWF      _co_du_lieu_moi+0
	MOVLW      0
	MOVWF      _co_du_lieu_moi+1
;mcu_controller.c,34 :: 		buoc_nhan = 0;
	CLRF       _buoc_nhan+0
	CLRF       _buoc_nhan+1
;mcu_controller.c,35 :: 		}
	GOTO       L_interrupt14
L_interrupt13:
;mcu_controller.c,37 :: 		buoc_nhan = 0; // D? li?u nhi?u -> Reset
	CLRF       _buoc_nhan+0
	CLRF       _buoc_nhan+1
;mcu_controller.c,38 :: 		}
L_interrupt14:
L_interrupt10:
L_interrupt8:
L_interrupt6:
L_interrupt4:
;mcu_controller.c,39 :: 		}
L_interrupt0:
;mcu_controller.c,40 :: 		}
L_end_interrupt:
L__interrupt24:
	MOVF       ___savePCLATH+0, 0
	MOVWF      PCLATH+0
	SWAPF      ___saveSTATUS+0, 0
	MOVWF      STATUS+0
	SWAPF      R15+0, 1
	SWAPF      R15+0, 0
	RETFIE
; end of _interrupt

_main:

;mcu_controller.c,45 :: 		void main() {
;mcu_controller.c,47 :: 		ANSEL  = 0; // T?t ch?c nang Analog
	CLRF       ANSEL+0
;mcu_controller.c,48 :: 		ANSELH = 0; // C?u hình toàn b? chân thành Digital (S?)
	CLRF       ANSELH+0
;mcu_controller.c,50 :: 		TRISD = 0x00; // Ð?t PORTD làm c?ng xu?t (Output) d? dk ro-le
	CLRF       TRISD+0
;mcu_controller.c,51 :: 		PORTD = 0x00; // Ban d?u t?t h?t ro-le
	CLRF       PORTD+0
;mcu_controller.c,54 :: 		UART1_Init(115200); // mikroC t? d?ng tính toán thanh ghi baudrate
	MOVLW      10
	MOVWF      SPBRG+0
	BSF        TXSTA+0, 2
	CALL       _UART1_Init+0
;mcu_controller.c,55 :: 		Delay_ms(100);      // Ð?i 100ms cho UART ?n d?nh
	MOVLW      3
	MOVWF      R11+0
	MOVLW      138
	MOVWF      R12+0
	MOVLW      85
	MOVWF      R13+0
L_main15:
	DECFSZ     R13+0, 1
	GOTO       L_main15
	DECFSZ     R12+0, 1
	GOTO       L_main15
	DECFSZ     R11+0, 1
	GOTO       L_main15
	NOP
	NOP
;mcu_controller.c,58 :: 		RCIE_bit = 1; // B?t ng?t UART RX
	BSF        RCIE_bit+0, BitPos(RCIE_bit+0)
;mcu_controller.c,59 :: 		PEIE_bit = 1; // B?t ng?t ngo?i vi
	BSF        PEIE_bit+0, BitPos(PEIE_bit+0)
;mcu_controller.c,60 :: 		GIE_bit  = 1; // B?t ng?t toàn c?c
	BSF        GIE_bit+0, BitPos(GIE_bit+0)
;mcu_controller.c,63 :: 		while(1) {
L_main16:
;mcu_controller.c,64 :: 		if (co_du_lieu_moi == 1) {
	MOVLW      0
	XORWF      _co_du_lieu_moi+1, 0
	BTFSS      STATUS+0, 2
	GOTO       L__main31
	MOVLW      1
	XORWF      _co_du_lieu_moi+0, 0
L__main31:
	BTFSS      STATUS+0, 2
	GOTO       L_main18
;mcu_controller.c,66 :: 		RCIE_bit = 0; // T?m t?t ng?t d? t?p trung x? lý co khí
	BCF        RCIE_bit+0, BitPos(RCIE_bit+0)
;mcu_controller.c,69 :: 		if (ma_loi == 1) {
	MOVF       _ma_loi+0, 0
	XORLW      1
	BTFSS      STATUS+0, 2
	GOTO       L_main19
;mcu_controller.c,71 :: 		PORTD.F0 = 1;
	BSF        PORTD+0, 0
;mcu_controller.c,72 :: 		Delay_ms(300);
	MOVLW      8
	MOVWF      R11+0
	MOVLW      157
	MOVWF      R12+0
	MOVLW      5
	MOVWF      R13+0
L_main20:
	DECFSZ     R13+0, 1
	GOTO       L_main20
	DECFSZ     R12+0, 1
	GOTO       L_main20
	DECFSZ     R11+0, 1
	GOTO       L_main20
	NOP
	NOP
;mcu_controller.c,73 :: 		PORTD.F0 = 0;
	BCF        PORTD+0, 0
;mcu_controller.c,74 :: 		}
L_main19:
;mcu_controller.c,77 :: 		co_du_lieu_moi = 0; // H? c?
	CLRF       _co_du_lieu_moi+0
	CLRF       _co_du_lieu_moi+1
;mcu_controller.c,78 :: 		RCIE_bit = 1;       // B?t ng?t l?i dón bo m?ch ti?p theo
	BSF        RCIE_bit+0, BitPos(RCIE_bit+0)
;mcu_controller.c,79 :: 		}
L_main18:
;mcu_controller.c,80 :: 		}
	GOTO       L_main16
;mcu_controller.c,81 :: 		}
L_end_main:
	GOTO       $+0
; end of _main
