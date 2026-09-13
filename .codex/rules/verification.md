# Перевірка змін

Виконуй релевантні перевірки та фіксуй результат у `docs/progress.md`:

```powershell
.\.venv\Scripts\python.exe -c "from backend.main import app; print(app.title)"
cmd /c "cd frontend && npm run build"
git diff --check
```

Для API додай smoke-перевірку запущеного сервера. Для БД погодь окрему безпечну перевірку локальної MariaDB.
