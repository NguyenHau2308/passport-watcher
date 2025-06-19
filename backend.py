from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import JSONResponse

app = FastAPI()

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
