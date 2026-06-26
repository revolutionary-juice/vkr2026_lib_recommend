# Прототип рекомендательной системы для пользователей Научной библиотеки ДВФУ

ВКР Яковлев Кирилл Андреевич, 09.03.04 Программная инженерия, ДВФУ 2026

---

## Запуск через Docker

Самый простой способ. Из программ нужен только Docker Desktop, больше ничего устанавливать не надо.

**Шаг 1.** Скачать и установить Docker Desktop

https://www.docker.com/products/docker-desktop/

**Шаг 2.** Клонировать репозиторий

Открыть терминал (можно прямо в IDE, например в PyCharm или VS Code) и выполнить

```bash
git clone https://github.com/revolutionary-juice/vkr2026_lib_recommend.git
```

**Шаг 3.** Перейти в папку проекта

```bash
cd vkr2026_lib_recommend
```

**Шаг 4.** Запустить

```bash
docker compose up
```

Первый раз займет несколько минут, Docker скачает всё что нужно и соберет контейнеры. Просто ждать пока в терминале не перестанут появляться новые сообщения.

**Шаг 5.** Открыть в браузере http://localhost:5173

Данные для входа

| Кто | Логин | Пароль |
|-----|-------|--------|
| Администратор | admin | admin |
| Тестовый пользователь | user001 | testpass123 |

Чтобы остановить нажать Ctrl+C в терминале, или в новом терминале выполнить

```bash
docker compose down
```

---

## Запуск без Docker

Нужно установить Python 3.10+, Node.js 20+, PostgreSQL 14+

**1. Клонировать репозиторий**

```bash
git clone https://github.com/revolutionary-juice/vkr2026_lib_recommend.git
cd vkr2026_lib_recommend
```

**2. Создать базу данных**

В pgAdmin или psql создать базу vkr_db с логином postgres и паролем 123456

```sql
CREATE DATABASE vkr_db;
```

Если пароль другой, поменяйте строку подключения в файле app/core/database.py

```python
DATABASE_URL = "postgresql+psycopg2://postgres:123456@127.0.0.1:5432/vkr_db"
```

Затем залить данные из дампа

```bash
psql -U postgres -d vkr_db -f dump.sql
```

**3. Запустить бэкенд**

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Бэкенд запустится на http://127.0.0.1:8000

**4. Запустить фронтенд (открыть второй терминал)**

```bash
cd frontend
npm install
npm run dev
```

Фронтенд запустится на http://localhost:5173

---

## Структура проекта

```
app/              бэкенд на FastAPI
frontend/         фронтенд на React
requirements.txt
docker-compose.yml
dump.sql          данные базы (загружаются автоматически при запуске через Docker)
```

---

## API документация

Когда бэкенд запущен, документация доступна по адресу http://127.0.0.1:8000/docs
