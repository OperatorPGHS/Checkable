from fastapi import FastAPI, Request, Form, Depends, Response, HTTPException
from fastapi.responses import RedirectResponse
from fastapi_login import LoginManager
from fastapi.templating import Jinja2Templates
import os

# 시크릿 키 (토큰 서명 등에 사용됨)
SECRET_KEY = os.environ.get("SECRET_KEY")
app = FastAPI()

# 로그인 매니저 설정 (쿠키 기반 인증 사용)
manager = LoginManager(SECRET_KEY, tokenUrl="/login", use_cookie=True)
manager.cookie_name = "auth_token"  # 쿠키 이름 설정

# 템플릿 디렉토리 설정 (Jinja2 사용)
templates = Jinja2Templates(directory="templates")

# 임시 사용자 저장소 (실제 서비스에서는 DB 사용 필요)
users = {"testuser": {"username": "testuser", "password": "password123"}}

# 사용자 정보를 불러오는 함수 (LoginManager에 필요)
@manager.user_loader
def load_user(username: str):
    user = users.get(username)
    return user

# 홈 페이지
@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# 회원가입 페이지 (GET 요청)
@app.get("/signup") 
async def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

# 회원가입 처리 (POST 요청)
@app.post("/signup")
async def signup(request: Request, username: str = Form(...), password: str = Form(...)):
    if username in users:
        # 이미 존재하는 사용자일 경우 에러 메시지 반환
        return templates.TemplateResponse("signup.html", {"request": request, "msg": "이미 존재하는 사용자입니다."})
    
    # 새로운 사용자 등록
    users[username] = {"username": username, "password": password}
    
    # 로그인 페이지로 리다이렉트
    return RedirectResponse(url="/login", status_code=302)

# 로그인 페이지 (GET 요청)
@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# 로그인 처리 (POST 요청)
@app.post("/login")
async def login(request: Request, response: Response, username: str = Form(...), password: str = Form(...)):
    user = load_user(username)
    # 사용자 존재 여부와 비밀번호 확인
    if not user or user.get("password") != password:
        return templates.TemplateResponse("login.html", {"request": request, "msg": "잘못된 사용자명 또는 비밀번호입니다."})
    
    # 토큰 생성 및 쿠키에 저장
    access_token = manager.create_access_token(data={"sub": username})
    manager.set_cookie(response, access_token)
    
    # 대시보드로 리다이렉트
    return RedirectResponse(url="/dashboard", status_code=302)

# 로그인 후 대시보드 페이지
@app.get("/dashboard")
async def dashboard(request: Request, user=Depends(manager)):
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})

# 로그아웃 처리
@app.get("/logout")
def logout(response: Response):
    response = RedirectResponse(url="/")
    response.delete_cookie(manager.cookie_name)  # 쿠키 삭제
    return response

# 개발 서버 실행 (직접 실행할 경우)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)