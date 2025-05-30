from fastapi import FastAPI, Request, Form, Response, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext

app = FastAPI()
templates = Jinja2Templates(directory="templates")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 메모리 임시 DB (학습용, 실제론 DB 사용)
fake_db = []

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    student_number = request.cookies.get("student_number")
    student = next((s for s in fake_db if s["student_number"] == student_number), None)
    if student:
        return templates.TemplateResponse("index.html", {"request": request, "name": student["name"]})
    return RedirectResponse("/login")

@app.get("/register", response_class=HTMLResponse)
def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
def register(
    name: str = Form(...),
    student_number: str = Form(...),
    password: str = Form(...),
    days: list[str] = Form(default=[])
):
    hashed_pw = pwd_context.hash(password)
    for day in days:
        fake_db.append({
            "student_number": student_number,
            "name": name,
            "password": hashed_pw,
            "day": day
        })
    return RedirectResponse("/login", status_code=302)

@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login(response: Response, student_number: str = Form(...), password: str = Form(...)):
    student = next((s for s in fake_db if s["student_number"] == student_number), None)
    if student and pwd_context.verify(password, student["password"]):
        response = RedirectResponse("/", status_code=302)
        response.set_cookie("student_number", student_number)
        return response
    return HTMLResponse("<h3>로그인 실패</h3><a href='/login'>다시 시도</a>", status_code=401)

@app.get("/logout")
def logout():
    response = RedirectResponse("/login", status_code=302)
    response.delete_cookie("student_number")
    return response
