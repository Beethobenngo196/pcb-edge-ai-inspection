#line 1 "D:/pcb-edge-ai-inspection/mcu_firmware/mcu_controller.c"



int buoc_nhan = 0;
unsigned short ma_loi, toa_do_x, toa_do_y;
int co_du_lieu_moi = 0;




void interrupt() {

 if (RCIF_bit) {
 unsigned short incoming_byte = UART1_Read();


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
 co_du_lieu_moi = 1;
 buoc_nhan = 0;
 }
 else {
 buoc_nhan = 0;
 }
 }
}




void main() {

 ANSEL = 0;
 ANSELH = 0;

 TRISD = 0x00;
 PORTD = 0x00;


 UART1_Init(115200);
 Delay_ms(100);


 RCIE_bit = 1;
 PEIE_bit = 1;
 GIE_bit = 1;


 while(1) {
 if (co_du_lieu_moi == 1) {

 RCIE_bit = 0;


 if (ma_loi == 1) {

 PORTD.F0 = 1;
 Delay_ms(300);
 PORTD.F0 = 0;
 }


 co_du_lieu_moi = 0;
 RCIE_bit = 1;
 }
 }
}
