Приложение предназначено для хранения хешированных файлов, сортировки и вывода хранимых файлов (типы указываются в конфигурации), 
быстрого поиска по сохранённым файлам.  
Использует MariaDB в качестве базы данных.


Перед тем как начать, убедитесь, что у вас установлены следующие компоненты:  

- **Python** (версия 3.11+)
- **MariaDB** (версия 10 или выше)
- **pip** 
- **virtualenv** (опционально)

## Установка

python -m venv venv
source venv/bin/activate  # Для macOS/Linux<br>
venv\Scripts\activate     # Для Windows

## Установите зависимости:
pip install -r requirements.txt

## Установите зависимости:
pip install -r requirements.txt

Структура файла .env в корне:  
DB_HOST="адрес хоста"  
DB_USER="имя пользователя"  
DB_PASSWORD="пароль"  
DB_NAME="название создаваемой базы данных"  
DB_PORT=3306  

user="имя пользователя"  
password="пароль пользователя"  
(второй блок задействуется в установке, можно после удалить)  


## Установка:  
Из корневой директории приложения  
*python3 -m create.install*

## Запуск приложения  
Для запуска приложения, выполните следующую команду:  
*python3 app.py*




