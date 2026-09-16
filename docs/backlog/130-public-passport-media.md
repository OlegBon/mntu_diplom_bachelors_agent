# Публічні вкладення паспорта

## Мета

Погодити, чи можуть plotting або фото каменю бути частиною public passport,
і реалізувати це без відкриття private storage або історичних image-path полів.

## Передумови

- 090 реалізує текстову public projection виданого звіту й не віддає media.
- `MediaAsset.is_public` лишається технічною майбутньою ознакою; сам по собі
  він не створює public URL.

## Scope

- Визначити дозволені asset types, consent/admin-flow та public metadata.
- Додати окремий allow-listed content endpoint без доступу до всього storage.
- Перевірити revoke/void, MIME, hash, cache headers та 404 для private/revoked
  asset.

## Не входить

- Автоматичне оприлюднення існуючих файлів або legacy image paths.
- Відновлення чи backfill historical media.
