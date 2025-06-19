from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import pathlib
import random
import datetime

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP

DATABASE_URL = "postgresql+asyncpg://postgres:123456@localhost:5432/passportdb"

engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()


class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True)
    icao_mrz = Column(Text, nullable=False)
    customer_code = Column(String(32), nullable=False)
    created_at = Column(TIMESTAMP)


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
SCAN_DIR = "scan_out"


@app.post("/check-passport")
async def check_passport(data: dict):
    icao_mrz = data.get("icao_mrz")
    if not icao_mrz:
        return JSONResponse({"error": "Thiếu mã MRZ"}, status_code=400)

    async with SessionLocal() as session:
        result = await session.execute(
            Customer.__table__.select().where(Customer.icao_mrz == icao_mrz)
        )
        customer = result.first()
        if customer:
            return {
                "result": "customer existed",
                "customer_code": customer[0].customer_code,
            }
        c = Customer(
            icao_mrz=icao_mrz,
            customer_code="",
            created_at=datetime.datetime.now(),
        )
        session.add(c)
        await session.flush()
        code = f"KH{c.id:04d}"
        c.customer_code = code
        await session.commit()
        return {"result": "new customer created", "customer_code": code}


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
