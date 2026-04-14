from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List

from app.database import engine, get_db
from app import models, schemas
from app.auth import hash_password
from app.calculator import CalculationFactory

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Calculator API - Module 11", version="3.0.0")


# ── Users ──────────────────────────────────────────────────────────────────

@app.post("/users/", response_model=schemas.UserRead, status_code=201)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(
        (models.User.username == user.username) | (models.User.email == user.email)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already exists")
    db_user = models.User(
        username=user.username,
        email=user.email,
        password_hash=hash_password(user.password),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.get("/users/", response_model=List[schemas.UserRead])
def list_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()


@app.get("/users/{user_id}", response_model=schemas.UserRead)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()


# ── Calculations ───────────────────────────────────────────────────────────

@app.post("/calculations/", response_model=schemas.CalculationRead, status_code=201)
def create_calculation(calc: schemas.CalculationCreate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == calc.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    result = CalculationFactory.compute(calc.type, calc.a, calc.b)
    db_calc = models.Calculation(
        a=calc.a,
        b=calc.b,
        type=calc.type.value,
        result=result,
        user_id=calc.user_id,
    )
    db.add(db_calc)
    db.commit()
    db.refresh(db_calc)
    return db_calc


@app.get("/calculations/", response_model=List[schemas.CalculationRead])
def list_calculations(db: Session = Depends(get_db)):
    return db.query(models.Calculation).all()


@app.get("/calculations/{calc_id}", response_model=schemas.CalculationRead)
def get_calculation(calc_id: int, db: Session = Depends(get_db)):
    calc = db.query(models.Calculation).filter(models.Calculation.id == calc_id).first()
    if not calc:
        raise HTTPException(status_code=404, detail="Calculation not found")
    return calc


@app.delete("/calculations/{calc_id}", status_code=204)
def delete_calculation(calc_id: int, db: Session = Depends(get_db)):
    calc = db.query(models.Calculation).filter(models.Calculation.id == calc_id).first()
    if not calc:
        raise HTTPException(status_code=404, detail="Calculation not found")
    db.delete(calc)
    db.commit()


# ── Join Query ─────────────────────────────────────────────────────────────

@app.get("/calculations/join/all", response_model=List[schemas.CalculationWithUser])
def calculations_with_users(db: Session = Depends(get_db)):
    rows = db.execute(text("""
        SELECT u.username, c.a, c.b, c.type, c.result
        FROM calculations c
        JOIN users u ON c.user_id = u.id
    """)).fetchall()
    return [schemas.CalculationWithUser(
        username=r.username,
        a=r.a,
        b=r.b,
        type=r.type,
        result=r.result,
    ) for r in rows]


# ── Health ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}
