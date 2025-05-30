from fastapi import FastAPI, Request, Form, Depends, Response
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi_login import LoginManager
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, or_
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from datetime import datetime
import bcrypt
import os
import re
from itsdangerous import URLSafeSerializer

# 환경 변수에서 SECRET_KEY 불러오기 (없을 경우 기본값 사용)
SECRET_KEY = os.environ.get("SECRET_KEY", "super-secret-key")
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./test.db")

# FastAPI 앱, 템플릿 설정s
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# DB 설정
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# 로그인 매니저 설정
manager = LoginManager(SECRET_KEY, tokenUrl="/login", use_cookie=True)
manager.cookie_name = "auth_token"
serializer = URLSafeSerializer(SECRET_KEY, salt="auth")

# DB 모델
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    nickname = Column(String, unique=True)
    email = Column(String, unique=True)
    password = Column(String)
    created_at = Column(DateTime)
    study_time = Column(Integer, default=0)
    total_study_time = Column(Integer, default=0)
    studytimegoal = Column(Integer, default=0)
    is_deleted = Column(Boolean, default=False)

class EmailVerification(Base):
    __tablename__ = "email_verifications"
    id = Column(Integer, primary_key=True)
    email = Column(String)
    verification_code = Column(String)
    expires_at = Column(DateTime)

Base.metadata.create_all(bind=engine)

# DB 의존성
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 비밀번호 유효성 검사 함수
def is_valid_password(password: str) -> bool:
    return (
        len(password) >= 8 and
        re.search(r"[A-Za-z]", password) and
        re.search(r"[0-9]", password) and
        re.search(r"[!@#$%^&*(),.?\":{}|<>]", password)
    )

# 로그인 매니저에 유저 로딩 함수 제공
@manager.user_loader
def load_user(nickname: str):
    db = SessionLocal()
    return db.query(User).filter(User.nickname == nickname).first()

# 홈 페이지
@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# 회원가입 GET
@app.get("/signup")
async def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request, "message": ""})

# 회원가입 POST
@app.post("/signup")
async def signup(
    request: Request,
    name: str = Form(...),
    nickname: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirmpassword: str = Form(...),
    verification_code: str = Form(...),
    db: Session = Depends(get_db),
):
    if confirmpassword != password:
        return templates.TemplateResponse("signup.html", {"request": request, "message": "비밀번호가 일치하지 않습니다."})

    if not is_valid_password(password):
        return templates.TemplateResponse("signup.html", {"request": request, "message": "비밀번호는 영문, 숫자, 특수문자를 포함해야 합니다."})

    verification = db.query(EmailVerification).filter(
        EmailVerification.email == email,
        EmailVerification.verification_code == verification_code
    ).first()

    if not verification:
        return templates.TemplateResponse("signup.html", {"request": request, "message": "잘못된 인증 코드입니다."})

    if datetime.now() > verification.expires_at:
        db.delete(verification)
        db.commit()
        return templates.TemplateResponse("signup.html", {"request": request, "message": "인증 코드가 만료되었습니다."})

    if db.query(User).filter(or_(User.nickname == nickname, User.email == email)).first():
        return templates.TemplateResponse("signup.html", {"request": request, "message": "이미 존재하는 닉네임 또는 이메일입니다."})

    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    user = User(
        name=name,
        nickname=nickname,
        email=email,
        password=hashed_pw.decode('utf-8'),
        created_at=datetime.now()
    )
    db.add(user)
    db.commit()
    db.delete(verification)
    db.commit()

    user_data = {'id': user.id, 'nickname': user.nickname}
    encrypted_data = serializer.dumps(user_data)
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie("user_data", encrypted_data, max_age=18144000, httponly=True, samesite="Lax")
    return response

# 로그인 GET
@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# 로그인 POST
@app.post("/login")
async def login(
    request: Request,
    nicknameoremail: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(or_(User.nickname == nicknameoremail, User.email == nicknameoremail)).first()

    if user and user.is_deleted:
        return templates.TemplateResponse("login.html", {"request": request, "message": "탈퇴된 계정입니다."})

    if user and bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
        user_data = {'id': user.id, 'nickname': user.nickname}
        encrypted_data = serializer.dumps(user_data)
        response = RedirectResponse(url="/", status_code=302)
        response.set_cookie("user_data", encrypted_data, max_age=18144000, httponly=True, samesite="Lax")
        return response

    return templates.TemplateResponse("login.html", {"request": request, "message": "닉네임/이메일 또는 비밀번호가 잘못되었습니다."})

# 대시보드 (로그인 필요)
@app.get("/dashboard")
async def dashboard(request: Request, user=Depends(manager)):
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})

# 로그아웃
@app.get("/logout")
def logout(response: Response):
    response = RedirectResponse(url="/")
    response.delete_cookie(manager.cookie_name)
    response.delete_cookie("user_data")
    return response
