# Foodgram

## Описание проекта
Сервис для публикации рецептов. Пользователи могут создавать рецепты, добавлять их в избранное и формировать список покупок.

## Технологии
- Python
- Django
- Django REST Framework  
- PostgreSQL
- Docker
- Nginx

## Локальный запуск

### 1. Настройка окружения
Создайте `.env` файл в корне проекта:

```env
SECRET_KEY=ваш_секретный_ключ
DEBUG=True
DOMAIN=web
DOMAIN_IP=127.0.0.1

DB_NAME=foodgram
DB_USER=ваш_пользователь
DB_PASSWORD=ваш_пароль
DB_HOST=db
DB_PORT=5432
```

### 2. Создание тестового пользователя
```bash 
docker-compose exec backend python manage.py createsuperuser
```

### 3. Запуск миграций
```bash 
docker-compose exec backend python manage.py migrate
```

### 4. Запуск приложения
```bash 
docker-compose up -d --build
```

### 5. Документация OpenAPI
После запуска проекта документация доступна по адресу:: http://localhost/api/docs/