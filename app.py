import hashlib
import subprocess
from datetime import datetime
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature, BadData
import os
from quart import Quart, request, render_template, send_from_directory, jsonify, redirect, url_for, session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from shemas.repository import Repo, engine


app = Quart(__name__)
app.secret_key = os.urandom(24)  # ключ для шифрования токенов
serializer = URLSafeTimedSerializer(app.secret_key)

async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

UPLOAD_FOLDER = 'files'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER                 # папка загрузки файлов
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024         # max 16mb
ALLOWED_EXTENSIONS = {'fb2', 'epub', 'pdf'}                 # разрешённые типы файлов
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


@app.route('/files/<path:filename>')                        # директория загрузки файлов
async def serve_file(filename):
    return await send_from_directory('files', filename)


def generate_token(username):                               # создание токена
    return serializer.dumps(username)


def verify_token(token):                                    # проверка токена
    try:
        username = serializer.loads(token, max_age=3600)  # Токен действителен 1 час
        return username
    except SignatureExpired:
        print("Токен истек.")
        return None
    except BadSignature:
        print("Недействительная подпись токена.")
        return None
    except BadData:
        print("Некорректные данные токена.")
        return None
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        return None


@app.route('/login')
async def log():
    return await render_template("login.html")


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


@app.route('/login', methods=['POST'])
async def login():
    form_data = await request.form
    username = form_data.get('username')
    password = form_data.get('password')
    hashed_password = hash_password(password)
    answer = await Repo.select_user(username, hashed_password)
    if answer is True:
        token = generate_token(username)
        session['token'] = token
        return redirect(url_for('index'))
    return jsonify({"message": "Ошибка доступа"}), 401


@app.route('/')
async def index():
    page = int(request.args.get('page', 1))
    per_page = 20
    async with async_session() as sessions:
        async with sessions.begin():
            category = await Repo.category(sessions)
            books = await Repo.sorted_recent(sessions, page, per_page)
            total_books = await Repo.count_books(sessions)
        return await render_template(
            'index.html', book_all=books, total_books=total_books,
                                           page=page, per_page=per_page, category=category
        )


@app.route("/select_category", methods=['GET'])
async def query_method():
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
            'index.html', book_all=books, total_books=total_books, name=name,
            page=page, per_page=per_page, link=link, category=category
        )


@app.route('/search', methods=['POST'])
async def search_book_author():
    form_data = await request.form
    search = form_data.get('search')
    search_type = form_data.get('search_type')
    async with async_session() as sessions:
        async with sessions.begin():
            books = await Repo.search_book(search, search_type)
            if books is None:
                return await render_template('search.html', err='По запросу ничего не найдено,'
                                                                  ' измените параметры поиска')
    return await render_template('search.html',books=books)


def generate_file_hash(file):                              # хеширование имени файла
    hash_md5 = hashlib.md5()
    for chunk in iter(lambda: file.read(4096), b""):
        hash_md5.update(chunk)
    file.seek(0)
    return hash_md5.hexdigest()


@app.route('/upload')
async def upload_form():
    token = session.get('token')  # Извлечение токена из сессии
    access = verify_token(token)
    if access:
        return await render_template("upload.html")
    return await render_template("login.html")


def create_directory(now):
    create_folder = now.strftime("%Y-%m-%d")
    dir_name = os.path.join(f"files/{create_folder[:4]}", create_folder)
    try:
        os.makedirs(dir_name, exist_ok=True)
        return create_folder
    except OSError as e:
        return f"Ошибка при создании директории: {str(e)}"


def allowed_file(filename):                                 # проверка допустимых типов файлов
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/upload', methods=['POST'])
async def upload_file():
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
        q = ('Недопустимый тип файла. Пожалуйста, загрузите файл с одним из следующих расширений: '
              '.fb2', '.pdf', '.epub')
        return await render_template("upload.html", success=q)

    if file.content_length > app.config['MAX_CONTENT_LENGTH']:
        q = 'Файл слишком большой. Максимальный размер файла 16MB.'
        return await render_template("upload.html", success=q)

    file_hash = generate_file_hash(file)
    file_extension = file.filename.rsplit('.', 1)[1].lower()
    dir_name = create_directory(now)
    print("dir_name", dir_name)
    new_filename = f"{dir_name[:4]}/{dir_name}/{title}_{file_hash}.{file_extension}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
    print("file_path", file_path)
    await file.save(file_path)

    l = [title, author, category, description, new_filename, date]
    await Repo.insert_new_book(l)

    q = f'Файл успешно загружен'
    return await render_template("upload.html", success=q)

@app.route('/delete')
async def delete_file():
    token = session.get('token')  # Извлечение токена из сессии
    access = verify_token(token)
    if access:
        return await render_template("delete.html")
    return await render_template("login.html")


@app.route('/drop_file', methods=['POST'])
async def drop_file():
    form_data = await request.form
    ssid = form_data.get('id')
    answer = await Repo.drop_file(ssid)
    if answer is not None:
        file_path = os.path.join('files/', answer)
        if os.path.exists(file_path):
            os.remove(file_path)
        else:
            print(f"Файл {file_path} не найден.")
    return await render_template('delete.html', answer=answer)


if __name__ == '__main__':
    app.run(debug=False)

