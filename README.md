# Proxy Access

Веб-сервис для управления доступом к прокси-серверам через ключи активации.

## Стек

- **Backend**: FastAPI + SQLAlchemy + PostgreSQL
- **Frontend**: Vue 3 + Vuetify 3
- **Desktop**: PyQt6
- **Очереди**: Celery + Redis
- **Контейнеризация**: Docker + docker-compose

---

## Быстрый старт

### 1. Клонируй репозиторий

```bash
git clone https://github.com/DizmaeR/TestCase_ProxyAccess.git
cd TestCase_ProxyAccess
```

### 2. Создай `.env` файл в корне проекта

```bash
APP_MODE=localhost
APP_PORT=8002

PG_HOST=postgres
PG_PORT=5432
PG_DATABASE=db_proxy
PG_USERNAME=user
PG_PASSWORD=your_password

JWT_SECRET_KEY=your_secret_key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_DAYS=3

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password

MAIL_USERNAME=your_mailtrap_username
MAIL_PASSWORD=your_mailtrap_password
MAIL_FROM=noreply@proxyaccess.com
MAIL_SERVER=sandbox.smtp.mailtrap.io
MAIL_PORT=587
```

### 3. Запусти проект одной командой

```bash
docker-compose up -d --build
```

После запуска доступно:

| Сервис | Адрес |
|--------|-------|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8002 |
| Swagger UI | http://localhost:8002/docs |

---

## Как зарегистрироваться

1. Открой http://localhost:5173/register
2. Введи email и пароль
3. Нажми **"Зарегистрироваться"**
4. Аккаунт активируется автоматически
5. Ключ активации отправляется на email

---

## Как получить ключ активации

**Способ 1** — через email (Mailtrap):
- После регистрации письмо придёт в Mailtrap sandbox
- Зайди на mailtrap.io и найди письмо с ключом

**Способ 2** — через личный кабинет:
- Зайди на http://localhost:5173/profile
- Нажми **"Обновить ключ"** — новый ключ придёт на email

**Способ 3** — напрямую из БД (для тестирования):
```bash
docker-compose exec postgres psql -U user -d db_proxy \
  -c "SELECT email, activation_key FROM users WHERE email = 'your@email.com';"
```

---

## Как запустить десктопное приложение

### Требования
- Python 3.10+
- Запущенный backend (`docker-compose up -d`)

### Установка

```bash
cd desktop
pip install -r requirements.txt
```

### Запуск

```bash
python main.py
```

### Использование

1. Введи **email** и **пароль** от аккаунта
2. Нажми **"Войти"**
3. Вставь **ключ активации** из email или личного кабинета
4. Нажми **"Подключиться"**
5. Приложение покажет данные прокси-сервера и статус подключения в реальном времени через WebSocket
6. Для завершения работы нажми **"Отключиться"**

---

## Запуск тестов

```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v
```

17 тестов покрывают: авторизацию, профиль, логику прокси.

---

## Тестовые прокси-серверы

При первом запуске автоматически создаются тестовые VM:

| Имя | Хост | Порт | Протокол |
|-----|------|------|----------|
| proxy-1 | 192.168.1.1 | 1080 | socks5 |
| proxy-2 | 192.168.1.2 | 1080 | socks5 |
| proxy-3 | 192.168.1.3 | 8080 | http |

---

## Архитектура

```
docker-compose
├── backend   (FastAPI, порт 8002)
├── frontend  (Vue 3 + Nginx, порт 5173)
├── postgres  (PostgreSQL 16)
├── redis     (Redis 7)
└── celery    (Celery Worker)
```

```
Запрос → api/ → services/ → repositories/ → БД
                    ↓
               Celery → Email
                    ↓
              WebSocket → Desktop
```

---

## API документация

Swagger UI: http://localhost:8002/docs