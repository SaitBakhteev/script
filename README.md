# Barter Platform - Платформа для обмена товарами

## 🚀 Установка и запуск проекта

### 1. Клонирование репозитория
Выполните в терминале:

Через SSH (рекомендуется)
```bash
git@github.com:SaitBakhteev/script.git
```
Или через HTTPS
```bash
https://github.com/SaitBakhteev/script.git
```
Перейдите в директория проекта
```bash
cd script
```

### 2. Создание виртуального окружения

```bash
python -m venv venv
```

#### Активация окружения
Windows:
```bash
venv\Scripts\activate
```
Linux/Mac:
```bash
source venv/bin/activate
```
#### Установка зависимостей
```bash
pip install -r requirements.txt
```

### 3. Настройка БД и запуск (по умолчанию SQLite)

#### Если у вас БД Postgres до выполните следующие действия:
- Откройте проект с помощью IDE и в файле <i>djangoProject/settings.py</i> закомментируйте строки, связанные с настройками SQLite и активируйте строки по Postgres:
 
```python
        # Настройки при использовании Sqlite
        #'ENGINE': 'django.db.backends.sqlite3',
        #'NAME': BASE_DIR / 'db.sqlite',

        # Настройки при использовании Postgres
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
        'USER': os.getenv('DB_USER'),
        'NAME': os.getenv('DB_NAME'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
```
- создайте в корневой директории проекта файл .env и пропишите там следующие данные:

```ini
DB_HOST=localhost  # или другой адрес, если не на локальном сервере
DB_PORT=5432  # или другой порт
DB_USER=<имя пользователя postgres>
DB_NAME=<название вашей базы данных>
DB_PASSWORD=<пароль базы данных>
``` 

#### Осуществите миграции и запустите сервер
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```
Сервер запустится по адресу: http://localhost:8000<br>

## 🔐 Первые шаги
1. Откройте <a href="http://localhost:8000/ads/">главную страницу</a>
2. Зарегистрируйтесь (кнопка "Регистрация")
3. Авторизуйтесь под своими данными
4. Начните работу с платформой

## ✨ Основные возможности
### 📢 Работа с объявлениями
- <b>Просмотр</b> всех объявлений с пагинацией
- <b>Создание</b> новых объявлений
- <b>Редактирование/удаление</b> своих объявлений
- <b>Фильтрация</b> по категориям и состоянию товара

### 🔄 Система обменов
- <b>Создание</b> предложений обмена
- <b>Просмотр</b> входящих/исходящих предложений
- <b>Управление</b> статусами предложений
- <b>История</b> выполненных обменов

## 🛠 Технические возможности
### 🧪 Тестирование
```bash
pytest ./ads/tests.py
```

### 📚 API Documentation
| <b>Инструмент</b>	             | <b>Ссылка</b>
|--------------------------------|--------------
| Swagger UI	                    | http://localhost:8000/api/docs
| ReDoc	                         | http://localhost:8000/api/redoc
| Schema (скачивание yml-файла)	 | http://localhost:8000/api/schema

### ⚠️ Важные заметки
1. Для изображений используйте только валидные URL, например:
```bash
https://example.com/valid-image.jpg
```
2. При создании объявления вводить валидные данные в поля, смотреть всплывающие подсказки.
3. Для SECRET_KEY в <i>djangoProject/settings.py</i> стоит заглушка. Если хотите применить 
другое значение SECRET_KEY, то закомментируйте проделайте следующие действия:
   - закомментируйте заглушку и активируйте строку ниже
    ```python
        #SECRET_KEY = 'django-insecure-)-rn7#1bmb+)159b#5dtxu-e+d3b59uvdu5*=^)*#@&6b)vh74'
        SECRET_KEY = os.getenv('SECRET_KEY')
    ```
   - пропишите в файле .env другое значение 
    ```ini
        SECRET_KEY=<ваше значение>        
    ```

 
## 📂 Структура проекта

```
django_test_21_05_25/
├── ads/               # Основное приложение
│   ├── models.py      # Модели данных
│   ├── views.py       # Логика представлений
│   └── tests.py       # Тесты
├── sign/              # Авторизация
├── templates/         # Шаблоны
├── requirements.txt   # Зависимости
└── manage.py          # Управление
```
