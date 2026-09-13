from ultralytics import YOLO

def main():
 
    model = YOLO('yolov8n.pt')

  
    print("[*] Đưa dữ liệu vào lò luyện bằng GPU...")
    results = model.train(
        data='dataset/data.yaml',
        epochs=50,
        imgsz=640,
        batch=8,
        device=0,                   
        workers=0,                 
        project='Smart_AOI_Runs',
        name='yolov8_pcb_model'
    )
    print("[*] Luyện công hoàn tất!")

 
if __name__ == '__main__':
 
    from multiprocessing import freeze_support
    freeze_support()
    
     
    main()