from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
import datetime
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    health_records = relationship("HealthRecord", back_populates="owner")

class HealthRecord(Base):
    __tablename__ = "health_records"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=datetime.datetime.utcnow)
    
    # User linkage
    user_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="health_records")

    # Xiaomi Scale Metrics
    body_weight = Column(Float, nullable=True)
    body_score = Column(Float, nullable=True)
    bmi = Column(Float, nullable=True)
    body_fat_percentage = Column(Float, nullable=True)
    body_water_mass = Column(Float, nullable=True)
    fat_mass = Column(Float, nullable=True)
    bone_mineral_mass = Column(Float, nullable=True)
    protein_mass = Column(Float, nullable=True)
    muscle_mass = Column(Float, nullable=True)
    muscle_percentage = Column(Float, nullable=True)
    body_water_percentage = Column(Float, nullable=True)
    protein_percentage = Column(Float, nullable=True)
    bone_mineral_percentage = Column(Float, nullable=True)
    skeletal_muscle_mass = Column(Float, nullable=True)
    visceral_fat_rating = Column(Float, nullable=True)
    basal_metabolic_rate = Column(Float, nullable=True)
    estimated_waist_to_hip_ratio = Column(Float, nullable=True)
    body_age = Column(Float, nullable=True)
    fat_free_body_weight = Column(Float, nullable=True)
    heart_rate = Column(Float, nullable=True)
