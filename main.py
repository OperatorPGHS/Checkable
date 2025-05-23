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

@app.get("/signup")
async def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request, "message": ""})

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
        return templates.TemplateResponse(
            "signup.html", {"request": request, "message": "비밀번호가 일치하지 않습니다."}
        )
    
    if not is_valid_password(password):
        return templates.TemplateResponse(
            "signup.html", {"request": request, "message": "비밀번호는 영문, 숫자, 특수문자가 포함되어야 합니다."}
        )
    
    verification = db.query(EmailVerification).filter(
        EmailVerification.email == email,
        EmailVerification.verification_code == verification_code
    ).first()
    if not verification:
        return templates.TemplateResponse(
            "signup.html", {"request": request, "message": "잘못된 인증 코드입니다."}
        )
    if datetime.now() > verification.expires_at:
        db.delete(verification)
        db.commit()
        return templates.TemplateResponse(
            "signup.html", {"request": request, "message": "인증 코드가 만료되었습니다."}
        )
    
    existing_user = db.query(User).filter(
        (User.nickname == nickname) | (User.email == email)
    ).first()
    if existing_user:
        return templates.TemplateResponse(
            "signup.html", {"request": request, "message": "닉네임 또는 이메일이 이미 존재합니다."}
        )
    
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    user = User(
        name=name,
        nickname=nickname,
        email=email,
        password=hashed_password.decode('utf-8'),
        created_at=datetime.now(),
        study_time=0,  # 기본값 설정
        total_study_time=0,  # 기본값 설정
        studytimegoal=0
    )
    db.add(user)
    db.commit()
    db.delete(verification)
    db.commit()
    
    # 자동 로그인 쿠키 설정
    user_data = {'id': user.id, 'nickname': user.nickname}
    encrypted_data = serializer.dumps(user_data)  # 암호화된 데이터 생성
    
    response = RedirectResponse(url="/index", status_code=302)
    response.set_cookie(
        key="user_data",
        value=encrypted_data,
        max_age=18144000,  # 6개월 유지
        httponly=True,  # 클라이언트 JavaScript 접근 제한
        samesite="Lax"  # CSRF 보호 강화
    )
    return response

@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(
    request: Request,
    nicknameoremail: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter((User.nickname == nicknameoremail) | (User.email == nicknameoremail))
        .first()
    )
    if user and user.is_deleted:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "message": "탈퇴 대기 중인 계정입니다. 복구하려면 고객센터에 문의하세요."},
        )
    if user and bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
        user_data = {'id': user.id, 'nickname': user.nickname}
        encrypted_data = serializer.dumps(user_data)

        response = RedirectResponse(url="/", status_code=302)

        # 쿠키 만료 시간을 7일(604800초)로 설정
        response.set_cookie(
            key="user_data",
            value=encrypted_data,
            max_age=18144000,  # 7일 (7 * 24 * 60 * 60)
            httponly=True,  # 클라이언트 JavaScript 접근 제한
            samesite="Lax"  # CSRF 보호 강화
        )
        return response
    
    else:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "message": "닉네임/이메일 또는 비밀번호가 잘못되었습니다."},
        )

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