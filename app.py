import jwt
import hashlib
from functools import wraps
from datetime import datetime, timedelta, timezone
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature, BadData
import os
from quart import Quart, request, render_template, send_from_directory, jsonify, redirect, url_for, session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from shemas.repository import Repo, engine


app = Quart(__name__)
app.secret_key = os.urandom(24)
serializer = URLSafeTimedSerializer(app.secret_key)

async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

UPLOAD_FOLDER = 'files'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = {'doc', 'pdf'}
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


@app.route('/files/<path:filename>')
async def serve_file(filename):
    """The path to the destination files."""
    return await send_from_directory('files', filename)


def generate_token(username):
    """generation token"""
    payload = {
        'user': username,
        'exp': datetime.now(timezone.utc) + timedelta(hours=1)
    }
    return jwt.encode(payload, algorithm='HS256')


def verify_token(token):
    """verification token"""
    if not token:
        return False, None
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=['HS256'])
        username = payload.get('username')
        return True, username
    except (jwt.InvalidTokenError, jwt.ExpiredSignatureError):
        return False, None


def token_required(f):
    """checking the token by validation (control panel)"""
    @wraps(f)
    async def decorated(*args, **kwargs):
        token = request.cookies.get('token')
        if not token:
            return jsonify({"message": "Токен отсутствует"}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            if not data:
                return jsonify({"message": "Недостаточно прав"}), 403
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Токен истек"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Неверный токен"}), 401
        return await f(*args, **kwargs)
    return decorated


def hash_password(password: str) -> str:
    """Password Hashing. """
    return hashlib.sha256(password.encode()).hexdigest()


@app.route('/login', methods=['GET', 'POST'])
async def login():
    """Authorization."""
    if request.method == 'GET':
        return await render_template('login.html')

    form_data = await request.form
    username = form_data.get('user')
    password = form_data.get('password')
    hashed_password = hash_password(password)
    user = await Repo.select_user(username, hashed_password)

    if user:
        token = jwt.encode(
            {
                'username': user.username,
                'exp': datetime.now(timezone.utc) + timedelta(hours=1)
            },
            app.config['SECRET_KEY'],
            algorithm='HS256'
        )

        response = redirect(url_for('index'))
        response.set_cookie(
            'token',
            token,
            httponly=True,
            secure=False,
            samesite="Lax"
        )
        return response
    return jsonify({"message": "Access error"}), 401

@app.route('/logout')
async def logout():
    response = redirect(url_for('login'))
    session.pop('token', None)
    response.set_cookie('token', '', expires=0)
    return response

@app.route('/')
async def index():
    """Main page."""
    token = session.get('token')
    access = verify_token(token)
    page = int(request.args.get('page', 1))
    per_page = 20
    async with async_session() as sessions:
        async with sessions.begin():
            category = await Repo.category(sessions)
            books = await Repo.sorted_recent(sessions, page, per_page)
            total_books = await Repo.count_books(sessions)
        return await render_template(
            'index.html', book_all=books, total_books=total_books, access=access,
                                           page=page, per_page=per_page, category=category,
        )


@app.route("/select_category", methods=['GET'])
async def query_method():
    """Switching through categories."""
    token = session.get('token')
    access = verify_token(token)
    name = request.args.get("name")
    link = request.args.get("link")
    page = int(request.args.get('page', 1))
    per_page = 20
    async with async_session() as sessions:
        async with sessions.begin():
            category = await Repo.category(sessions)
            books = await Repo.all_query(sessions, page, per_page, link, name)
            total_books = await Repo.count_books(sessions)
        return await render_template(
            'index.html', book_all=books, total_books=total_books, name=name, access=access,
            page=page, per_page=per_page, link=link, category=category
        )


@app.route('/search', methods=['POST'])
async def search_book_author():
    """Search."""
    token = session.get('token')
    access = verify_token(token)
    form_data = await request.form
    search = form_data.get('search')
    search_type = form_data.get('search_type')
    async with async_session() as sessions:
        async with sessions.begin():
            books = await Repo.search_book(search, search_type)
            category = await Repo.category(sessions)
            if books is None:
                return await render_template('search.html', err='По запросу ничего не найдено,'
                                                                  ' измените параметры поиска')
    return await render_template('search.html',books=books, access=access, category=category)


def generate_file_hash(file):
    """Generating a hash of the file name."""
    hash_md5 = hashlib.md5()
    for chunk in iter(lambda: file.read(4096), b""):
        hash_md5.update(chunk)
    file.seek(0)
    return hash_md5.hexdigest()


@app.route('/upload')
@token_required
async def upload_form():
    """Redirect to upload form."""
    token = session.get('token')  # Извлечение токена из сессии
    access = verify_token(token)
    if access:
        return await render_template("upload.html")
    return await render_template("login.html")


def create_directory(now):
    """Create new directory (if not)."""
    create_folder = now.strftime("%Y-%m-%d")
    dir_name = os.path.join(f"files/{create_folder[:4]}", create_folder)
    try:
        os.makedirs(dir_name, exist_ok=True)
        return create_folder
    except OSError as e:
        return f"Ошибка при создании директории: {str(e)}"


def allowed_file(filename):
    """Checking valid file types."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/upload', methods=['POST'])
@token_required
async def upload_file():
    """Upload file."""
    now = datetime.now()
    date = now.strftime("%Y-%m-%d-%H-%M-%S")
    files = await request.files
    if 'file' not in files:
        q = 'Нет файла для загрузки'
        return await render_template("upload.html", succes=q)

    file = files['file']
    form_data = await request.form
    title = form_data.get('title')
    author = form_data.get('author')
    category = form_data.get('category')
    description = form_data.get('description')

    if file.filename == '':
        q = 'Нет выбранного файла'
        return await render_template("upload.html", success=q)

    if not allowed_file(file.filename):
        q = "Недопустимый тип файла. Пожалуйста, загрузите файл с одним из следующих расширений: '.pdf'"
        return await render_template("upload.html", success=q)

    if file.content_length > app.config['MAX_CONTENT_LENGTH']:
        q = 'Файл слишком большой. Максимальный размер файла 16MB.'
        return await render_template("upload.html", success=q)

    file_hash = generate_file_hash(file)
    file_extension = file.filename.rsplit('.', 1)[1].lower()
    dir_name = create_directory(now)
    new_filename = f"{dir_name[:4]}/{dir_name}/{title}_{file_hash}.{file_extension}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
    await file.save(file_path)

    items = [title, author, category, description, new_filename, date]
    await Repo.insert_new_book(items)

    q = 'Файл успешно загружен'
    return await render_template("upload.html", success=q)


@app.route('/delete')
@token_required
async def delete_file():
    """Redirect to delete file."""
    token = session.get('token')
    access = verify_token(token)
    if access:
        return await render_template("delete.html")
    return await render_template("login.html", access=access)


@app.route('/drop_file', methods=['POST'])
@token_required
async def drop_file():
    """Delete file."""
    token = session.get('token')
    access = verify_token(token)
    form_data = await request.form
    ssid = form_data.get('id')
    answer = await Repo.drop_file(ssid)
    if answer is not None:
        file_path = os.path.join('files/', answer)
        if os.path.exists(file_path):
            os.remove(file_path)
        else:
            print(f"Файл {file_path} не найден.")
    return await render_template('delete.html', answer=answer, access=access)


if __name__ == '__main__':
    app.run(debug=False)
