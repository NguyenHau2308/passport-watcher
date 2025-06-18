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

def parse_txt_to_dict(txt):
    data = {}
    for line in txt.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip()
    return data

class ScanHandler(FileSystemEventHandler):
    def on_any_event(self, event):
        if event.is_directory:
            return
        if check_full_passport_files(SCAN_DIR):
            print("ĐÃ ĐỦ FILE PASSPORT, CHUẨN BỊ XỬ LÝ.")
            info_path = pathlib.Path(SCAN_DIR) / "001-INFO.txt"
            if info_path.exists():
                with open(info_path, "r", encoding="utf-8") as f:
                    txt = f.read()
                print("----- Passport Info TXT -----")
                print(txt)
                print("-----------------------------")
                parsed = parse_txt_to_dict(txt)
                print("Parsed data:", parsed)
            # Move files sang processed
            for f in ["001-IMAGEPHOTO.jpg", "001-IMAGEVIS.jpg", "001-INFO.txt"]:
                src = pathlib.Path(SCAN_DIR) / f
                dst = pathlib.Path(PROCESSED_DIR) / f
                shutil.move(str(src), str(dst))
            print("ĐÃ MOVE FILE SANG FOLDER processed/")

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
