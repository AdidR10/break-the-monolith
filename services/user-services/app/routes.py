from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from app.schemas import RegisterRequest, LoginRequest, TokenResponse
from app.models import User, RickshawProfile, StudentProfile, UserType
from app.auth import hash_password, verify_password, create_access_token
from app.utils import get_db

router = APIRouter()

@router.post("/register", response_model=TokenResponse)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter((User.email == data.email) | (User.phone == data.phone)).first():
        raise HTTPException(status_code=400, detail="Email or phone already registered")

    if data.user_type == UserType.RICKSHAW_PULLER and not data.rickshaw_number:
        raise HTTPException(status_code=400, detail="Rickshaw number is required for rickshaw pullers")

    user = User(
        email=data.email,
        phone=data.phone,
        password_hash=hash_password(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        user_type=data.user_type
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    if data.user_type == UserType.RICKSHAW_PULLER:
        profile = RickshawProfile(user_id=user.id, rickshaw_number=data.rickshaw_number, license_number=data.license_number)
        db.add(profile)
    else:
        profile = StudentProfile(user_id=user.id, student_id=data.student_id, department=data.department)
        db.add(profile)

    db.commit()

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token)

@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token)

@router.post("/logout")
def logout():
    # Stub: token invalidation would be handled using a blacklist or DB flag
    return {"message": "Logged out successfully"}
