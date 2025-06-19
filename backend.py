from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import pathlib

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
SCAN_DIR = "scan_out"

def parse_txt_to_dict(txt):
    data = {}
    for line in txt.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip()
    return data

@app.post("/check-passport")
async def check_passport(data: dict):
    passport_no = data.get("PASSPORT_NO")
    if passport_no and passport_no.startswith("C"):
        return {"result": "customer existed", "customer_code": "CUST-" + passport_no}
    else:
        return {"result": "new customer created", "customer_code": "CUST-NEW123"}

@app.post("/upload-passport-images")
async def upload_passport_images(
    customer_code: str = Form(...),
    image_photo: UploadFile = None,
    image_vis: UploadFile = None,
):
    # Giả lập: chỉ nhận và báo success
    return JSONResponse({"result": "success", "customer_code": customer_code})

@app.get("/api/pending-passports")
def pending_passports():
    files = list(pathlib.Path(SCAN_DIR).glob("*-INFO.txt"))
    result = []
    for f in files:
        prefix = f.name.split("-")[0]
        photo = f"{prefix}-IMAGEPHOTO.jpg"
        vis = f"{prefix}-IMAGEVIS.jpg"
        with open(f, "r", encoding="utf-8") as finfo:
            txt = finfo.read()
        info = {
            "icao_mrz": txt.strip(),
            "info_file": f.name,
            "image_photo": photo,
            "image_vis": vis,
        }
        result.append(info)
    return result

@app.get("/api/passport-img/{img_name}")
def get_passport_img(img_name: str):
    path = pathlib.Path(SCAN_DIR) / img_name
    return FileResponse(path)
