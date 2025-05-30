from fastapi import FastAPI, Form, Request, Response, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import datetime
from database import SessionLocal
from models import Base, PeriodEnum, Student,WeekdayEnum,Attendance

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
@app.post("/attendance/{period_num}")
def mark_attendance(
    period_num: int,
    day: str = Form(...),
    request: Request = None,
    db: Session = Depends(get_db)
):
    student_number = request.cookies.get("student_number")
    if not student_number:
        return RedirectResponse("/login", status_code=302)

    # 차시 처리
    if period_num == 1:
        period = PeriodEnum.first
    elif period_num == 2:
        period = PeriodEnum.second
    else:
        return HTMLResponse("<h3>잘못된 차시입니다.</h3>", status_code=400)

    # 학생 조회
    student = db.query(Student).filter_by(student_number=student_number, day=day).first()
    if not student:
        return HTMLResponse("<h3>해당 요일에 등록된 학생 정보가 없습니다.</h3>", status_code=400)

    # 출석 중복 체크
    today = datetime.date.today()
    exists = db.query(Attendance).filter_by(
        student_id=student.id,
        day=day,
        period=period,
        date=today
    ).first()

    if exists:
        return HTMLResponse(f"<h3>{period.value} 출석은 이미 완료되었습니다!</h3>")

    # 출석 저장
    attendance = Attendance(
        student_id=student.id,
        day=day,
        period=period,
        date=today
    )
    db.add(attendance)
    db.commit()

    return HTMLResponse(f"<h3>{period.value} 출석 완료!</h3>")

@app.get("/")
def home(request: Request):
    student_number = request.cookies.get("student_number")
    if not student_number:
        return RedirectResponse("/login", status_code=302)

    weekday_map = ["월", "화", "수", "목", "금", "토", "일"]
    today = datetime.date.today()
    today_weekday = weekday_map[today.weekday()]  # 0 = 월, 1 = 화 ...

    return templates.TemplateResponse("index.html", {
        "request": request,
        "student_number": student_number,
        "today_weekday": today_weekday
    })