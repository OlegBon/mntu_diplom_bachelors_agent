# Правила frontend

- Джерела: `frontend/src/pug`, `frontend/src/scss`, `frontend/src/js`; `frontend/dist` не редагується вручну.
- API-клієнт залишається в `src/js/modules/api.js`, авторизація — в `src/js/modules/auth.js`.
- Використовуй семантичний HTML, доступні повідомлення про помилки й label для кожного поля.
- SCSS використовує токени з `_variables.scss`; не дублюй кольори й відступи магічними значеннями.
- Після UI-зміни виконай `npm run build` і перевір цільову сторінку.
