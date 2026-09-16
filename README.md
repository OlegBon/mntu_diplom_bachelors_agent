# ІС Ідентифікації Діамантів (mntu_diplom_bachelors)

![Repo Status](https://img.shields.io/badge/status-active-brightgreen)
![Python Version](https://img.shields.io/badge/python-3.13-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-05998b)
![MariaDB](https://img.shields.io/badge/MariaDB-Local-003545)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Render-336791)
![License](https://img.shields.io/badge/license-MIT-yellow)

**Кваліфікаційна робота бакалавра**
**Тема:** Розроблення інформаційної системи ідентифікації діамантів.
**Заклад:** МНТУ (MNTU)

## 📌 Опис проєкту

Система призначена для автоматизації роботи гемологів, проведення інтелектуального аналізу фізичних характеристик діамантів та прогнозування їхньої ринкової вартості на основі моделей машинного навчання.

## 🏗 Архітектура системи

Проєкт базується на каскадній обробці даних та розділенні на три логічні зони (БД):

- **OLTP (diamond_oltp)**: Зберігання транзакційних даних експертів та звітів.
- **Market (diamond_market)**: Зберігання довідників IDC (Grade Mappings) та динамічних індексів цін.
- **Analytics (diamond_analytics)**: Результати роботи ML-моделей та кластеризації.

## 🧭 Структура репозиторію

```
mntu_diplom/
├── .venv/            # Віртуальне середовище Python
├── .gitignore        # Файл для ігнорування системного сміття
├── .env              # Приватні локальні змінні середовища (не потрапляє в Git)
├── .env.example      # Безпечний шаблон змінних без реальних значень
├── requirements.txt  # Залежності Python
├── data/
│ └── diamonds_dataset.csv
├── scripts/
│ ├── seed_db.py       # Єдиний руйнівний локальний seed усіх трьох схем
│ └── recalc_grades.py # Скрипт масового перерахунку оцінок (Backfill)
├── backend/           # FastAPI додаток (Python)
│ ├── __init__.py      # Щоб Python вважав цю папку модулем
│ ├── calculator.py    # Логіка оцінки (IDC Rules)
│ ├── config.py        # Валідація локальної конфігурації без fallback-секретів
│ ├── crud.py          # Операції з БД (Repository pattern)
│ ├── database.py      # Налаштування SQLAlchemy (Singleton)
│ ├── main.py          # Точка входу (FastAPI)
│ ├── models.py        # Опис таблиць бази даних (ORM)
│ ├── schemas.py       # Валідація даних (Pydantic)
│ ├── security.py      # Авторизація та JWT
└── frontend/          # Фронтенд на Pug/SCSS
  ├── src/             # Вихідні коди (Pug, SCSS, JS Modules)
  ├── dist/            # Скомпільований результат (HTML/CSS/JS)
  ├── gulpfile.js      # Налаштування збірки (Gulp 5)
  └── package.json     # Залежності Node.js
```

## ✅ Поточний стан реалізації

### 🗄️ База Даних та Дані

- [x] Розроблено схему для трьох баз: **OLTP, Market, Analytics**.
- [x] Реалізовано "Розумний Сідер", який генерує фізичні виміри та наповнює ринкові довідники.
- [x] Налаштовано **SQLAlchemy ORM** із використанням патерну **Singleton**.

### ⚙️ Backend API (FastAPI)

- [x] **Core:** Повний **CRUD** для звітів та користувачів.
- [x] **Intelligent Core:** Модуль `Calculator` (стандарти IDC) для автоматичного визначення `Cut Grade`.
- [ ] **Authoritative pricing / ML:** потребує окремо погоджених джерела, фінансового контракту та provenance; demo-прогноз не записується як ціна.
- [x] **Market Control:** Реалізовано API для отримання довідників (`/market/mappings`) та **адміністрування ринкових цін** (`/market/price`).
- [x] **Admin Panel API:** Управління персоналом (RBAC) та перегляд глобальної статистики.
- [x] **Backfill:** Скрипт перерахунку історичних даних при зміні алгоритмів.
- [x] **Pagination & Search:** Пошук звітів (`DR-XXXXX`) та пагінація.
- [x] Реалізовано валідацію вхідних даних через **Pydantic** (Schemas).
- [x] Реалізовано **пагінацію** для списків даних.
- [x] Реалізовано збір **статистики** ефективності експертів.

### 🎨 Frontend (Web UI)

- [x] **Architecture:** Налаштовано збірку Gulp + Pug + SCSS (Dart Sass).
- [x] **Responsive Layout:** Реалізовано адаптивну сітку (Desktop / Tablet / Mobile).
- [x] **Smart Header:**
  - Автоматичне визначення ролі (Гість / Експерт / Адмін).
  - Dropdown-меню профілю.
  - Мобільне меню ("Бургер").
- [x] **Pages:**
  - **Landing Page:** Презентаційна головна сторінка з пошуком та стрічкою останніх звітів.
  - **Login Page:** Форма авторизації з обробкою помилок.
- [x] **Auth Logic:** Інтеграція з JWT (Login/Logout), збереження сесії.
- [x] **Expert Dashboard:**
  - Таблиця звітів з горизонтальним скролом на мобільних.
  - **New:** Додано колонку якості огранювання (Cut Grade).
  - Швидкі фільтри (Статус, Сортування, Автор).
  - **Advanced Filters:** Розширена панель (4C, Ціна, Дата, Shape) з анімацією.
- [x] **Report Wizard (Майстер створення звіту):**
  - **Split Screen UI:** Екран розділений на форму введення та панель результатів (Sticky Sidebar).
  - **Step-by-Step:** Покрокова навігація (Ідентифікація -> Геометрія -> Фініш).
  - **Live IDC Calculator:** Автоматичний розрахунок **Cut Grade** (Proportions, Polish, Symmetry) та орієнтовної ціни в реальному часі (JS).
  - **Mobile UX:** Авто-скрол табів навігації, адаптивна сітка полів.

### 🔐 Безпека та Доступ

- [x] **JWT Auth:** Система автентифікації на токенах.
- [x] **RBAC:** Розділення прав Admins vs Experts.
- [x] **Security foundation:** bcrypt-хешування для нового локального seed, обов’язковий `SECRET_KEY`, CORS Middleware.

### 🔜 У розробці

- [ ] **API Integration:** Повна інтеграція Frontend (JS) з Python Backend (відправка форм, отримання даних).
- [ ] **Public Passport:** Сторінка перегляду сертифіката для клієнтів (View Report) з генерацією QR-коду.
- [ ] **Analytics:** Сторінка зі статистикою та графіками (порівняння оцінки експерта та AI).

## ⚙️ Налаштування конфігурації (.env)

Скопіюйте `.env.example` у приватний `.env`, задайте унікальний `SECRET_KEY` і параметри MariaDB. Для руйнівного seed додайте локальні `SEED_ADMIN_PASSWORD` та `SEED_GEMOLOGIST_PASSWORD`; у БД зберігатимуться лише їх bcrypt-хеші. Реальні значення не комітуються й не документуються.

## 🗄️ Налаштування Бази Даних (Local)

Проєкт використовує MariaDB через XAMPP.

1. Запустіть **XAMPP Control Panel**.
2. Натисніть **Start** навпроти модуля **MySQL**.
3. Переконайтеся, що у файлі `.env` налаштування співпадають з вашим XAMPP (зазвичай порт 3306, user: root).
4. Лише якщо всі локальні дані можна втратити, виконайте первинне наповнення трьох баз (перебуваючи в корені проєкту):
   ```bash
   python scripts/seed_db.py
   ```

## 🚀 Запуск Backend (Local)

1. Активуйте віртуальне оточення:
   source .venv/bin/activate # (або .venv\Scripts\activate для Windows)

2. Встановіть залежності:
   pip install -r requirements.txt

3. Запустіть сервер з кореня репозиторію:
   python -m uvicorn backend.main:app --reload

4. Відкрийте документацію API (Swagger UI):
   http://127.0.0.1:8000/docs

## 🎨 Запуск Frontend (Local)

Вимоги: **Node.js v22 LTS**

1. Перейдіть у папку фронтенду:

```bash
cd frontend
```

2. Встановіть залежності:

```bash
npm install
```

3. Запустіть режим розробки (Сервер + Gulp Watch):

```bash
npm start
```

4. Відкрийте у браузері: `http://localhost:3000`

Для чистової збірки (без запуску сервера): `npm run build`

Після запуску seed використовуйте локальні облікові записи, але паролі беруться лише з ваших приватних `SEED_*` змінних у `.env`.

## 🛠 Технологічний стек

- **Backend**: Python (FastAPI), SQLAlchemy.
- **Frontend**: Gulp, Pug, SCSS, JavaScript.
- **Database**: MariaDB (Local Dev) / PostgreSQL (Cloud Prod).
- **DevOps**: Docker, Render.

## ▶️ Приклад роботи з `venv` (Windows PowerShell)

```bash
# Створюємо віртуальне середовище (один раз)
python -m venv .venv

# Активуємо віртуальне середовище
.venv\Scripts\activate

# Оновлюємо pip
python -m pip install --upgrade pip

# Встановлюємо залежності
pip install -r requirements.txt

# Встановлюємо необхідну бібліотеку
pip install fastapi

# Перевіряємо встановлення
pip show fastapi

# Фіксуємо залежності
pip freeze > requirements.txt

# Наповнення бази даних (із кореня проєкту)
python scripts/seed_db.py

# Деактивуємо середовище
deactivate
```

> 💡 Якщо використовуємо Bash (наприклад, Git Bash або WSL), команда активації буде: `source .venv/bin/activate`

## 👨‍🎓 Автор

**Олег Бондаренко**

- Студент кафедри Інформаційних та комунікаційних технологій (група І26, Інженерія програмного забезпечення)
- МНТУ (Міжнародний науково-технічний університет імені академіка Юрія Бугая)

## ⚖️ Ліцензія

Цей проєкт розповсюджується під ліцензією MIT. Детальніше див. у файлі [LICENSE](LICENSE).
