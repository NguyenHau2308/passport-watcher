from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import pathlib
import datetime
import os

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey, select

DATABASE_URL = "postgresql+asyncpg://postgres:123456@localhost:5432/passportdb"

engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()

class Info(Base):
    __tablename__ = "info"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(4))
    country_code = Column(String(4))
    last_name = Column(String(64))
    first_name = Column(String(64))
    passport_no = Column(String(32))
    nationality = Column(String(8))
    date_of_birth = Column(String(12))
    gender = Column(String(4))
    date_of_expiry = Column(String(12))
    icao_mrz = Column(Text)

class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True)
    info_id = Column(Integer, ForeignKey("info.id"))
    icao_mrz = Column(Text, nullable=False)
    customer_code = Column(String(32), nullable=False)
    created_at = Column(TIMESTAMP)

class PassportImage(Base):
    __tablename__ = "passport_images"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer)
    image_type = Column(String(32))
    file_name = Column(String(255))
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
PROCESSED_DIR = os.path.join(os.path.dirname(SCAN_DIR), "processed")
pathlib.Path(PROCESSED_DIR).mkdir(parents=True, exist_ok=True)

def parse_mrz(mrz):
    lines = [l.strip() for l in mrz.strip().splitlines() if l.strip()]
    if len(lines) < 2:
        return {}
    l1, l2 = lines[0], lines[1]
    return {
        "type": l1[0:2].replace("<", ""),
        "country_code": l1[2:5].replace("<", ""),
        "last_name": l1[5:].split("<<")[0].replace("<", ""),
        "first_name": l1[5:].split("<<")[1].replace("<", "") if "<<" in l1[5:] else "",
        "passport_no": l2[0:9].replace("<", ""),
        "nationality": l2[10:13].replace("<", ""),
        "date_of_birth": "19"
        + l2[13:19][0:2]
        + "-"
        + l2[13:19][2:4]
        + "-"
        + l2[13:19][4:6],
        "gender": l2[20],
        "date_of_expiry": "20"
        + l2[21:27][0:2]
        + "-"
        + l2[21:27][2:4]
        + "-"
        + l2[21:27][4:6],
        "icao_mrz": mrz,
    }
def move_files(prefix):
    files = [
        f"{prefix}-INFO.txt",
        f"{prefix}-IMAGEPHOTO.jpg",
        f"{prefix}-IMAGEVIS.jpg"
    ]
    processed_dir = pathlib.Path(SCAN_DIR).parent / "processed"
    processed_dir.mkdir(exist_ok=True)
    for fname in files:
        src = pathlib.Path(SCAN_DIR) / fname
        dst = processed_dir / fname
        if src.exists():
            src.rename(dst)

@app.post("/check-passport")
async def check_passport(data: dict):
    icao_mrz = data.get("icao_mrz")
    if not icao_mrz:
        return JSONResponse({"error": "Thiếu mã ICAO"}, status_code=400)

    async with SessionLocal() as session:
        result = await session.execute(
            select(Customer).where(Customer.icao_mrz == icao_mrz)
        )
        customer = result.scalars().first()
        if customer:
            return {
                "result": "customer existed",
                "customer_code": customer.customer_code,
            }
        info_dict = parse_mrz(icao_mrz)
        new_info = Info(**info_dict)
        session.add(new_info)
        await session.flush()
        code = f"KH{new_info.id:04d}"
        c = Customer(
            info_id=new_info.id,
            icao_mrz=icao_mrz,
            customer_code=code,
            created_at=datetime.datetime.now(),
        )
        session.add(c)
        await session.commit()
        return {"result": "new customer created", "customer_code": code}


@app.post("/upload-passport-images")
async def upload_passport_images(
    customer_code: str = Form(...),
    image_photo: str = Form(...),
    image_vis: str = Form(...),
    prefix: str = Form(...),
):
    async with SessionLocal() as session:
        result = await session.execute(
            select(Customer).where(Customer.customer_code == customer_code)
        )
        customer = result.scalars().first()
        if not customer:
            return JSONResponse({"error": "not found"}, status_code=404)
        customer_id = customer.id

        for file_name, img_type in [(image_photo, "photo"), (image_vis, "vis")]:
            img = PassportImage(
                customer_id=customer_id,
                image_type=img_type,
                file_name=file_name,
                created_at=datetime.datetime.now(),
            )
            session.add(img)
        await session.commit()
        move_files(prefix)
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
@app.get("/api/processed-passports")
def processed_passports():
    processed_dir = pathlib.Path(SCAN_DIR).parent / "processed"
    files = list(processed_dir.glob("*-INFO.txt"))
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
            "prefix": prefix
        }
        result.append(info)
    return result
