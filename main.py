from fastapi import FastAPI, Request, Form, Depends, Response, HTTPException
from fastapi.responses import RedirectResponse
from fastapi_login import LoginManager
from fastapi.templating import Jinja2Templates

SECRET = "your_secret_key_here"
app = FastAPI()

# 로그인 매니저 설정 (use_cookie=True로 쿠키 기반 인증)
manager = LoginManager(SECRET, tokenUrl="/login", use_cookie=True)
manager.cookie_name = "auth_token"

# 템플릿 디렉토리 설정
templates = Jinja2Templates(directory="templates")

# 간단한 인메모리 사용자 저장소
users = {"testuser": {"username": "testuser", "password": "password123"}}

@manager.user_loader
def load_user(username: str):
    user = users.get(username)
    return user

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/signup")
async def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.post("/signup")
async def signup(request: Request, username: str = Form(...), password: str = Form(...)):
    if username in users:
        return templates.TemplateResponse("signup.html", {"request": request, "msg": "이미 존재하는 사용자입니다."})
    users[username] = {"username": username, "password": password}
    return RedirectResponse(url="/login", status_code=302)

@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, response: Response, username: str = Form(...), password: str = Form(...)):
    user = load_user(username)
    if not user or user.get("password") != password:
        return templates.TemplateResponse("login.html", {"request": request, "msg": "잘못된 사용자명 또는 비밀번호입니다."})
    access_token = manager.create_access_token(data={"sub": username})
    manager.set_cookie(response, access_token)
    return RedirectResponse(url="/dashboard", status_code=302)

@app.get("/dashboard")
async def dashboard(request: Request, user=Depends(manager)):
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})

@app.get("/logout")
def logout(response: Response):
    response = RedirectResponse(url="/")
    response.delete_cookie(manager.cookie_name)
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)