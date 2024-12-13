import hashlib
import os
from quart import Quart, request, render_template, send_from_directory
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from shemas.repository import Repo
from create.create_structure import engine

app = Quart(__name__)

async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

UPLOAD_FOLDER = 'files'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER                 # папка загрузки файлов
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024         # max 16mb
ALLOWED_EXTENSIONS = {'fb2', 'epub', 'pdf'}                 # разрешённые типы файлов
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/files/<path:filename>')                        # директория загрузки файлов
async def serve_file(filename):
    return await send_from_directory('files', filename)

@app.route('/')
async def index():
    page = int(request.args.get('page', 1))
    per_page = 20
    async with async_session() as session:
        async with session.begin():
            books = await Repo.select_all_book()
            paginated_books = books[(page-1)*per_page:page*per_page]
    return await render_template('index.html', book_all=paginated_books,
                                 total_books=len(books), page=page, per_page=per_page)

@app.route('/')                                               # пагинация
async def pagination():
    page = int(request.args.get('page', 1))
    per_page = 20
    async with async_session() as session:
        async with session.begin():
            books = await Repo.select_all_book()
            paginated_books = books[(page-1)*per_page:page*per_page]
    pagination_links = []
    for i in range(1, int(len(books)/per_page) + 2):
        pagination_links.append(f'<a href="?page={i}">{i}</a>')
    return await render_template('index.html', book_all=paginated_books,
                                 total_books=len(books), page=page, per_page=per_page)

@app.route('/category')
async def sorted_category():
    page = int(request.args.get('page', 1))
    per_page = 20
    async with async_session() as session:
        async with session.begin():
            books = await Repo.sorted_category()
            paginated_books = books[(page-1)*per_page:page*per_page]
    return await render_template('index.html', book_all=paginated_books,
                                 total_books=len(books), page=page, per_page=per_page)

@app.route('/autor')
async def sorted_autor():
    page = int(request.args.get('page', 1))
    per_page = 20
    async with async_session() as session:
        async with session.begin():
            books = await Repo.sorted_autor()
            paginated_books = books[(page-1)*per_page:page*per_page]
    return await render_template('index.html', book_all=paginated_books,
                                 total_books=len(books), page=page, per_page=per_page)

@app.route('/search', methods=['POST'])
async def search_book_author():
    form_data = await request.form
    search = form_data.get('search')
    search_type = form_data.get('search_type')
    async with async_session() as session:
        async with session.begin():
            books = await Repo.search_book(search, search_type)
            print("books", books)
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
    return await render_template("upload.html")

def allowed_file(filename):                                 # проверка допустимых типов файлов
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
async def upload_file():
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
    new_filename = f"{file_hash}.{file_extension}"

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
    await file.save(file_path)

    l = [title, author, category, description, new_filename]
    await Repo.insert_new_book(l)

    q = f'Файл успешно загружен'
    return await render_template("upload.html", success=q)

@app.route('/delete')
async def delete_file():
    return await render_template("delete.html")

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
    return await render_template('delete.html')

if __name__ == '__main__':
    app.run(debug=False)

