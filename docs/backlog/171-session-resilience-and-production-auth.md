# 171 — Session resilience і production auth

## Мета

Зробити локальну авторизацію стійкою до короткого restart/network failure і
підготувати безпечний production session lifecycle без подовження JWT як
єдиного механізму.

## Етап A — local MVP

- Не видаляти `localStorage` token і не redirect-ити на login, якщо
  `GET /users/me` або page-specific API падає через network error, timeout чи
  `5xx`. Logout відбувається лише після підтвердженого `401`.
- Показати зрозумілий retry/error state: backend може коротко перезапускатися
  під `uvicorn --reload` або frontend може оновитися раніше, ніж API готовий.
- Винести TTL access token у безпечну локальну конфігурацію та встановити
  practical local-MVP значення 8–12 годин. Не друкувати secret/JWT у logs/UI.
- Перевірити login, protected page reload під час temporary API failure,
  confirmed expired/invalid token і manual logout.

## Етап B — перед production/staging

- Короткий access token (15–30 хв) плюс rotating, server-revocable refresh
  sessions; refresh token передається тільки secure `HttpOnly`/`SameSite`
  cookie, не `localStorage`.
- Session/device inventory, explicit revoke current/all sessions, reuse
  detection, expiry/rotation/audit та CSRF model для cookie flow.
- Rate limit/login hardening, production CORS/TLS/cookie config і security
  review разом із staging/deployment задачами 161/140.

## Межі

Не змінює RBAC, report ownership, demo opt-in, wizard work-session tracking
або lifecycle даних. `30 min` поточний JWT не є production session strategy.

## Перевірки

API/unit тести JWT expiration і auth errors; frontend test, що network/`5xx`
не очищує token, а `401` очищує; manual local restart/retry scenario. Перед
етапом B — окремий security review.
