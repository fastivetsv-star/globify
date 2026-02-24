import os
import shutil
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import FastAPI, Request, Depends, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from passlib.context import CryptContext
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv

# 1. Завантажуємо секретний сейф
load_dotenv()

# 2. Налаштування додатку
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY"))

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 3. Налаштування Бази Даних
SQLALCHEMY_DATABASE_URL = os.getenv("DB_URL")
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 4. Налаштування Пошти
SENDER_EMAIL = os.getenv("EMAIL_SENDER")
SENDER_PASSWORD = os.getenv("EMAIL_PASSWORD")

def send_verification_email(receiver_email: str, token: str):
    subject = "Підтвердження реєстрації на GlobiFy 🚀"
    verification_link = f"https://globify-site.onrender.com/verify/{token}"
    
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; text-align: center; padding: 30px; background-color: #f8f9fa;">
            <div style="max-width: 500px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                <h2 style="color: #333;">Вітаємо у GlobiFy! 🎉</h2>
                <p style="color: #555; font-size: 16px;">Дякуємо за реєстрацію. Щоб активувати ваш акаунт, натисніть на кнопку нижче:</p>
                <a href="{verification_link}" style="display: inline-block; padding: 12px 25px; color: white; background-color: #ffc107; text-decoration: none; border-radius: 50px; font-weight: bold; margin-top: 20px; font-size: 16px;">Підтвердити пошту</a>
            </div>
        </body>
    </html>
    """
    
    msg = MIMEMultipart()
    msg["From"] = f"GlobiFy <{SENDER_EMAIL}>"
    msg["To"] = receiver_email
    msg["Subject"] = subject
    msg.attach(MIMEText(html_content, "html"))
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()  # Цей рядок обов'язковий для порту 587! Він шифрує з'єднання.
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
            print(f"✅ УРА! Лист успішно відправлено на {receiver_email}")
    except Exception as e:
        print(f"❌ Помилка відправки листа: {e}")
        # Хакерське посилання для логів:
        print(f"🔥 ХАКЕРСЬКЕ ПОСИЛАННЯ ДЛЯ ПІДТВЕРДЖЕННЯ: {verification_link}")

# Хешування паролів
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- 2. МОДЕЛІ ДАНИХ ---
class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_verified = Column(Boolean, default=False)
    verify_token = Column(String)
    avatar_url = Column(String, default="")
    bio = Column(String, default="")

class FilmDB(Base):
    __tablename__ = "films"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    author = Column(String)
    rating = Column(Float)
    link = Column(String)
    owner_id = Column(Integer)
    is_shared = Column(Boolean, default=False)
    image_url = Column(String, default="")

class BookDB(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    author = Column(String)
    rating = Column(Float)
    link = Column(String)
    owner_id = Column(Integer)
    is_shared = Column(Boolean, default=False)
    image_url = Column(String, default="")

class MusicDB(Base):
    __tablename__ = "music"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    author = Column(String)
    rating = Column(Float)
    link = Column(String)
    owner_id = Column(Integer)
    is_shared = Column(Boolean, default=False)
    image_url = Column(String, default="")

class VideoDB(Base):
    __tablename__ = "videos"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    author = Column(String)
    rating = Column(Float)
    link = Column(String)
    owner_id = Column(Integer)
    is_shared = Column(Boolean, default=False)
    image_url = Column(String, default="")

# Створюємо таблиці
Base.metadata.create_all(bind=engine)

# --- 4. ДОПОМІЖНІ ФУНКЦІЇ ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(request: Request, db: Session):
    username = request.session.get("user")
    if not username:
        return None
    user = db.query(UserDB).filter(UserDB.username == username).first()
    return user


# --- 5. МАРШРУТИ ---

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    
    if not current_user:
        return templates.TemplateResponse("index.html", {"request": request, "user": None})
    
    # 📊 Статистика
    films_count = db.query(FilmDB).filter(FilmDB.owner_id == current_user.id).count()
    books_count = db.query(BookDB).filter(BookDB.owner_id == current_user.id).count()
    music_count = db.query(MusicDB).filter(MusicDB.owner_id == current_user.id).count()
    videos_count = db.query(VideoDB).filter(VideoDB.owner_id == current_user.id).count()
    
    # 📌 1. МОЇ закріплені матеріали
    my_films = db.query(FilmDB).filter(FilmDB.owner_id == current_user.id, FilmDB.is_shared == True).order_by(FilmDB.rating.desc()).all()
    my_books = db.query(BookDB).filter(BookDB.owner_id == current_user.id, BookDB.is_shared == True).order_by(BookDB.rating.desc()).all()
    my_music = db.query(MusicDB).filter(MusicDB.owner_id == current_user.id, MusicDB.is_shared == True).order_by(MusicDB.rating.desc()).all()
    my_videos = db.query(VideoDB).filter(VideoDB.owner_id == current_user.id, VideoDB.is_shared == True).order_by(VideoDB.rating.desc()).all()

    # 🌍 2. ГЛОБАЛЬНА СТРІЧКА
    global_films = db.query(FilmDB, UserDB).join(UserDB, FilmDB.owner_id == UserDB.id).filter(FilmDB.is_shared == True, FilmDB.owner_id != current_user.id).order_by(FilmDB.rating.desc()).all()
    global_books = db.query(BookDB, UserDB).join(UserDB, BookDB.owner_id == UserDB.id).filter(BookDB.is_shared == True, BookDB.owner_id != current_user.id).order_by(BookDB.rating.desc()).all()
    global_music = db.query(MusicDB, UserDB).join(UserDB, MusicDB.owner_id == UserDB.id).filter(MusicDB.is_shared == True, MusicDB.owner_id != current_user.id).order_by(MusicDB.rating.desc()).all()
    global_videos = db.query(VideoDB, UserDB).join(UserDB, VideoDB.owner_id == UserDB.id).filter(VideoDB.is_shared == True, VideoDB.owner_id != current_user.id).order_by(VideoDB.rating.desc()).all()

    return templates.TemplateResponse("index.html", {
        "request": request, 
        "user": current_user.username,
        "films_count": films_count,
        "books_count": books_count,
        "music_count": music_count,
        "videos_count": videos_count,
        "my_films": my_films,
        "my_books": my_books,
        "my_music": my_music,
        "my_videos": my_videos,
        "global_films": global_films,
        "global_books": global_books,
        "global_music": global_music,
        "global_videos": global_videos
    })

# --- РЕЄСТРАЦІЯ ---
@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
async def register_user(username: str = Form(...), email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    if db.query(UserDB).filter((UserDB.username == username) | (UserDB.email == email)).first():
        return HTMLResponse("<h3>Користувач з таким логіном або поштою вже існує! <a href='/register'>Назад</a></h3>")
    
    hashed_pass = pwd_context.hash(password)
    token = str(uuid.uuid4())
    
    new_user = UserDB(username=username, email=email, hashed_password=hashed_pass, is_verified=False, verify_token=token)
    db.add(new_user)
    db.commit()

    send_verification_email(email, token)

    return HTMLResponse(f"""
        <div style='text-align: center; margin-top: 50px; font-family: sans-serif;'>
            <h2>🎉 Реєстрація майже завершена!</h2>
            <p>Ми відправили лист на <b>{email}</b>.</p>
            <p><i>Будь ласка, перевірте вашу пошту (та папку Спам) і натисніть на кнопку підтвердження.</i></p>
        </div>
    """)

@app.get("/verify/{token}")
async def verify_email(token: str, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.verify_token == token).first()
    if not user:
        return HTMLResponse("<h3 style='text-align:center; color:red;'>❌ Недійсне посилання або акаунт вже підтверджено!</h3>")
    
    user.is_verified = True
    user.verify_token = ""
    db.commit()
    return HTMLResponse("<h3 style='text-align:center; color:green; mt-5'>✅ Пошту успішно підтверджено! Тепер ви можете <a href='/login'>увійти</a>.</h3>")

# --- ВХІД ---
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login_user(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.username == username).first()
    
    if not user or not pwd_context.verify(password, user.hashed_password):
        return HTMLResponse("<h3>Невірний логін або пароль! <a href='/login'>Спробувати ще раз</a></h3>")
    
    if not user.is_verified:
        return HTMLResponse("<h3>⚠️ Ваш акаунт не підтверджено! Перевірте електронну пошту. <a href='/login'>Назад</a></h3>")
        
    request.session["user"] = user.username
    return RedirectResponse(url="/", status_code=303)

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)

# --- МІЙ ПРОФІЛЬ ---
@app.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    
    return templates.TemplateResponse("profile.html", {"request": request, "user_data": current_user})

@app.post("/profile")
async def update_profile(
    request: Request, 
    bio: str = Form(""), 
    avatar_file: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    current_user = get_current_user(request, db)
    if current_user:
        current_user.bio = bio
        
        if avatar_file and avatar_file.filename:
            allowed_extensions = {"jpg", "jpeg", "png", "webp"}
            file_extension = avatar_file.filename.split(".")[-1].lower()
            
            if file_extension not in allowed_extensions:
                return HTMLResponse("<h3 style='text-align:center; color:red; margin-top:50px;'>❌ Помилка: Можна завантажувати тільки картинки (.jpg, .png, .webp)! <br><br><a href='/profile'>Повернутися назад</a></h3>")
            
            new_filename = f"avatar_{current_user.id}_{uuid.uuid4().hex[:8]}.{file_extension}"
            file_path = os.path.join(UPLOAD_DIR, new_filename)
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(avatar_file.file, buffer)
            
            current_user.avatar_url = f"/{file_path}"
            
        db.commit()
    return RedirectResponse(url="/profile", status_code=303)

# --- КАТАЛОГИ ---
@app.get("/films", response_class=HTMLResponse)
async def films_list(request: Request, q: str = None, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if not current_user: return RedirectResponse(url="/login", status_code=303)
    query = db.query(FilmDB).filter(FilmDB.owner_id == current_user.id)
    if q: query = query.filter(FilmDB.title.ilike(f"%{q}%"))
    films = query.order_by(FilmDB.rating.desc()).all()
    return templates.TemplateResponse("films.html", {"request": request, "films": films, "user": current_user.username})

@app.get("/books", response_class=HTMLResponse)
async def books_list(request: Request, q: str = None, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if not current_user: return RedirectResponse(url="/login", status_code=303)
    query = db.query(BookDB).filter(BookDB.owner_id == current_user.id)
    if q: query = query.filter(BookDB.title.ilike(f"%{q}%"))
    books = query.order_by(BookDB.rating.desc()).all()
    return templates.TemplateResponse("books.html", {"request": request, "books": books, "user": current_user.username})

@app.get("/music", response_class=HTMLResponse)
async def music_list(request: Request, q: str = None, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if not current_user: return RedirectResponse(url="/login", status_code=303)
    query = db.query(MusicDB).filter(MusicDB.owner_id == current_user.id)
    if q: query = query.filter(MusicDB.title.ilike(f"%{q}%"))
    music = query.order_by(MusicDB.rating.desc()).all()
    return templates.TemplateResponse("music.html", {"request": request, "music": music, "user": current_user.username})

@app.get("/video", response_class=HTMLResponse)
async def video_list(request: Request, q: str = None, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if not current_user: return RedirectResponse(url="/login", status_code=303)
    query = db.query(VideoDB).filter(VideoDB.owner_id == current_user.id)
    if q: query = query.filter(VideoDB.title.ilike(f"%{q}%"))
    videos = query.order_by(VideoDB.rating.desc()).all()
    return templates.TemplateResponse("video.html", {"request": request, "videos": videos, "user": current_user.username})

# --- ДОДАВАННЯ ---
@app.post("/add_film")
async def add_new_film(request: Request, title: str = Form(...), author: str = Form(...), rating: float = Form(...), link: str = Form(""), image_url: str = Form(""), db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if current_user:
        new_item = FilmDB(title=title, author=author, rating=rating, link=link, image_url=image_url, owner_id=current_user.id)
        db.add(new_item)
        db.commit()
    return RedirectResponse(url="/films", status_code=303)

@app.post("/add_book")
async def add_new_book(request: Request, title: str = Form(...), author: str = Form(...), rating: float = Form(...), link: str = Form(""), db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if current_user:
        new_item = BookDB(title=title, author=author, rating=rating, link=link, owner_id=current_user.id)
        db.add(new_item)
        db.commit()
    return RedirectResponse(url="/books", status_code=303)

@app.post("/add_music")
async def add_new_music(request: Request, title: str = Form(...), author: str = Form(...), rating: float = Form(...), link: str = Form(""), db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if current_user:
        new_item = MusicDB(title=title, author=author, rating=rating, link=link, owner_id=current_user.id)
        db.add(new_item)
        db.commit()
    return RedirectResponse(url="/music", status_code=303)

@app.post("/add_video")
async def add_new_video(request: Request, title: str = Form(...), author: str = Form(...), rating: float = Form(...), link: str = Form(""), db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if current_user:
        new_item = VideoDB(title=title, author=author, rating=rating, link=link, owner_id=current_user.id)
        db.add(new_item)
        db.commit()
    return RedirectResponse(url="/video", status_code=303)

# --- ВИДАЛЕННЯ ---
@app.get("/delete_film/{item_id}")
async def delete_film(item_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user:
        item = db.query(FilmDB).filter(FilmDB.id == item_id, FilmDB.owner_id == user.id).first()
        if item:
            db.delete(item)
            db.commit()
    return RedirectResponse(url="/films", status_code=303)

@app.get("/delete_book/{item_id}")
async def delete_book(item_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user:
        item = db.query(BookDB).filter(BookDB.id == item_id, BookDB.owner_id == user.id).first()
        if item:
            db.delete(item)
            db.commit()
    return RedirectResponse(url="/books", status_code=303)

@app.get("/delete_music/{item_id}")
async def delete_music(item_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user:
        item = db.query(MusicDB).filter(MusicDB.id == item_id, MusicDB.owner_id == user.id).first()
        if item:
            db.delete(item)
            db.commit()
    return RedirectResponse(url="/music", status_code=303)

@app.get("/delete_video/{item_id}")
async def delete_video(item_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user:
        item = db.query(VideoDB).filter(VideoDB.id == item_id, VideoDB.owner_id == user.id).first()
        if item:
            db.delete(item)
            db.commit()
    return RedirectResponse(url="/video", status_code=303)

# --- РЕПОСТИ (ПОШИРЕННЯ) ---
@app.get("/share_film/{item_id}")
async def share_film(item_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user:
        item = db.query(FilmDB).filter(FilmDB.id == item_id, FilmDB.owner_id == user.id).first()
        if item:
            item.is_shared = not item.is_shared
            db.commit()
    return RedirectResponse(url="/films", status_code=303)

@app.get("/share_book/{item_id}")
async def share_book(item_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user:
        item = db.query(BookDB).filter(BookDB.id == item_id, BookDB.owner_id == user.id).first()
        if item:
            item.is_shared = not item.is_shared
            db.commit()
    return RedirectResponse(url="/books", status_code=303)

@app.get("/share_music/{item_id}")
async def share_music(item_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user:
        item = db.query(MusicDB).filter(MusicDB.id == item_id, MusicDB.owner_id == user.id).first()
        if item:
            item.is_shared = not item.is_shared
            db.commit()
    return RedirectResponse(url="/music", status_code=303)

@app.get("/share_video/{item_id}")
async def share_video(item_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user:
        item = db.query(VideoDB).filter(VideoDB.id == item_id, VideoDB.owner_id == user.id).first()
        if item:
            item.is_shared = not item.is_shared
            db.commit()
    return RedirectResponse(url="/video", status_code=303)

# --- РЕДАГУВАННЯ ЗАПИСІВ ---
@app.get("/edit_film/{item_id}", response_class=HTMLResponse)
async def edit_film_page(item_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user: return RedirectResponse(url="/login", status_code=303)
    item = db.query(FilmDB).filter(FilmDB.id == item_id, FilmDB.owner_id == user.id).first()
    return templates.TemplateResponse("edit.html", {"request": request, "item": item, "category": "film", "return_url": "films"})

@app.post("/edit_film/{item_id}")
async def edit_film_post(item_id: int, request: Request, title: str = Form(...), author: str = Form(...), rating: float = Form(...), link: str = Form(""), image_url: str = Form(""), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user:
        item = db.query(FilmDB).filter(FilmDB.id == item_id, FilmDB.owner_id == user.id).first()
        if item:
            item.title, item.author, item.rating, item.link, item.image_url = title, author, rating, link, image_url
            db.commit()
    return RedirectResponse(url="/films", status_code=303)

@app.get("/edit_book/{item_id}", response_class=HTMLResponse)
async def edit_book_page(item_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user: return RedirectResponse(url="/login", status_code=303)
    item = db.query(BookDB).filter(BookDB.id == item_id, BookDB.owner_id == user.id).first()
    return templates.TemplateResponse("edit.html", {"request": request, "item": item, "category": "book", "return_url": "books"})

@app.post("/edit_book/{item_id}")
async def edit_book_post(item_id: int, request: Request, title: str = Form(...), author: str = Form(...), rating: float = Form(...), link: str = Form(""), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user:
        item = db.query(BookDB).filter(BookDB.id == item_id, BookDB.owner_id == user.id).first()
        if item:
            item.title, item.author, item.rating, item.link = title, author, rating, link
            db.commit()
    return RedirectResponse(url="/books", status_code=303)

@app.get("/edit_music/{item_id}", response_class=HTMLResponse)
async def edit_music_page(item_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user: return RedirectResponse(url="/login", status_code=303)
    item = db.query(MusicDB).filter(MusicDB.id == item_id, MusicDB.owner_id == user.id).first()
    return templates.TemplateResponse("edit.html", {"request": request, "item": item, "category": "music", "return_url": "music"})

@app.post("/edit_music/{item_id}")
async def edit_music_post(item_id: int, request: Request, title: str = Form(...), author: str = Form(...), rating: float = Form(...), link: str = Form(""), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user:
        item = db.query(MusicDB).filter(MusicDB.id == item_id, MusicDB.owner_id == user.id).first()
        if item:
            item.title, item.author, item.rating, item.link = title, author, rating, link
            db.commit()
    return RedirectResponse(url="/music", status_code=303)

@app.get("/edit_video/{item_id}", response_class=HTMLResponse)
async def edit_video_page(item_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user: return RedirectResponse(url="/login", status_code=303)
    item = db.query(VideoDB).filter(VideoDB.id == item_id, VideoDB.owner_id == user.id).first()
    return templates.TemplateResponse("edit.html", {"request": request, "item": item, "category": "video", "return_url": "video"})

@app.post("/edit_video/{item_id}")
async def edit_video_post(item_id: int, request: Request, title: str = Form(...), author: str = Form(...), rating: float = Form(...), link: str = Form(""), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user:
        item = db.query(VideoDB).filter(VideoDB.id == item_id, VideoDB.owner_id == user.id).first()
        if item:
            item.title, item.author, item.rating, item.link = title, author, rating, link
            db.commit()
    return RedirectResponse(url="/video", status_code=303)

@app.get("/contacts", response_class=HTMLResponse)
async def contacts(request: Request):
    return HTMLResponse("<h1>Контакти</h1><a href='/'>Назад</a>")





# cd my_homework/my_flask_site
# source ../../venv/Scripts/activate
# uvicorn main:app --reload