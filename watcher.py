import time
import pathlib
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

SCAN_DIR = "scan_out"
PROCESSED_DIR = "processed"

class ScanHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        print(f"File mới xuất hiện: {event.src_path}")

if __name__ == "__main__":
    path = pathlib.Path(SCAN_DIR)
    path.mkdir(exist_ok=True)
    observer = Observer()
    observer.schedule(ScanHandler(), str(path), recursive=False)
    observer.start()
    print(f"Đang giám sát folder: {SCAN_DIR}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
