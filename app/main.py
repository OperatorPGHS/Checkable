from fastapi import FastAPI, Request, Form, Depends, Response, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi_login import LoginManager
from fastapi.templating import Jinja2Templates
from pathlib import Path
from jinja2 import TemplateNotFound  # ← 예외 캐치용

SECRET = "your_secret_key_here"
app = FastAPI()

manager = LoginManager(SECRET, token_url="/login", use_cookie=True)
manager.cookie_name = "auth_token"

# ────────────────────────────────────────────
# templates 디렉토리가 없어도 절대경로 지정
# ────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

users = {"testuser": {"username": "testuser", "password": "password123"}}

@manager.user_loader
def load_user(username: str):
    return users.get(username)

# ────────────────────────────────────────────
# 템플릿 안전 호출 헬퍼
# ────────────────────────────────────────────
def safe_template(name: str, request: Request, **ctx):
    try:
        return templates.TemplateResponse(name, {"request": request, **ctx})
    except TemplateNotFound:
        # 템플릿 없으면 즉석에서 기본 HTML 반환
        body = f"""
        <html>
          <head><title>{name}</title></head>
          <body>
            <h1>{ctx.get('msg', 'Checkable')}</h1>
            <p>'{name}' 템플릿이 아직 준비되지 않았습니다.<br>
               templates/{name} 파일을 만들면 자동으로 교체됩니다.</p>
          </body>
        </html>
        """
        return HTMLResponse(content=body, status_code=200)

# ────────────────────────────────────────────
# 라우트
# ────────────────────────────────────────────
@app.get("/")
async def home(request: Request):
    return safe_template("index.html", request)

@app.get("/signup")
async def signup_page(request: Request):
    return safe_template("signup.html", request)

@app.post("/signup")
async def signup(request: Request, username: str = Form(...), password: str = Form(...)):
    if username in users:
        return safe_template("signup.html", request, msg="이미 존재하는 사용자입니다.")
    users[username] = {"username": username, "password": password}
    return RedirectResponse(url="/login", status_code=302)

@app.get("/login")
async def login_page(request: Request):
    return safe_template("login.html", request)

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    user = load_user(username)
    if not user or user["password"] != password:
        return safe_template("login.html", request, msg="잘못된 사용자명 또는 비밀번호입니다.")
    access_token = manager.create_access_token(data={"sub": username})
    redirect = RedirectResponse(url="/dashboard", status_code=302)
    manager.set_cookie(redirect, access_token)
    return redirect

@app.get("/dashboard")
async def dashboard(request: Request, user=Depends(manager)):
    return safe_template("dashboard.html", request, user=user)

@app.get("/logout")
def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie(manager.cookie_name)
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)