---
name: database-migrations
description: Планування безпечної майбутньої міграції Diamant ID з MariaDB на PostgreSQL: схема, дані, backfill і rollback.
---

# Database Migrations

Застосовуй лише під час зміни схеми або даних. Поточна runtime-БД — локальна MariaDB; PostgreSQL поки не впроваджено.

Перед зміною: звір моделі, SQL, seed і фактичні дані; визнач обсяг, сумісність MariaDB/PostgreSQL, порядок backfill та rollback. Нову схему вводь expand-contract: спершу сумісні nullable-поля/структури, потім дані, після перевірки — обов’язковість або видалення застарілого.

Міграція до PostgreSQL має охопити `DATABASE_URL`, версіоновані Alembic-міграції, ідемпотентний seed, звірку кількості й цілісності даних та smoke-тест API. Будь-які команди, що змінюють БД, виконуються лише після прямого дозволу користувача.
