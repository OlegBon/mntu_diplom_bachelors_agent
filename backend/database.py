from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import get_database_url

# Singleton engine. URL береться лише з явної конфігурації, без секретних fallback.
engine = create_engine(get_database_url(), pool_pre_ping=True)

# The real browser E2E runtime is explicitly SQLite-only and must keep the
# production MariaDB schema names out of its disposable database file.
if engine.url.get_backend_name() == "sqlite":
    engine = engine.execution_options(schema_translate_map={
        "diamond_oltp": None,
        "diamond_market": None,
        "diamond_analytics": None,
    })

# Фабрика сесій (для кожного запиту буде своя сесія)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовий клас для моделей
Base = declarative_base()

# Функція для отримання сесії (Dependency Injection)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
