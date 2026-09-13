# Hệ thống Edge AI Kiểm định và Phân loại Khuyết tật Bo mạch (PCB) Tự động

## 1. Tổng quan Dự án (Project Description)
Dự án nghiên cứu và phát triển một hệ thống thị giác máy tính nhúng (Embedded Computer Vision System) ứng dụng trong môi trường công nghiệp. Hệ thống sử dụng mô hình học sâu YOLO được lượng tử hóa chạy trên máy tính biên để phát hiện và phân loại các khuyết tật vi mô trên bo mạch in (như mẻ mạch, đứt mạch, khuyết lỗ) theo thời gian thực. Sau khi xử lý ảnh, máy tính biên sẽ giao tiếp bất đồng bộ qua chuẩn nối tiếp với cụm vi điều khiển trung tâm để điều khiển cơ cấu cơ khí, tự động loại bỏ sản phẩm lỗi khỏi dây chuyền.

## 2. Kiến trúc Hệ thống (System Architecture)
Hệ thống được chia làm 3 lớp (Layer) phân định rõ ràng nhiệm vụ:
- **Lớp 1 - Khối Trạm Biên (Edge AI Node):** Chạy luồng Producer lấy dữ liệu từ Camera, đẩy vào Queue. Luồng Consumer (AI Core) rút ảnh, suy luận qua TensorRT. Luồng I/O đóng gói dữ liệu tọa độ và mã lỗi.
- **Lớp 2 - Khối Giao tiếp (Communication Bridge):** Sử dụng giao thức UART để truyền tải khung dữ liệu từ trạm biên xuống phần cứng điều khiển.
- **Lớp 3 - Khối Điều khiển Chấp hành (Hardware Control):** Vi điều khiển xử lý tín hiệu thông qua ngắt nhận (UART Receive Interrupt) để bắt gói tin, giải mã và xuất xung PWM ra cơ cấu chấp hành (động cơ/rơ-le).

## 3. Đặc tả Yêu cầu Hệ thống (SRS)

### Yêu cầu Phần cứng
| Thành phần | Đặc tả kỹ thuật | Chức năng trong hệ thống |
| :--- | :--- | :--- |
| **Edge Computer** | Kiến trúc ARM, RAM >= 4GB (Jetson Nano / Raspberry Pi). | Chạy HĐH Linux, luồng Camera, xử lý AI TensorRT. |
| **Microcontroller** | Dòng 8-bit công nghiệp (PIC 16F887 / 18F4550). | Xử lý ngắt tín hiệu, điều khiển thời gian thực. |
| **Camera Sensor** | Giao tiếp USB, phân giải >= 720p (ưu tiên Global Shutter). | Thu thập hình ảnh PCB không bị nhòe chuyển động. |
| **Actuator** | Động cơ bước (+ Driver) hoặc Van khí nén + Relay 5V. | Tác động vật lý loại bỏ sản phẩm lỗi. |

### Yêu cầu Phần mềm & Hiệu năng
| Chỉ tiêu | Đặc tả & Ngưỡng yêu cầu | Ý nghĩa |
| :--- | :--- | :--- |
| **Thuật toán AI** | TensorRT / DeepStream (Lượng tử hóa INT8/FP16). | Tối ưu hóa file trọng số để giảm tải VRAM. |
| **Kiến trúc Code** | C++ / Python Multi-threading (Queue + Mutex). | Ngăn chặn Deadlock và hiện tượng nghẽn khung hình. |
| **Inference FPS** | Tối thiểu **30 FPS**. | Đảm bảo không bỏ sót PCB trên dây chuyền. |
| **System Latency**| Tối đa **150 ms**. | Thời gian từ lúc chụp ảnh đến lúc kích hoạt cơ khí. |

### Giao thức Truyền thông (UART Frame Protocol)
- Cấu hình: Baudrate 115200, 8 Data bits, No Parity, 1 Stop bit.
- Khung truyền 5 Bytes: `[START_BYTE] - [ERROR_CODE] - [X_COORD] - [Y_COORD] - [END_BYTE]`

| Byte # | Tên trường | Giá trị (Hex) | Mô tả chi tiết |
| :--- | :--- | :--- | :--- |
| 1 | `START_BYTE` | `0xAA` | Báo hiệu bắt đầu một khung truyền. |
| 2 | `ERROR_CODE` | `0x00` -> `0xFF` | `0x01` (Khuyết lỗ), `0x02` (Mẻ mạch), `0x00` (Tốt). |
| 3 | `X_COORD` | `0x00` -> `0xFF` | Tọa độ tâm X của lỗi (chuẩn hóa 0-255). |
| 4 | `Y_COORD` | `0x00` -> `0xFF` | Tọa độ tâm Y của lỗi (chuẩn hóa 0-255). |
| 5 | `END_BYTE` | `0x55` | Chốt khung truyền. Xác nhận gói tin hợp lệ. |

## 4. Lộ trình Triển khai Kỹ thuật "Bottom-Up"
- **Bước 1 - Thiết lập Hệ sinh thái (Day 1):** Khởi tạo repository trên Git. Phân chia rõ thư mục `edge_core/` và `mcu_firmware/`. Ghi chú `README.md` rõ ràng.
- **Bước 2 - Thông tuyến Giao tiếp UART (Tuần 1):** Viết script gửi chuỗi 5 byte chuẩn từ trạm biên. Lập trình Firmware vi điều khiển cấu hình Ngắt nhận UART để bắt chính xác chuỗi này và phản hồi bằng tín hiệu I/O cơ bản (sáng LED/quay Động cơ).
- **Bước 3 - Xây dựng Khung Đa luồng (Tuần 2):** Bỏ qua model AI. Viết luồng 1 (Producer) đọc Camera đẩy vào Queue. Viết luồng 2 (Consumer) đọc Queue, kết hợp hàm delay giả lập thời gian chạy model để đo lường độ ổn định RAM và FPS.
- **Bước 4 - Tích hợp AI và Hoàn thiện (Tuần 3 & 4):** Chuyển đổi mô hình YOLO hiện tại sang định dạng TensorRT (`.engine`). Nhúng lõi AI này vào luồng Consumer. Nối kết quả đầu ra vào hàm truyền UART đã test ở Bước 2 để hệ thống chạy khép kín.