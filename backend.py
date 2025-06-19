from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

@app.post("/check-passport")
async def check_passport(data: dict):
    passport_no = data.get("PASSPORT_NO")
    # Giả lập: Nếu PASSPORT_NO bắt đầu bằng "C" thì đã tồn tại
    if passport_no and passport_no.startswith("C"):
        return {"result": "customer existed", "customer_code": "CUST-" + passport_no}
    else:
        return {"result": "new customer created", "customer_code": "CUST-NEW123"}

@app.post("/upload-passport-images")
async def upload_passport_images(request: Request):
    # Nhận ảnh (tạm thời trả về success)
    return JSONResponse({"result": "success"})
