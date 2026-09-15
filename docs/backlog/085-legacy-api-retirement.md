# Прибирання legacy `/diamonds/*` після detail/edit

## Мета

Після завершення private detail/edit прибрати невикористаний frontend-код і
погоджено визначити долю compatibility API `/diamonds/*`, не ламаючи чинний
local MVP або майбутній public passport.

## Передумови

- Dashboard і wizard вже працюють через приватний `/reports`.
- У `frontend/src/js/main.js` лишається ізольований legacy handler, який
  очікує відсутній `#legacy-wizard-form` та викликає `/diamonds/*`.
- `/diamonds/*` не є public passport і не повинен ним стати випадково.

## Scope

- Після 080 перевірити, що detail/edit і media використовують лише `/reports`.
- Видалити unreachable legacy frontend handler і пов'язані hardcoded mappings.
- Провести API usage-аудит перед deprecation/removal маршрутів.
- Окремо вирішити: залишити read-only compatibility на перехідний період або
  прибрати `/diamonds/*` у versioned change.
- Додати регресійні API/DOM/E2E перевірки для обраного рішення.

## Не входить

- Public passport/QR — задача 090.
- Масове очищення legacy-колонок і даних — лише окрема погоджена міграція.

## Критерії готовності

- У frontend немає мертвого handler, який викликає `/diamonds/*`.
- API contract, документація і тести узгоджені з обраною долею маршрутів.
- Немає неавторизованого public access до приватного report-data.
