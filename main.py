from fastapi import FastAPI, Form, Request, Response, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from database import SessionLocal
from models import Base, Student,WeekdayEnum

app = FastAPI()
templates = Jinja2Templates(directory="templates")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# DB 세션 의존성
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 회원가입 페이지
@app.get("/register")
def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

# 회원가입 처리
@app.post("/register")
def register(
    request: Request,
    student_number: str = Form(...),
    name: str = Form(...),
    password: str = Form(...),
    days: list[str] = Form(...),
    db: Session = Depends(get_db)
):
    hashed_pw = pwd_context.hash(password)

    # 학번+요일 중복 확인
    for day in days:
        exists = db.query(Student).filter_by(student_number=student_number, day=day).first()
        if exists:
            return HTMLResponse(f"<h3>{student_number}의 {day}요일은 이미 등록되어 있습니다.</h3>", status_code=400)

    # 데이터 삽입
    for day in days:
        new_entry = Student(
            student_number=student_number,
            name=name,
            password=hashed_pw,
            day=WeekdayEnum(day)
        )
        db.add(new_entry)
    db.commit()

    return RedirectResponse("/login", status_code=302)

# 로그인 페이지
@app.get("/login")
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# 로그인 처리
@app.post("/login")
def login(
    response: Response,
    student_number: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    students = db.query(Student).filter_by(student_number=student_number).all()
    if not students:
        return HTMLResponse("<h3>학번이 존재하지 않습니다.</h3>", status_code=401)

    if pwd_context.verify(password, students[0].password):
        res = RedirectResponse("/", status_code=302)
        res.set_cookie("student_number", student_number)
        return res

    return HTMLResponse("<h3>비밀번호가 틀렸습니다.</h3>", status_code=401)

# 홈
@app.get("/")
def home(request: Request):
    name = request.cookies.get("student_number")
    return templates.TemplateResponse("index.html", {"request": request, "name": name})
