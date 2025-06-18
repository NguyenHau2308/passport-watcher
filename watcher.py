import time
import pathlib
import shutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

SCAN_DIR = "scan_out"
PROCESSED_DIR = "processed"

def check_full_passport_files(folder):
    files = list(pathlib.Path(folder).glob("001-*"))
    required = {"001-IMAGEPHOTO.jpg", "001-IMAGEVIS.jpg", "001-INFO.txt"}
    found = set([f.name for f in files])
    return required.issubset(found)

class ScanHandler(FileSystemEventHandler):
    def on_any_event(self, event):
        if event.is_directory:
            return
        # Kiểm tra đủ bộ 3 file chưa
        if check_full_passport_files(SCAN_DIR):
            print("ĐÃ ĐỦ FILE PASSPORT, CHUẨN BỊ XỬ LÝ.")
            # Move files sang processed để tránh xử lý lặp
            for f in ["001-IMAGEPHOTO.jpg", "001-IMAGEVIS.jpg", "001-INFO.txt"]:
                src = pathlib.Path(SCAN_DIR) / f
                dst = pathlib.Path(PROCESSED_DIR) / f
                shutil.move(str(src), str(dst))
            print("ĐÃ MOVE FILE SANG FOLDER processed/")
        else:
            print("Chưa đủ file, đợi tiếp...")

if __name__ == "__main__":
    pathlib.Path(SCAN_DIR).mkdir(exist_ok=True)
    pathlib.Path(PROCESSED_DIR).mkdir(exist_ok=True)
    observer = Observer()
    observer.schedule(ScanHandler(), SCAN_DIR, recursive=False)
    observer.start()
    print(f"Đang giám sát folder: {SCAN_DIR}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
