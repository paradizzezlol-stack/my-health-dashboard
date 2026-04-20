import os
from datetime import timedelta
from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pathlib import Path

import models
import database
import auth
from ai_extractor import extract_health_data_from_image

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = auth.jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except auth.JWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse(request, "index.html")

@app.post("/register")
def register(user_data: dict, db: Session = Depends(get_db)):
    username = user_data.get("username")
    password = user_data.get("password")
    
    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password required")
        
    db_user = db.query(models.User).filter(models.User.username == username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
        
    hashed_password = auth.get_password_hash(password)
    db_user = models.User(username=username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"message": "User registered successfully"}

@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/users")
async def get_users(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    return [{"id": u.id, "username": u.username} for u in users]

@app.get("/api/data")
async def get_data(user_id: int = None, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    target_id = user_id if user_id else current_user.id
    records = db.query(models.HealthRecord).filter(models.HealthRecord.user_id == target_id).all()
    
    return [
        {
            "id": r.id,
            "date": r.date.isoformat(),
            "body_weight": r.body_weight,
            "body_score": r.body_score,
            "bmi": r.bmi,
            "body_fat_percentage": r.body_fat_percentage,
            "body_water_mass": r.body_water_mass,
            "fat_mass": r.fat_mass,
            "bone_mineral_mass": r.bone_mineral_mass,
            "protein_mass": r.protein_mass,
            "muscle_mass": r.muscle_mass,
            "muscle_percentage": r.muscle_percentage,
            "body_water_percentage": r.body_water_percentage,
            "protein_percentage": r.protein_percentage,
            "bone_mineral_percentage": r.bone_mineral_percentage,
            "skeletal_muscle_mass": r.skeletal_muscle_mass,
            "visceral_fat_rating": r.visceral_fat_rating,
            "basal_metabolic_rate": r.basal_metabolic_rate,
            "estimated_waist_to_hip_ratio": r.estimated_waist_to_hip_ratio,
            "body_age": r.body_age,
            "fat_free_body_weight": r.fat_free_body_weight,
            "heart_rate": r.heart_rate
        } for r in records
    ]

@app.post("/api/upload")
async def upload_image(file: UploadFile = File(...), current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Save the file temporarily
    temp_dir = Path("temp_uploads")
    temp_dir.mkdir(exist_ok=True)
    temp_file_path = temp_dir / file.filename
    
    with open(temp_file_path, "wb") as buffer:
        buffer.write(await file.read())
        
    try:
        # Extract data using Gemini
        extracted_data = extract_health_data_from_image(str(temp_file_path))
        
        if not extracted_data:
            raise HTTPException(status_code=500, detail="Failed to extract data from image")
            
        # Create a new record
        new_record = models.HealthRecord(
            user_id=current_user.id,
            **extracted_data
        )
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
        
        return {"message": "Data extracted and saved successfully", "data": extracted_data}
    finally:
        # Cleanup
        if temp_file_path.exists():
            os.remove(temp_file_path)
